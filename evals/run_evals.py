#!/usr/bin/env python3
"""运行20个fixture/脚本/状态/契约评测；分类报告，不宣称模型语义评测。"""
import argparse
import contextlib
import copy
import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evals"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXCLUDE = {"SKILL.reactive.json"}
EXCLUDE_SUFFIX = {".pyc", ".zip"}
EXCLUDE_DIRS = {"__pycache__", ".git"}


def package_preflight(root):
    """内存打包预演：与 README 打包示例共用同一排除集合，只报不阻断（除非超限）。"""
    entries, traversal, nested_zip, has_root_skill = 0, [], 0, False
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(root)
            if path.suffix == ".zip":
                nested_zip += 1
            if path.name in EXCLUDE or path.suffix in EXCLUDE_SUFFIX or EXCLUDE_DIRS.intersection(rel.parts):
                continue
            arc = rel.as_posix()
            if arc.startswith("/") or ".." in rel.parts or ":" in arc:
                traversal.append(arc)
                continue
            archive.write(path, arc)
            entries += 1
            has_root_skill = has_root_skill or arc == "SKILL.md"
    return {"entries": entries, "root_skill": has_root_skill, "traversal": traversal, "nested_zip": nested_zip, "bytes": buffer.tell()}


OUTPUT_VALIDATOR = load_module("validate_output")
PLAN_VALIDATOR = load_module("validate_plan")
PROFILE_STORE = load_module("profile_store")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def all_prompt_text():
    parts = [(ROOT / "SKILL.md").read_text(encoding="utf-8")]
    for name in ("method.md", "degradation.md", "profile-and-feedback.md", "domain-packs.md", "plan-and-verification.md"):
        parts.append((ROOT / "references" / name).read_text(encoding="utf-8"))
    return "\n".join(parts)


def contract(terms):
    text = all_prompt_text()
    missing = [term for term in terms if term not in text]
    return not missing, "静态Prompt契约存在；不是模型行为证明" if not missing else "缺少契约：" + "、".join(missing)


def validate_both(data):
    return OUTPUT_VALIDATOR.validate_output(data) + PLAN_VALIDATOR.validate_plan(data)


