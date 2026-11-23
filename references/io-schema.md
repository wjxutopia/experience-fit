# 可选 JSON 数据契约

纯 Prompt 交付不需要 JSON。只有调用校验器时，才把同一结果整理为 UTF-8 JSON；校验失败要修正结果，不得为了通过而删去必要信息。

```json
{
  "outcome": "fitted",
  "domain_mode": "vertical",
  "experience_summary": "一句话概括，不补作者事实",
  "content_type": "可执行经验",
  "author_goal": "作者目标",
  "evidence_strength": "原帖证据与当前用户证据的边界",
  "author_conditions": ["作者明示条件"],
  "steps": ["S1 原步骤"],
  "claims": ["作者声称……"],
  "hidden_assumptions": ["推测：……"],
  "unknowns": ["一个会改变分支的未知"],
  "branches": ["如果……那么……；最多三条（outcome=fitted 时可省略，空数组等价）"],
  "questions": [
    {
      "round": "initial",
      "question": "具体问题？",
      "why_it_matters": "改变哪个决定",
      "judgments_it_can_flip": ["S1"],
      "uncertainty": "当前未知",
      "priority": 1,
      "answer_status": "answered"
    }
  ],
  "fit_judgments": [
    {
      "step": "S1 原步骤",
      "personal_conditions": ["用户明确回答"],
      "status": "改造",
      "reason": "理由",
      "evidence": "原步骤与回答",
      "source": "个人改造",
      "background": "背景",
      "options": ["保留", "改造"],
      "decision": "当前决定",
      "consequences": "后果",
      "reversibility": "可逆性及恢复方式"
    }
  ],
  "executable_plan": {
    "personal_v1": ["当前可执行动作"],
    "plan": {
      "goal": "唯一目标",
      "success_criteria": "完成标准",
      "assumptions": ["假设"],
      "resources": ["已有资源"],
      "phases": [
        {
          "name": "P0",
          "duration": "今晚",
          "minutes": 10,
          "actions": ["一个动作"],
          "output": "记录",
          "checkpoint": {
            "when": "第3天",
            "metric": "实际用时",
            "threshold": ">40",
            "action": "结束本轮并记录当前版本不适用；新剂量另开版本"
          }
        }
      ],
      "schedule": "第一次与频率",
      "fallbacks": ["没时间……", "缺资源……", "中断……", "状态差……"],
      "stop_rules": ["停止条件"],
      "first_action": "今天或明天的一个动作",
      "not_to_do": ["不扩围事项"],
      "provenance": [
        {"phase": "P0", "source": "个人改造", "detail": "对应哪条原经验"}
      ],
      "feasibility_checks": {
        "resources": "资源说明",
        "dependencies": "依赖说明",
        "risks": "风险说明",
        "habit_changes": 1
      },
      "time_budgets": [
        {"name": "首晚", "available_minutes": 40, "phase_names": ["P0"]}
      ]
    }
  },
  "verification_card": {
    "hypothesis": "一个假设",
    "action": "一个最小动作",
    "context": "时间地点资源",
    "cost": "可计算成本",
    "reversibility": "如何撤回",
    "frequency_or_opportunities": "机会数",
    "metric": "指标与记录条件",
    "stop_rule": "停止条件",
    "decision_rule": "保留/修改/放弃规则",
    "first_action": "第一个动作"
  },
  "profile_updates": []
}
```

规则：本完整产物校验器只处理 `outcome=fitted/conditional`；高风险和无步骤退出走主 Prompt 的轻量退出格式，不强行生成三件产物。`domain_mode` 必填 `vertical/generic`；`generic` 必须在 `content_type` 或 `experience_summary` 明示“通用模式，领域规则未覆盖”。`questions.round` 仅 `initial/followup`；`answer_status` 可 `answered/declined/unknown/partial`；`fit_judgments.status` 仅 `保留/改造/暂缓/放弃`。步骤字符串必须唯一，判定按原顺序与 `steps` 一一对应。阶段对象必须使用 `name` 字段，阶段名唯一，每个阶段只能进入一个时间组，`minutes` 必须为有限正数（`duration` 只是展示文本，不受此限）。`risk_level` 为可选字段，取值 `standard/cautious/exit`；缺省视为 `standard`；声明 `exit` 时不生成执行方案与验证卡，走轻量退出格式。脚本不校验 risk_level，语义由模型/评审判断。

`branches` 在 `outcome=fitted` 时可省略（空数组等价）；`conditional` 必填 1–3 条分支、至少一个拒答/未知/部分回答，并在 `personal_v1` 明确标“条件式”，且必须提供验证卡。普通（fitted）产物是否附验证卡，由“关键未知是否会改变分支”判断，不在脚本强制范围；脚本只检查“给了卡就必须字段齐全”。验证卡不能替代计划中的资源、检查点或兜底；同一轮改变关键变量时应结束本轮，另开版本。

分享稿是可选 `share_draft` 对象：`title`、`body`、`practice_status`、`ai_label`。未实践时 `practice_status` 必须为“待验证”且正文也包含“待验证”；“未执行”只是内部状态，不作为分享完成态。`ai_label` 必须为“AI 辅助整理”。若状态为“部分验证/对当前用户有效/证据不足”，还必须有 `practice_evidence` 字段记录用户真实证据；脚本只检查非空，不判断证据真实性。
