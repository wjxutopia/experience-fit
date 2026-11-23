# 经验试穿（experience-fitting）

把一篇别人的经验帖，按**你的**目标、时间、基础、资源和边界，改成能执行的个人版本。

- 英文 ID：`experience-fitting`
- 中文展示名：经验试穿
- 版本：1.2.1
- 运行方式：支持加载 Skill 的 Agent；核心流程纯 Prompt，无网络、无外部 API、无第三方依赖
- 依赖：可选 Python 3（仅用于结构校验与画像存储，缺失时自动降级）

---

## 一、它解决什么问题

收藏夹里堆着"每天背 200 词""每周复盘一次""每天开 15 分钟站会"这类经验帖，照抄往往失败：作者的条件和你不一样，作者的效果也没被验证过。

经验试穿不提供"标准答案"，而是把经验当**原材料**：

1. 忠实拆出作者的步骤、明示条件、隐含前提和声称结果；
2. 逐条对照你的条件，判为 **保留 / 改造 / 暂缓 / 放弃**；
3. 把改造落到具体动作、数量、时间和条件；
4. 只对"会改变方案的关键未知"设计一个低成本实验；
5. 默认只在当前对话交付，不擅自写盘。

核心闭环：**拆 → 对 → 改 → 试 → 存**。

### 它不做什么

- 不生成文案：不代写笔记正文，也不做标题党；
- 不生成配图：不出封面、不做图片，只给可直接复制的文本卡；
- 不给适配百分比：不打适合度分数，只说哪条保留、哪条要改；
- 不承诺效果：不承诺提分、上岸、记忆增强或健康疗效；
- 不自动发布：不代发、不批量生成，发布前由你确认。

它只做一件事：把别人的步骤改成你能执行、能验证的版本。

## 二、什么时候用 / 什么时候不用

| 适合 | 不适合 |
|---|---|
| 粘贴一篇包含具体做法的经验正文，想判断、改编或落地 | 纯链接、纯图片、纯视频 |
| 学习方法、阅读、语言、编程练习等成长类经验 | 多篇混合试穿 |
| 收纳、家务、生活习惯等轻量居家经验 | 查定义、事实核查 |
| 团队流程、职场习惯、兴趣实践等低风险领域（走通用模式） | 纯情绪倾诉、通用日程安排 |
| 想验证"这条经验对我到底成不成立" | 医疗、用药、法律、投资、心理危机、结构改造、电路、燃气、消防等高风险个性化建议 |
| | 自动发布、代写笔记、批量生成 |

高风险内容会**直接退出**个性化建议：只说明退出原因和一般性专业求助方向，不生成执行方案，也不生成验证卡。高风险排除**优先于**任何触发词或内容形状——哪怕它看起来像一篇普通经验帖。

## 三、交付什么

| 产物 | 内容 | 出现条件 |
|---|---|---|
| **经验试穿卡** | 经验拆解摘要、逐条判定（原步骤/个人条件/理由/来源/留痕）、关键未知 | 总是 |
| **可执行个人版** | 个人 v1＋执行方案：目标、完成标准、假设、资源、阶段、每次时间、时间预算、频率、检查点、兜底、停止规则、第一个动作、不做事项、来源、可行性检查 | 总是 |
| **验证卡** | 假设、最小动作、执行条件、成本、可逆性、频率/机会、指标、停止条件、决策规则、第一个动作 | 仅当关键未知会改变分支 |
| 分享稿 | 第一人称说明"我的条件/我改了什么/为什么/下一步怎么验证"，末尾标"AI 辅助整理" | 仅用户明确要求 |

硬性约束：首轮提问 ≤5，追问 ≤3，总计 ≤8；条件分支 ≤3（最多 2 条主分支 + 1 条兜底）；不给适配百分比或总分；不承诺提分、上岸、记忆增强、健康疗效；未实际执行的结果一律标"待验证"。

## 四、怎么用

安装本包后，粘贴**一篇**经验正文即可：

```text
试穿一下这个学习方法。我的目标是……，请先问我真正会改变方案的问题。
```

或者：

```text
这条经验适合我吗？别让我照抄，帮我改成能执行的版本。
```

多轮节奏：

1. 第一轮只做拆解并提问，不产出方案；
2. 你回答、部分回答或拒答；
3. 同一会话继续，生成三件产物；
4. 你确认后才进入画像/版本等"存"的动作。

拒答不会中断：未知项会保留，方案转为**条件式**（分支并列，不伪装成确定版本）。

## 五、目录与每个文件的作用