def run_cli(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def invoke_store(args):
    old = sys.argv
    sys.argv = ["profile_store.py", *map(str, args)]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return PROFILE_STORE.main()
    finally:
        sys.argv = old


def profile_flow():
    script = ROOT / "scripts" / "profile_store.py"
    with tempfile.TemporaryDirectory(prefix="experience-fitting-eval-") as temp:
        data_dir = Path(temp) / "user-data"
        record40 = json.dumps({"id": "study_time", "type": "profile", "value": "工作日40分钟", "source": "模拟回答A", "scope": "learning"}, ensure_ascii=False)
        record60 = json.dumps({"id": "study_time", "type": "profile", "value": "工作日60分钟", "source": "模拟回答B", "scope": "learning"}, ensure_ascii=False)
        denied = run_cli(script, "upsert", "--data-dir", data_dir, "--record", record40)
        if denied.returncode == 0 or (data_dir / "profile.json").exists():
            return False, "未确认写入未被拒绝"
        first = run_cli(script, "upsert", "--data-dir", data_dir, "--confirm", "--record", record40)
        second = run_cli(script, "upsert", "--data-dir", data_dir, "--confirm", "--record", record60)
        if first.returncode or second.returncode:
            return False, "确认写入失败：" + first.stdout + second.stdout
        restored = run_cli(script, "restore", "--data-dir", data_dir, "--confirm")
        if restored.returncode or read_json(data_dir / "profile.json")["records"][0]["value"] != "工作日40分钟":
            return False, "单备份恢复未回到40分钟"
        deleted = run_cli(script, "delete", "--data-dir", data_dir, "--id", "study_time", "--confirm")
        if deleted.returncode or read_json(data_dir / "profile.json")["records"]:
            return False, "删除失败"
        session = run_cli(script, "upsert", "--session-only", "--confirm", "--record", record40)
        if session.returncode or "未持久化" not in session.stdout:
            return False, "会话降级未明确提示"

        failure_dir = Path(temp) / "failure-matrix"
        primary = failure_dir / "profile.json"
        backup = failure_dir / "profile.json.bak"
        current60 = {"schema_version": 1, "records": [{"id": "x", "type": "profile", "value": "60", "source": "test", "scope": "learning"}]}
        previous40 = {"schema_version": 1, "records": [{"id": "x", "type": "profile", "value": "40", "source": "test", "scope": "learning"}]}
        PROFILE_STORE.atomic_write(primary, current60)
        PROFILE_STORE.atomic_write(backup, previous40)
        before = (primary.read_bytes(), backup.read_bytes())
        if invoke_store(["upsert", "--data-dir", failure_dir, "--confirm"]) == 0 or before != (primary.read_bytes(), backup.read_bytes()):
            return False, "无效upsert改变了主文件或备份"
        if invoke_store(["delete", "--data-dir", failure_dir, "--confirm", "--id", "missing"]) == 0 or before != (primary.read_bytes(), backup.read_bytes()):
            return False, "无效delete改变了主文件或备份"
        real_write = PROFILE_STORE.atomic_write
        for command in ("upsert", "delete"):
            for fail_at in (2, 3):
                real_write(primary, current60)
                real_write(backup, previous40)
                before = (primary.read_bytes(), backup.read_bytes())
                calls = {"count": 0}

                def fail_update(path, data):
                    calls["count"] += 1
                    if calls["count"] == fail_at:
                        raise OSError(f"注入：{command}第{fail_at}次写失败")
                    real_write(path, data)

                PROFILE_STORE.atomic_write = fail_update
                try:
                    command_args = [command, "--data-dir", failure_dir, "--confirm"]
                    if command == "upsert":
                        command_args += ["--record", record60]
                    else:
                        command_args += ["--id", "x"]
                    update_rc = invoke_store(command_args)
                finally:
                    PROFILE_STORE.atomic_write = real_write
                if update_rc == 0 or before != (primary.read_bytes(), backup.read_bytes()):
                    return False, f"合法{command}第{fail_at}次写失败后未按原始字节回滚"
                if list(failure_dir.glob(".profile-restore-*")):
                    return False, f"合法{command}回滚后仍残留事务临时文件"

        real_write(primary, current60)
        real_write(backup, previous40)
        before = (primary.read_bytes(), backup.read_bytes())
        calls = {"count": 0}

        def fail_third(path, data):
            calls["count"] += 1
            if calls["count"] == 3:
                raise OSError("注入：restore备份阶段写失败")
            real_write(path, data)

        PROFILE_STORE.atomic_write = fail_third
        try:
            restore_rc = invoke_store(["restore", "--data-dir", failure_dir, "--confirm"])
        finally:
            PROFILE_STORE.atomic_write = real_write
        if restore_rc == 0 or before != (primary.read_bytes(), backup.read_bytes()):
            return False, "restore第二次写失败后未完整回滚"
        if list(failure_dir.glob(".profile-restore-*")):
            return False, "完整回滚后仍残留事务临时文件"
        return True, "确认/恢复/删除/降级、无效写不变、合法更新及restore写失败回滚均通过"


def duplicate_phase_case(word):
    data = copy.deepcopy(word)
    plan = data["executable_plan"]["plan"]
    plan["phases"] = [dict(plan["phases"][0], name="DUP", minutes=30), dict(plan["phases"][1], name="DUP", minutes=20)]
    plan["time_budgets"] = [{"name": "X", "available_minutes": 40, "phase_names": ["DUP", "DUP"]}]
    plan["provenance"] = [{"phase": "DUP", "source": "个人改造", "detail": "A"}, {"phase": "DUP", "source": "个人改造", "detail": "B"}]
    return data


def evaluate(case, fixtures, manual):
    check = case["check"]
    valid_map = {"valid_word": "word", "valid_home": "home", "valid_english": "english", "valid_photography": "photography", "valid_team": "team"}
    if check in valid_map:
        errors = validate_both(copy.deepcopy(fixtures[valid_map[check]]))
        return not errors, "独立fixture结构与可计算约束通过；语义另评" if not errors else "；".join(errors)
    if check in {"manual_L02", "manual_L03"}:
        case_id = check.split("_")[1]
        key = "reading" if case_id == "L02" else "programming"
        start = manual.find(f"## 案例 {case_id}")
        end = manual.find("\n---", start)
        section = manual[start:end if end >= 0 else None]
        needed = ["【经验试穿卡】", "【可执行个人版】", "【验证卡】", "待验证"]
        missing = [item for item in needed if item not in section]
        errors = validate_both(copy.deepcopy(fixtures[key]))
        return not missing and not errors, f"{key}独立fixture与手动三产物通过" if not missing and not errors else "；".join(missing + errors)
    if check == "time_over_budget":
        data = copy.deepcopy(fixtures["word"])
        data["executable_plan"]["plan"]["time_budgets"] = [
            {"name": "练习日", "available_minutes": 40, "phase_names": ["P1练习", "P2测试"]},
            {"name": "首晚", "available_minutes": 40, "phase_names": ["P0基线"]},
        ]
        over_errors = PLAN_VALIDATOR.validate_plan(data)
        duplicate_errors = validate_both(duplicate_phase_case(fixtures["word"]))
        detected = any("超预算" in e for e in over_errors), any("阶段名必须唯一" in e for e in duplicate_errors)
        return all(detected), "按预期拒绝超预算及重复阶段名绕过" if all(detected) else f"负向断言：{detected}"
    if check == "missing_checkpoint":
        data = copy.deepcopy(fixtures["word"])
        for phase in data["executable_plan"]["plan"]["phases"]:
            phase.pop("checkpoint", None)
        checkpoint_errors = PLAN_VALIDATOR.validate_plan(data)
        nonfinite = copy.deepcopy(fixtures["word"])
        nonfinite["executable_plan"]["plan"]["phases"][0]["minutes"] = float("nan")
        nonfinite_errors = PLAN_VALIDATOR.validate_plan(nonfinite)
        detected = any("至少一个阶段" in e for e in checkpoint_errors), any("有限正数" in e for e in nonfinite_errors)
        return all(detected), "按预期拒绝无检查点及非有限时间" if all(detected) else f"负向断言：{detected}"
    if check == "forbidden_percentage":
        variants = []
        data = copy.deepcopy(fixtures["word"]); data["questions"] = [dict(q, round="initial") for q in fixtures["word"]["questions"] * 2] + [dict(q, round="followup") for q in fixtures["word"]["questions"]]; variants.append(("总提问", OUTPUT_VALIDATOR.validate_output(data)))
        data = copy.deepcopy(fixtures["word"]); data["branches"] = ["1", "2", "3", "4"]; variants.append(("branches", OUTPUT_VALIDATOR.validate_output(data)))
        data = copy.deepcopy(fixtures["word"]); data["fit_judgments"] = [dict(j, step="完全无关且重复") for j in data["fit_judgments"]]; variants.append(("一一对应", OUTPUT_VALIDATOR.validate_output(data)))
        data = copy.deepcopy(fixtures["word"]); data["share_draft"] = {"title": "我的版本", "body": "还没实践，只准备明天开始。", "practice_status": "未执行", "ai_label": "AI 辅助整理"}; variants.append(("分享稿状态", OUTPUT_VALIDATOR.validate_output(data)))
        data = copy.deepcopy(fixtures["team"]); data["content_type"] = "可执行经验"; data["experience_summary"] = "没有通用标识"; variants.append(("generic 必须", OUTPUT_VALIDATOR.validate_output(data)))
        detected = [any(token in error for error in errors) for token, errors in variants]
        ok_doc, doc_detail = contract(["适配百分比", "不得承诺提分"])
        ok = all(detected) and ok_doc
        return ok, "拒绝9问/4分支/步骤错位/未执行分享/通用标识缺失；百分比与承诺转为文档契约与评审" if ok else f"负向断言：{detected}；文档契约：{doc_detail}"
    if check == "conditional_refusal":
        data = copy.deepcopy(fixtures["conditional"])
        errors = validate_both(data)
        valid_conditional = data["outcome"] == "conditional" and len(data["branches"]) <= 3 and any(q["answer_status"] == "declined" for q in data["questions"])
        return not errors and valid_conditional, "独立拒答fixture含未知、条件式v1和3分支" if not errors and valid_conditional else "；".join(errors)
    if check == "contract_pseudo_documented":
        ok, detail = contract(["再调研一下", "多收集信息", "坚持一段时间看看"])
        return ok, detail + "；伪实验识别归模型/评审，脚本不判定"
    if check == "contract_multi_goal":
        return contract(["本次唯一主目标", "不要混成大杂烩"])
    if check == "contract_high_risk":
        return contract(["停止个性化建议", "不生成执行方案或验证卡", "医疗", "投资", "Cautious", "不沿用原帖剂量", "退出某步骤"])
    if check == "contract_empty":
        return contract(["空输入要正文", "无行动步骤只做拆解", "不足以试穿"])
    if check == "contract_long":
        ok, detail = contract(["超长文本分段", "标记截断边界"])
        with tempfile.TemporaryDirectory(prefix="experience-fitting-bom-") as temp:
            path = Path(temp) / "bom.json"; path.write_text(json.dumps(fixtures["word"], ensure_ascii=False), encoding="utf-8-sig")
            result = run_cli(ROOT / "scripts" / "validate_output.py", path)
            return ok and result.returncode == 0, detail + "；UTF-8 BOM读取" + ("通过" if result.returncode == 0 else "失败")
    if check == "contract_no_steps":
        return contract(["无行动步骤只做拆解", "不足以试穿"])
    if check == "contract_emotion":
        return contract(["纯情绪内容"])
    if check == "reuse_conditions":
        original, variant = fixtures["word"], fixtures["alt"]
        errors = validate_both(copy.deepcopy(original)) + validate_both(copy.deepcopy(variant))
        changes = sum(a["status"] != b["status"] for a, b in zip(original["fit_judgments"], variant["fit_judgments"]))
        return not errors and changes >= 3, f"两份完整fixture有{changes}处判定变化；语义合理性另评" if not errors else "；".join(errors)
    if check == "profile_flow":
        return profile_flow()
    if check == "degradation":
        ok, detail = contract(["无脚本", "无持久化", "不抓链接", "待验证"])
        manual_ok = "不调用脚本、不读写画像" in manual
        return ok and manual_ok, detail + "；四例纯Prompt记录" + ("存在" if manual_ok else "缺失")
    return False, f"未知检查类型：{check}"


def static_validation(case_count):
    errors, warnings = [], []
    required = ["SKILL.md", "README.md", "assets/card-template.md", "assets/share-example.md", "references/method.md", "references/io-schema.md", "references/profile-and-feedback.md", "references/degradation.md", "scripts/validate_output.py", "scripts/validate_plan.py", "scripts/profile_store.py"]
    for name in required:
        if not (ROOT / name).is_file():
            errors.append(f"缺少文件：{name}")
    # SKILL.reactive.json 由平台安装/加载时自动生成，不属于发布包，不计入 30 文件上限
    files = [p for p in ROOT.rglob("*") if p.is_file() and p.name not in EXCLUDE and p.suffix not in EXCLUDE_SUFFIX and not EXCLUDE_DIRS.intersection(p.relative_to(ROOT).parts)]
    size = sum(p.stat().st_size for p in files)
    if len(files) > 30:
        errors.append(f"文件数{len(files)}>30")
    if size > 40 * 1024 * 1024:
        errors.append(f"大小{size}>40MB")
    pack = package_preflight(ROOT)
    if pack["entries"] > 30:
        errors.append(f"打包条目{pack['entries']}>30")
    if not pack["root_skill"]:
        errors.append("打包根目录缺少SKILL.md")
    if pack["traversal"]:
        errors.append("打包出现路径穿越：" + "、".join(pack["traversal"]))
    scripts = sorted(p.name for p in (ROOT / "scripts").glob("*.py"))
    if scripts != ["profile_store.py", "validate_output.py", "validate_plan.py"]:
        errors.append("scripts 必须且只能含3个指定Python脚本")
    if not 18 <= case_count <= 22:
        errors.append(f"eval数量{case_count}不在18–22")
    allowed_dirs = {"assets", "config", "evals", "prompts", "references", "scripts", "templates", "workflows"}
    for path in ROOT.iterdir():
        if path.is_dir() and path.name not in allowed_dirs:
            errors.append(f"非标准目录：{path.name}")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", skill, re.S)
    if not match:
        errors.append("SKILL.md frontmatter 无效")
    else:
        lines = match.group(1).splitlines()
        names = [line.split(":", 1)[1].strip() for line in lines if line.startswith("name:")]
        descriptions = [line.split(":", 1)[1].strip() for line in lines if line.startswith("description:")]
        if len(names) != 1 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", names[0] if names else "") or not 1 <= len(names[0]) <= 64:
            errors.append("name 不符合slug规则")
        if len(descriptions) != 1 or not descriptions[0] or len(descriptions[0]) > 1024:
            errors.append("description 必须为单行且1–1024字符")
        if names and names[0] != ROOT.name:
            warnings.append(f"开发目录{ROOT.name}与slug {names[0]}不同；成品zip不含外层目录")
    if len(skill) > 50000:
        errors.append("SKILL.md 正文超过50000字符")
    for path in files:
        if path.suffix == ".py":
            text = path.read_text(encoding="utf-8")
            if re.search(r"^\s*(?:import|from)\s+(?:requests|PIL|httpx|aiohttp)\b", text, re.M):
                errors.append(f"发现禁止的外部依赖：{path.name}")
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http" + "://", "https" + "://", "#", "mailto:")):
                    continue
                local_target = target.split("#", 1)[0]
                if local_target and not (path.parent / local_target).resolve().exists():
                    errors.append(f"Markdown断链：{path.relative_to(ROOT)} -> {target}")
    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {"status": status, "errors": errors, "warnings": warnings, "file_count": len(files), "bytes": size, "pack": pack}


def main():
    parser = argparse.ArgumentParser(description="运行经验试穿20例与静态检查")
    parser.add_argument("--report", help="可选：写入JSON结果")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    cases = read_json(EVAL_DIR / "cases.json")
    static = static_validation(len(cases))
    results = []
    if not args.static_only:
        fixture_files = {"word": "word200.json", "home": "home-drawer.json", "reading": "reading.json", "programming": "programming.json", "english": "english.json", "conditional": "conditional-home.json", "alt": "word200-alt.json", "photography": "photography.json", "team": "team-meeting.json"}
        fixtures = {key: read_json(EVAL_DIR / "fixtures" / name) for key, name in fixture_files.items()}
        manual = (EVAL_DIR / "manual-runs.md").read_text(encoding="utf-8")
        for case in cases:
            try:
                passed, detail = evaluate(case, fixtures, manual)
            except Exception as exc:
                passed, detail = False, f"评测异常：{type(exc).__name__}: {exc}"
            kind = "contract" if case["check"].startswith("contract") or case["check"] == "degradation" else "script_fixture"
            results.append({"id": case["id"], "title": case["title"], "evidence_type": kind, "status": "PASS" if passed else "FAIL", "detail": detail})
            print(f"{results[-1]['status']} {case['id']} [{kind}] {case['title']} — {detail}")
    passed = sum(item["status"] == "PASS" for item in results)
    contract_total = sum(item["evidence_type"] == "contract" for item in results)
    print(f"EVAL: {passed}/{len(results)} PASS | script/fixture={len(results)-contract_total} | static-contract={contract_total} | 非模型语义总分")
    report = {"scope": "独立fixture、脚本、状态与静态契约分类检查，不是模型语义正确性证明", "eval_passed": passed, "eval_total": len(results), "script_fixture_total": len(results) - contract_total, "contract_total": contract_total, "results": results, "static": static}
    if args.report:
        report_path = Path(args.report); report_path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            report["static"] = static
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            refreshed = static_validation(len(cases))
            if refreshed["bytes"] == static["bytes"] and refreshed["file_count"] == static["file_count"]:
                break
            static = refreshed
        report["static"] = static
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"STATIC: {static['status']} | files={static['file_count']} | bytes={static['bytes']}")
    print(f"PACK: entries={static['pack']['entries']} | root={'OK' if static['pack']['root_skill'] else 'BAD'}")
    for warning in static["warnings"]:
        print("WARN: " + warning)
    for error in static["errors"]:
        print("FAIL: " + error)
    return 0 if not args.static_only and passed == len(results) and static["status"] != "FAIL" else (0 if args.static_only and static["status"] != "FAIL" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
