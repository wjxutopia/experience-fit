#!/usr/bin/env python3
"""经验试穿执行计划的可计算约束校验，不做语义适配判断。"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

PLAN_FIELDS = (
    "goal", "success_criteria", "assumptions", "resources", "phases", "schedule",
    "fallbacks", "stop_rules", "first_action", "not_to_do", "provenance",
    "feasibility_checks", "time_budgets",
)
VERIFY_FIELDS = (
    "hypothesis", "action", "context", "cost", "reversibility",
    "frequency_or_opportunities", "metric", "stop_rule", "decision_rule", "first_action",
)
THRESHOLD = re.compile(r"^(?:>=|<=|>|<|=)\d+(?:\.\d+)?(?:%|[^\d\s]{1,4})?$")


def present(value):
    return value is not None and value != "" and value != [] and value != {}


def validate_plan(data):
    errors = []
    root = data if isinstance(data, dict) else {}
    executable = root.get("executable_plan", {})
    plan = executable.get("plan", {}) if isinstance(executable, dict) else root
    if not isinstance(plan, dict):
        return ["plan 必须是对象"]
    for key in PLAN_FIELDS:
        if not present(plan.get(key)) and plan.get(key) != 0:
            errors.append(f"plan 缺少或为空：{key}")
    phases = plan.get("phases", [])
    phase_names = []
    checkpoint_count = 0
    if not isinstance(phases, list) or not phases:
        errors.append("phases 必须是非空数组")
        phases = []
    for index, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"phases[{index}] 必须是对象")
            continue
        for key in ("name", "duration", "minutes", "actions", "output"):
            if not present(phase.get(key)) and phase.get(key) != 0:
                errors.append(f"phases[{index}] 缺少或为空：{key}")
        name = phase.get("name")
        if isinstance(name, str) and name:
            phase_names.append(name)
        minutes = phase.get("minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, (int, float)) or not math.isfinite(minutes) or minutes <= 0:
            errors.append(f"phases[{index}].minutes 必须是有限正数")
        checkpoint = phase.get("checkpoint")
        if checkpoint is not None:
            checkpoint_count += 1
            if not isinstance(checkpoint, dict):
                errors.append(f"phases[{index}].checkpoint 必须是对象")
            else:
                for key in ("when", "metric", "threshold", "action"):
                    if not present(checkpoint.get(key)):
                        errors.append(f"phases[{index}].checkpoint 缺少或为空：{key}")
                threshold = checkpoint.get("threshold")
                if isinstance(threshold, str) and not THRESHOLD.fullmatch(threshold.replace(" ", "")):
                    errors.append(f"phases[{index}] 阈值须为 >=70、<50 等可计算形式")
    if checkpoint_count < 1:
        errors.append("至少一个阶段必须有 checkpoint")
    duplicate_phases = sorted({name for name in phase_names if phase_names.count(name) > 1})
    if duplicate_phases:
        errors.append(f"阶段名必须唯一，重复：{duplicate_phases}")
    budgets = plan.get("time_budgets", [])
    assigned = []
    if not isinstance(budgets, list) or not budgets:
        errors.append("time_budgets 必须是非空数组")
        budgets = []
    minutes_by_name = {p.get("name"): p.get("minutes") for p in phases if isinstance(p, dict)}
    for index, budget in enumerate(budgets):
        if not isinstance(budget, dict):
            errors.append(f"time_budgets[{index}] 必须是对象")
            continue
        available = budget.get("available_minutes")
        names = budget.get("phase_names")
        if isinstance(available, bool) or not isinstance(available, (int, float)) or not math.isfinite(available) or available <= 0:
            errors.append(f"time_budgets[{index}].available_minutes 必须是有限正数")
            continue
        if not isinstance(names, list) or not names:
            errors.append(f"time_budgets[{index}].phase_names 必须非空")
            continue
        assigned.extend(names)
        total = 0
        for name in names:
            minutes = minutes_by_name.get(name)
            if isinstance(minutes, (int, float)) and not isinstance(minutes, bool):
                total += minutes
            else:
                errors.append(f"时间组引用了未知阶段：{name}")
        if total > available:
            errors.append(f"时间组 {budget.get('name', index)} 超预算：{total}>{available} 分钟")
    if len([str(x) for x in assigned]) != len(set(str(x) for x in assigned)):
        errors.append("同一阶段不得重复归入时间组")
    if sorted(str(x) for x in assigned) != sorted(str(x) for x in phase_names):
        errors.append("每个阶段必须且只能归入一个时间组")
    provenance = plan.get("provenance", [])
    provenance_phases = []
    if isinstance(provenance, list):
        for index, item in enumerate(provenance):
            if not isinstance(item, dict) or not all(present(item.get(k)) for k in ("phase", "source", "detail")):
                errors.append(f"provenance[{index}] 须含 phase/source/detail")
            else:
                provenance_phases.append(item["phase"])
    if sorted(str(x) for x in provenance_phases) != sorted(str(x) for x in phase_names):
        errors.append("每个阶段必须且只能有一条 provenance")
    feasibility = plan.get("feasibility_checks", {})
    if not isinstance(feasibility, dict):
        errors.append("feasibility_checks 必须是对象")
    else:
        for key in ("resources", "dependencies", "risks"):
            if not present(feasibility.get(key)):
                errors.append(f"feasibility_checks 缺少或为空：{key}")
        habits = feasibility.get("habit_changes")
        if isinstance(habits, bool) or not isinstance(habits, int) or not 0 <= habits <= 2:
            errors.append("habit_changes 须为 0、1 或 2")
    fallbacks = plan.get("fallbacks")
    if not isinstance(fallbacks, list) or not fallbacks:
        errors.append("fallbacks 至少需要 1 条")
    verification = root.get("verification_card")
    if verification is not None:
        if not isinstance(verification, dict):
            errors.append("verification_card 必须是对象")
        else:
            for key in VERIFY_FIELDS:
                if not present(verification.get(key)):
                    errors.append(f"verification_card 缺少或为空：{key}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="只校验计划 schema、时间求和、阈值与固定要素")
    parser.add_argument("input", help="JSON 文件，或 - 从 stdin 读取")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL: 无法读取 JSON：{exc}")
        return 2
    errors = validate_plan(data)
    if errors:
        print(f"FAIL: {len(errors)} 项可计算约束问题（未做语义校验）")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: 计划结构与可计算约束通过（不证明资源真实或计划有效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