```text
experience-fitting/
├── SKILL.md                    模型实际执行的契约（何时用、门控、五步流程、交付格式、降级）
├── README.md                   本文件：给人看的项目介绍
├── assets/
│   ├── card-template.md        三件产物的文本模板（可直接填）
│   └── share-example.md        可选分享稿的格式示例
├── references/
│   ├── method.md               拆/对/改/试/存的方法细则、判定四档表、来源枚举、风险门控
│   ├── context-questions.md    提问池与配比（为什么问、会翻转哪条判定）
│   ├── domain-packs.md         领域包边界：学习成长为主、居家生活为轻量第二领域、其余走通用模式
│   ├── plan-and-verification.md 计划必备要素、时间组规则、检查点、兜底纪律、验证卡字段
│   ├── io-schema.md            可选 JSON 数据契约与封闭枚举（仅在校验时使用）
│   ├── profile-and-feedback.md 画像/版本的数据边界、确认写入、单备份、恢复与反馈节奏
│   ├── degradation.md          降级矩阵（无脚本、无持久化、无网络、上下文短、模型不可用、无图片）
│   └── eval-rubric.md          评测边界：哪些是脚本证据、哪些只是文字契约
├── scripts/
│   ├── validate_output.py      产物结构校验（字段、枚举、判定与步骤一一对应、分享稿状态）
│   ├── validate_plan.py        计划结构校验（时间求和、阶段归属、阈值格式、provenance、兜底条数）
│   └── profile_store.py        画像存储（show/upsert/delete/restore/export、原子写、单备份、回滚）
└── evals/
    ├── cases.json              20 个评测用例（13 个脚本/fixture + 7 个静态契约）
    ├── run_evals.py            评测器：跑用例 + 静态包检查，可用 --report 生成机器回执
    ├── last-results.json       最近一次运行的机器回执（由 --report 生成，不是手写）
    ├── manual-runs.md          人工多轮记录与历史失败案例
    ├── validation-report.md    验证报告：结果、证据边界、修复记录、仍开放项
    └── fixtures/               9 份完整产物样例
        ├── word200.json        学习/背词：完整产物与计划
        ├── word200-alt.json    同一经验换个人条件（用于比较判定变化）
        ├── reading.json        阅读方法
        ├── programming.json    编程练习
        ├── english.json        纯英文经验
        ├── home-drawer.json    居家收纳
        ├── conditional-home.json 关键信息拒答 → 条件式试穿
        ├── photography.json    技能学习（摄影）
        └── team-meeting.json   团队例会（通用模式，领域规则未覆盖）
```

## 六、可选的结构校验

核心交付**不依赖**脚本。需要确定性检查时，按 `references/io-schema.md` 把同一结果整理成 JSON，再运行：

```powershell
python scripts/validate_output.py evals/fixtures/word200.json
python scripts/validate_plan.py   evals/fixtures/word200.json
python scripts/validate_output.py evals/fixtures/team-meeting.json
python scripts/validate_plan.py   evals/fixtures/team-meeting.json
```

| 脚本 | 检查 | 不检查 |
|---|---|---|
| `validate_output.py` | 字段存在与类型、`status` 四值、判定与步骤一一对应、提问 3/5/8、分支 ≤3、条件式必须有卡、分享稿状态与标识 | 语义是否合理、来源是否真实、是否存在"适合度百分比"或"效果承诺"式表达 |
| `validate_plan.py` | 计划字段、`minutes` 有限正数、时间组求和与阶段归属、阶段名唯一、阈值格式（允许单位或 %）、provenance 每阶段一条、`habit_changes` 0–2、兜底至少 1 条、验证卡字段 | 伪实验、兜底是否真的覆盖四类、两个主分支+一个兜底的结构、方案是否可行 |

设计原则：**代码只做可计算、可枚举、可加总的约束**；"这句话算不算承诺""这个兜底算不算覆盖"这类判断交给模型与评审，不塞进正则。

没有 Python 时，直接按 `assets/card-template.md` 人工自检，并标注"未做自动校验"——不要猜 JSON 字段，也不要声称已通过。

## 七、画像与版本（可选）

默认**只在当前对话交付**，不写盘。只有你明确确认后，才会写入你指定的独立目录：

```powershell
python scripts/profile_store.py show   --data-dir "D:\my-experience-data"
python scripts/profile_store.py upsert --data-dir "D:\my-experience-data" --confirm --record-file "D:\confirmed-record.json"
python scripts/profile_store.py restore --data-dir "D:\my-experience-data" --confirm
python scripts/profile_store.py delete --data-dir "D:\my-experience-data" --id study_time --confirm
python scripts/profile_store.py export --data-dir "D:\my-experience-data"
```

