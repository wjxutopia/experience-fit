#!/usr/bin/env python3
"""经验试穿产物结构校验；不判断语义、来源真实性或方法效果。"""
import argparse
import json
import sys
from pathlib import Path

JUDGMENT_FIELDS = (
    "step", "personal_conditions", "status", "reason", "evidence", "source",
    "background", "options", "decision", "consequences", "reversibility",
)
PLAN_KEYS = (
    "goal", "success_criteria", "assumptions", "resources", "phases", "schedule",
    "fallbacks", "stop_rules", "first_action", "not_to_do", "provenance",
    "feasibility_checks", "time_budgets",
)
VERIFY_KEYS = (
    "hypothesis", "action", "context", "cost", "reversibility",
    "frequency_or_opportunities", "metric", "stop_rule", "decision_rule", "first_action",
)


def _present(value):
    return value is not None and value != "" and value != [] and value != {}


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def validate_output(data):
    errors = []
    if not isinstance(data, dict):
        return ["根节点必须是 JSON 对象"]
    for key in ("experience_summary", "content_type", "author_goal", "evidence_strength",
                "author_conditions", "steps", "claims", "hidden_assumptions", "unknowns",
                "questions", "fit_judgments", "executable_plan"):
        if key not in data or (key in ("experience_summary", "content_type", "author_goal", "evidence_strength", "steps", "questions", "fit_judgments") and not _present(data[key])):
            errors.append(f"缺少或为空：{key}")
    outcome = data.get("outcome")
    if outcome not in {"fitted", "conditional"}:
        errors.append("outcome 必须为 fitted/conditional；本校验器不处理高风险或无步骤退出格式")
    domain_mode = data.get("domain_mode")
    if domain_mode not in {"vertical", "generic"}:
        errors.append("domain_mode 必须为 vertical/generic")
    if domain_mode == "generic" and "通用模式，领域规则未覆盖" not in (str(data.get("content_type", "")) + str(data.get("experience_summary", ""))):
        errors.append("generic 必须在 content_type 或 experience_summary 明示“通用模式，领域规则未覆盖”")
    for key in ("author_conditions", "steps", "claims", "hidden_assumptions", "unknowns"):
        if key in data and not isinstance(data[key], list):
            errors.append(f"{key} 必须是数组")
    steps = data.get("steps", [])
    judgments = data.get("fit_judgments", [])
    if isinstance(steps, list) and isinstance(judgments, list):
        if not all(isinstance(step, str) and step for step in steps):
            errors.append("steps 必须全部是非空字符串")
        elif len(set(steps)) != len(steps):
            errors.append("steps 不得包含重复步骤")
        elif [item.get("step") if isinstance(item, dict) else None for item in judgments] != steps:
            errors.append("fit_judgments 必须按原顺序与 steps 一一对应，不得重复、缺失或替换")
    allowed = {"保留", "改造", "暂缓", "放弃"}
    for index, item in enumerate(judgments if isinstance(judgments, list) else []):
        if not isinstance(item, dict):
            errors.append(f"fit_judgments[{index}] 必须是对象")
            continue
        for key in JUDGMENT_FIELDS:
            if not _present(item.get(key)):
                errors.append(f"fit_judgments[{index}] 缺少或为空：{key}")
        status = str(item.get("status", "")).split("·")[-1]
        if status not in allowed:
            errors.append(f"fit_judgments[{index}].status 非法")
    questions = data.get("questions", [])
    if isinstance(questions, list):
        initial = sum(isinstance(q, dict) and q.get("round") == "initial" for q in questions)
        followup = sum(isinstance(q, dict) and q.get("round") == "followup" for q in questions)
        if len(questions) > 8:
            errors.append(f"总提问 {len(questions)} > 8")
        if initial > 5:
            errors.append(f"首轮提问 {initial} > 5")
        if followup > 3:
            errors.append(f"追问 {followup} > 3")
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                errors.append(f"questions[{index}] 必须是对象")
                continue
            for key in ("round", "question", "why_it_matters", "judgments_it_can_flip", "uncertainty", "priority", "answer_status"):
                if not _present(question.get(key)) and question.get(key) != 0:
                    errors.append(f"questions[{index}] 缺少或为空：{key}")
            if question.get("round") not in {"initial", "followup"}:
                errors.append(f"questions[{index}].round 非法")
            if question.get("answer_status") not in {"answered", "declined", "unknown", "partial"}:
                errors.append(f"questions[{index}].answer_status 非法")
    branches = data.get("branches", [])
    if not isinstance(branches, list) or len(branches) > 3:
        errors.append("branches 必须是最多 3 条的数组")
    if outcome == "conditional":
        if not branches:
            errors.append("条件式试穿必须提供至少 1 条条件分支")
        personal = data.get("executable_plan", {}).get("personal_v1", [])
        if not isinstance(personal, list) or not any(isinstance(item, str) and "条件式" in item for item in personal):
            errors.append("条件式试穿的 personal_v1 必须明确标注“条件式”")
        if isinstance(questions, list) and questions and all(isinstance(q, dict) and q.get("answer_status") == "answered" for q in questions):
            errors.append("条件式试穿至少保留一个拒答、未知或部分回答的问题")
    verification = data.get("verification_card")
    if verification is not None:
        if not isinstance(verification, dict):
            errors.append("verification_card 必须是对象")
        else:
            for key in VERIFY_KEYS:
                if not _present(verification.get(key)):
                    errors.append(f"verification_card 缺少或为空：{key}")
    if outcome == "conditional" and not isinstance(verification, dict):
        errors.append("声明条件式试穿时必须提供 verification_card")
    executable = data.get("executable_plan", {})
    if not isinstance(executable, dict) or not _present(executable.get("personal_v1")):
        errors.append("executable_plan.personal_v1 必须非空")
    plan = executable.get("plan", {}) if isinstance(executable, dict) else {}
    for key in PLAN_KEYS:
        if not _present(plan.get(key)) and plan.get(key) != 0:
            errors.append(f"executable_plan.plan 缺少或为空：{key}")
    share = data.get("share_draft")
    if share is not None:
        if not isinstance(share, dict):
            errors.append("share_draft 必须是对象")
        else:
            for key in ("title", "body", "practice_status", "ai_label"):
                if not _present(share.get(key)):
                    errors.append(f"share_draft 缺少或为空：{key}")
            if share.get("ai_label") != "AI 辅助整理":
                errors.append("分享稿必须标注 AI 辅助整理")
            status = share.get("practice_status")
            if status not in {"待验证", "部分验证", "对当前用户有效", "证据不足"}:
                errors.append("分享稿状态只能是待验证/部分验证/对当前用户有效/证据不足；未执行不得作为分享完成态")
            if status == "待验证" and "待验证" not in str(share.get("body", "")):
                errors.append("未实践分享稿正文必须标注“待验证”")
            if status in {"部分验证", "对当前用户有效", "证据不足"} and not _present(share.get("practice_evidence")):
                errors.append("有实践状态的分享稿必须提供 practice_evidence；脚本不判断其真实性")
    return errors


def main():
    parser = argparse.ArgumentParser(description="只校验经验试穿产物结构与固定约束")
    parser.add_argument("input", help="JSON 文件，或 - 从 stdin 读取")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: 无法读取 JSON：{exc}")
        return 2
    errors = validate_output(data)
    if errors:
        print(f"FAIL: {len(errors)} 项结构/约束问题（未做语义校验）")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 产物结构与固定约束通过（不代表语义、来源或效果通过）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