- 数据目录必须由你指定并自行展开环境变量；脚本拒绝写入 Skill 包目录。
- 写操作必须显式 `--confirm`；未确认一律拒写。
- 只保留一个 `.bak`；主文件或备份写失败时按原始字节回滚。
- 无持久化环境用 `--session-only`，输出会明确标"未持久化，下次需手动带回"。
- 反馈只在本场三件产物交付后回收，每会话最多主动一次；v2 需要真实反馈，不是现场承诺。

## 八、降级能力

| 场景 | 行为 |
|---|---|
| 无脚本 | 用模板与人工清单完成三件产物，不声称已校验 |
| 无持久化 | 会话内保留状态，交付可复制的档案卡，明确不能跨会话 |
| `references/`、`assets/` 不可读 | 按 SKILL.md 内置的拆解项、判定四档与三件产物结构继续，标注"未做参考文件核对" |
| 无网络 | 核心流程照常；需要外部核实的断言保持"作者声称/未知" |
| 上下文短 | 单次处理 ≤1,500 字或 ≤12 步；超出按步骤边界切分，标注“第 n/m 段（原帖第 x–y 步）”并记录截断边界 |
| 模型不可用 | 可展示已生成示例，但必须明确"不是实时结果" |
| 无图片能力 | 直接交付 Markdown/文本卡；不请求任何账号或外部权限 |

## 九、评测与证据边界

```powershell
python evals/run_evals.py
python evals/run_evals.py --static-only
python evals/run_evals.py --report evals/last-results.json
```

- `evals/cases.json` 共 20 例：**13 项独立 fixture／脚本证据 + 7 项静态 Prompt 契约**。
- 静态契约只证明 Prompt 文字存在，不证明真实 Agent 会遵守。
- fixture 通过只证明结构与可计算约束成立，不证明来源真实、改造合理或方法有效。
- 负向用例的 PASS 表示"校验器按预期拒绝了无效数据"，不是无效产物通过。
- 真实 Agent 多轮记录见 `evals/manual-runs.md`；其中团队实例首次 JSON 序列化失败被单列保留，没有抹掉。
- `evals/last-results.json` 是机器回执；`evals/validation-report.md` 记录了修复历史与仍未解决的问题。

## 十、打包与自检

`SKILL.md` 必须位于 zip 根目录；文件数 ≤30，体积 <40MB。打包建议用 Python（相对路径，避免出现绝对路径条目）：

```python
import zipfile, pathlib
root = pathlib.Path("experience-fitting")
EXCLUDE = {"SKILL.reactive.json"}          # 与 evals/run_evals.py 的 package_preflight 共用同一集合
EXCLUDE_SUFFIX = {".pyc", ".zip"}
EXCLUDE_DIRS = {"__pycache__", ".git"}
with zipfile.ZipFile("experience-fitting.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root)
        if f.name in EXCLUDE or f.suffix in EXCLUDE_SUFFIX or EXCLUDE_DIRS & set(rel.parts):
            continue
        z.write(f, rel.as_posix())
```

不要在安装态目录直接打包（会带入 `SKILL.reactive.json`，条目会多 1 个）；先复制出一份干净源目录，或确保排除集合与 `evals/run_evals.py` 一致。`python evals/run_evals.py` 会同时打印 `PACK: entries=N | root=OK` 作为打包预演。

打包后建议解压到独立目录再跑一次 `python evals/run_evals.py`，确认"打出来的包"与源目录行为一致。

## 十一、版本记录

| 版本 | 变更 |
|---|---|
| 1.0.0 | 首次发布：五步流程、三件产物、9 个 fixture、20 例评测 |
| 1.1.0 | 补高风险排除优先级与引用缺失降级；安装态计数修正；收缩校验器：删除伪实验词表、打卡词表、`unknowns→卡` 代理与两条表达正则，语义判断交回模型；阈值允许单位/%、`habit_changes` 允许 0；回执与报告数字对齐 |
| 1.2.0 | 风险按动作分三级（Exit / Cautious / Standard），谨慎层复用“暂缓”并给保守替代；写死长文阈值（≤1,500 字或 ≤12 步）与去噪规则；交付改为结论先行、留痕降为可选附录；输出语言跟随提问语言；移出演示脚本（29 文件）；`run_evals` 新增内存打包预演，排除集合与 README 一致；`branches` 在 fitted 下可省略；分享稿补卡片版、5 条标题与封面截图说明；description 补“粘贴正文”与“收藏干货”触发词 |

> 发布流程与运营信息不属于 Skill 本身，已移出本包；本包只保留通用能力与可选分享稿。