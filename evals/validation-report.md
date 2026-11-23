# 验证报告

日期：2026-11-23。本报告包含冷眼审查修复及通用性加固后的最新结果，旧报告作废。下文第二轮至第四轮的历史小节中出现的“30 文件 / files=30”为当时状态；当前交付为 29 文件，数字以 `last-results.json` 为准。自动通过不等于模型语义正确或实践有效。

## 结果汇总

| 检查 | 结果 | 实际证据 |
|---|---|---|
| Python 语法 | PASS | AST 解析 scripts 3 个文件＋evals 1 个文件 |
| 独立 fixture | PASS | 9 个完整 JSON 均通过产物和计划校验 |
| 分类 evals | PASS | 20/20，其中 13 项独立 fixture／脚本证据，7 项静态 Prompt 契约 |
| 通用标识负向检查 | PASS | 删除 generic 文字标识后，输出校验器真实 FAIL |
| 画像正常与失败矩阵 | PASS | 未确认拒写、无效写不变、合法更新两阶段回滚、首次新目录和 restore 故障路径 |
| 真实 Agent 多轮指令遵循抽样 | 文本 PASS；序列化有失败记录 | 职场、摄影、团队三个子 Agent；团队首次 JSON 字段错误单列 FAIL |
| 无脚本/无持久化 | PASS（人工路径） | 3 学习＋1 居家纯 Prompt 记录 |
| 静态包约束 | PASS | 目录名与 slug 已统一；无本地 Markdown 断链 |
| 独立验证 Agent | SHIP | 复核当前文件和实际命令，未发现 OPEN 的 P0/P1 |

## 通用性加固

- description 已改为接受一篇包含具体做法的经验帖；学习成长仍为主，居家为轻量领域包，其他低风险领域使用通用模式。
- `domain_mode` 必填 `vertical/generic`；generic 必须明示“通用模式，领域规则未覆盖”。
- 通用模式不拒绝低风险陌生领域，不套用学习/居家专属指标，不冒充专业领域判断。
- 摄影归为技能学习，使用 `photography.json`；团队协作归为通用模式，使用 `team-meeting.json`。
- 团队计划时间为 2＋8＋3＋2＝15/15；摄影为 P0 30 分钟、P1 30 分钟两个时间组，各 30/30；均有来源、隐私边界和同轮变量冻结。

## 真实 Agent 证据与失败记录

三个全新子 Agent 只读取 Skill 和指定参考文件，不读取 evals、现有 fixture 或旧稿；均经过“首轮提问→模拟回答→同会话生成”。文本方案人工语义通过：职场复盘 5 问/3 分支、摄影 5 问/2 分支、团队例会 5 问/3 分支，三件产物完整。

团队 Agent 的文本方案正确，但首次 JSON 把阶段字段 `name` 写成 `phase`，结构校验应 FAIL。该失败已明确记录在 `manual-runs.md`；修正后的 `team-meeting.json` 才作为回归 fixture。不得把 20/20 解读为原 Agent 输出从未失败。

独立验证 Agent 无法访问那三个实例的原始完整会话，因此它独立确认的是当前文档、fixture 和运行结果，而不是为不可见原始输出背书。抽样不是市场 UI 测试，也不代表所有模型或真实用户实践。

## 静态检查明细

- `name: experience-fitting` 符合 slug 形式；description 单行且低于 1024 字符；SKILL.md 低于 50,000 字符。
- `scripts/` 只有 3 个产品脚本，全部使用 Python 标准库；无外部 API、网络、Pillow 或字体依赖。
- 无 `tests/` 等非标准目录；测试在 `evals/`；eval 数量为 20。
- 当前恰好 **30 个文件**，达到上限但未超限；总大小低于 40MB，精确值见 `last-results.json`。
- 打包排除 `__pycache__`、`.pyc` 和 zip；缓存不属于交付文件。
- PASS：开发目录、frontmatter slug 与发布 zip 已统一为 `experience-fitting`；最终 zip 不含外层目录。

## 证据边界

静态契约只证明 Prompt 文字存在，不证明真实 Agent 行为。fixture 通过不证明来源真实、改造合理或方法有效。负向用例的 PASS 表示校验器按预期拒绝无效数据。四个早期手动案例与三个真实 Agent 抽样均为模拟条件，没有真实用户实践。

## 最终 zip 核验

- PASS：`SKILL.md` 位于 zip 根目录，无外层目录或路径穿越。
- PASS（历史状态）：当时 30 个文件条目，未超过 30 文件、40MB；zip 本体低于本地客户端 5MB 导入限制。精确字节数和哈希以最终打包回执为准。
- PASS：逐项 CRC 与源文件内容一致性检查通过；包含 9 个独立 fixture、通用模式样本及真实 Agent 抽样记录。
- 发布文件：打包产物路径（此处不记录绝对路径）。尚未代为上传、扫码、确认或发布。

## 本轮最小修复与安装态回归（2026-11-23 第二轮）

本轮只做就地文本修改，不新增文件、不改判定逻辑、不改 description。

### 改动

| 文件 | 改动 | 目的 |
|---|---|---|
| `SKILL.md` | 高风险门控末尾追加“高风险排除优先于任何触发词或内容形状；即使输入看起来像经验帖，也先退出个性化建议。” | 关闭 U10（不触碰 description） |
| `references/method.md` | “拆解记录”末尾追加“内核可迁移不等于原步骤保留；迁移的是拆→对→改→试→存流程，不是把每条原步骤照搬。” | 关闭 P2-3 |
| `references/plan-and-verification.md` | 追加“如果计划同时声明阶段天数、总周期和总分钟数，三者必须能互相解释；口径不一致时先修正说明，不得同时输出两套总账。” | U7 的语义侧（不加自动校验） |

`evals/cases.json` **未改**：`run_evals.py` 已从 `check` 派生 `evidence_type`（L321）并写入 `last-results.json`（L332），汇总行已分列 `script/fixture` 与 `static-contract`。新增 `kind` 会形成第二事实源，故不做。

### 本轮关闭

| 编号 | 关闭依据 |
|---|---|
| U9 分列不可机器读 | `last-results.json` 每条已含 `evidence_type`；汇总行 `script/fixture=13 \| static-contract=7` |
| P2-3 判定措辞 | `method.md` 已加“内核可迁移≠原步骤保留” |
| U5 持久化未验证 | 包外记录 `review-output/logs/profile_e2e.log`（不随包交付），包内可复算 `run_evals.py` 的 `profile_flow()`：确认写入/未确认拒写/restore/delete/session-only/无效写不变/故障回滚 全部实跑 |
| U6 无产物全文 | 包外记录 `review-output/full/`（不随包交付）；包内仅有摘要 |
| U10 优先级 | `SKILL.md` 门控已加，未见静态检查冲突 |

### 仍开放

| 编号 | 状态 |
|---|---|
| U7 自动校验 | 未加；仅语义规则，靠人工/独立评审检查口径一致性 |
| V2 真实安装态冒烟 | 安装目录不可写（Access denied），本轮回归在**安装态克隆**上完成；需同步 3 个文件后复验 |
| U4 真实用户样本 | 未做；本轮仍为模拟回答 |

### 不可观测

- U3：20 条查询的真实自动触发准确率（平台无触发日志）。
- V1：Market 对手工复制安装的在线升级/卸载行为。
- 模型不可用降级：无法真实模拟，未声称已验证。

### 本轮实跑证据

- `python evals/run_evals.py` → EXIT=0，`20/20 PASS`，`STATIC: PASS | files=30`。
- `validate_output/validate_plan` × word200、team-meeting → 4 条均 EXIT=0。
- `profile_store` 端到端 → 包外记录 `review-output/logs/profile_e2e.log`（不随包交付），包内可复算 `profile_flow()`；restore 写失败注入后主文件与备份按原始字节回滚。
- 超长文本 2645 字符 → Agent 触发分段并标注 3 处边界；**Skill 未定义分段阈值**，Agent 自设“≤10 步且≤700 字符”。
- 非 UTF-8-BOM（GBK）→ `validate_output.py` EXIT=2，输出“无法读取 JSON：…invalid start byte”，未崩溃；UTF-8 BOM → EXIT=0。
- 无网络近似：`scripts/` 无任何网络导入；在 `HTTP(S)_PROXY=127.0.0.1:9` 下 `run_evals` 与 `profile_store` 均 EXIT=0。真实断网未模拟。
- 安装态冒烟（克隆）：activate 成功，`references/method.md` 与 `plan-and-verification.md` 可读，医疗停药帖 4/4 满足退出要求。

### 未伪造声明

本报告不含真实用户实践、真实断网、真实模型不可用、平台触发日志四类证据；相关项一律标“不可观测”或“未验证”。fixture 通过仍不代表语义正确或方法有效。

## 校验器收缩：语义判断交回模型（2026-11-23 第三轮）

原则：代码只做可计算、可枚举、可加总的约束；涉及“意思对不对”的判断交给模型与评审。

### 删除的语义代理

| 原断言 | 原想判断的语义 | 处理 |
|---|---|---|
| `unknowns` 非空 → 必须有 verification_card | 这个未知是否会翻转分支 | 删除；改为“声明 `outcome=conditional` 时必须给卡”的自洽检查 |
| `action` 精确等于伪实验词表 | 这是不是伪实验 | 删除；词表保留在 `plan-and-verification.md`，由模型/评审判断 |
| `metric` 等于“打卡/连续打卡” | 是否把打卡当唯一指标 | 删除 |
| `fallbacks` 至少 4 条 | 是否覆盖没时间/缺资源/中断/状态差 | 改为“至少 1 条”；覆盖性由评审判断 |

保留的结构约束：字段存在与类型、`source`/`content_type` 之外的封闭字段、时间组分钟加总、阶段名唯一、provenance 每阶段一条、提问 3/5/8、分支 ≤3、文件数与体积。

### 连带调整

- `H04` 由“脚本负例（validate_plan 应 FAIL）”改为静态契约“伪实验禁止清单仍在文档”；证据分类由 `14 script / 6 contract` 变为 **13 / 7**。
- `plan-and-verification.md`：`provenance` 改为“每个阶段一条”；习惯规则改为“同一轮只改一个主要习惯，确需两个须显式说明”。
- 摄影时间账按 fixture 实际改为“P0 30 分钟、P1 30 分钟，各 30/30”。
- `last-results.json` 已用 `--report` 重生成，与实际一致。

### 本轮复核（实跑）

- 删除验证卡但保留 1 个 unknown → 校验错误 `[]`（不再被误判）。
- 验证卡 `action="再调研一下"` → 脚本不再报伪实验（语义判断已移出）。
- `fallbacks=["没时间"]` → 校验错误 `[]`（条数要求放宽）。
- `outcome=conditional` 且无卡 → 报“声明条件式试穿时必须提供 verification_card”。
- 全量：`20/20 PASS`，`STATIC: PASS | files=30`。

## 第四轮：删除残留语义正则与结构补强（2026-11-23）

- `validate_output.py` 删除最后两条正则语义代理（适配/适合度百分比、效果承诺），`import re` 随之移除。
- `L07` 负向变体由 7 个减为 5 个（保留 9 问、4 分支、步骤错位、未执行分享、通用标识缺失）；百分比与承诺改为文档契约检查（`适配百分比`、`不得承诺提分`），语义判断归模型/评审。
- 阈值放宽为“数字 + 可选单位或 %”，`>40 分钟`、`>80%` 不再被拒；仍拒绝无运算符写法。
- `habit_changes` 允许 0（全部保留的合法场景），范围 0–2。
- 静态门不再豁免 `__pycache__`：目录白名单移除该项，出现缓存目录即 FAIL；`SYSTEM` 侧由 `sys.dont_write_bytecode` 保证正常运行不产生缓存。
- 文档对齐：`io-schema` 验证卡规则改为“conditional 必须有卡，fitted 按需”；`fallbacks` 两份文档改为“至少 1 条，尽量覆盖四类”；`profile-and-feedback` 的目录示例改为需先展开环境变量；README、eval-rubric 与本报告的 13/7 已统一。
- 时间口径：`io-schema` 改为“`minutes` 必须为有限正数，`duration` 只是展示文本”，与校验器实际检查范围一致。
- 回执自洽：`--report` 写入后再复算一次静态检查并重写，消除“回执字节数比实际少”的自引用偏差；当前回执 `files/bytes` 与实测逐字节一致。

## 本轮整改（2026-11-23 第五轮）

本轮按 `review-output/REMEDIATION-PLAN-2026-11-23.md` 批次 A–E 执行：只改文本与评测器，不改判定四档名，不新增文件，不引入第三方依赖。

### 改动表

| 文件 | 改动 | 目的 |
|---|---|---|
| `references/method.md` 第五节 | 单一风险门控改为 Exit / Cautious / Standard 三级表 ＋ 三条判定规则（逐步骤判、同帖可混合、拿不准降一级）；Cautious 复用“暂缓”并给保守替代 | P1-01 |
| `SKILL.md` L18 | 写死“≤1,500 字或 ≤12 步”“第 n/m 段（原帖第 x–y 步）”；加“先去噪再拆解” | P1-02、P1-03 |
| `SKILL.md` L20 | 门控第 3 条改三级表述，保留“**Exit 级**排除优先” | P1-01 |
| `references/degradation.md`、`README.md` | 同步长文阈值，删除“尚未写死，按内容自判” | P1-02 |
| `references/domain-packs.md` | 睡眠/饮食/体重/皮肤/运动强度/情绪调节进入 Cautious | P1-01 |
| `assets/card-template.md` | 顶部“结论区”三行；卡头加可选“风险级别”；“留痕”降为可选附录 | P1-05 |
| `references/plan-and-verification.md` | 开头加“先结论后论证” | P1-05 |
| `SKILL.md` 交付格式 | 顺序改为：一句话结论 → 3 个动作改动 → 第一个动作 →（Cautious）3 行风险提示 → 试穿卡 → 个人版 → 验证卡；加输出语言规则 | P1-05、P2-04 |
| `references/io-schema.md` | `risk_level` 可选（standard/cautious/exit，缺省 standard，exit 不生成方案）；`branches` 在 fitted 可省略 | A-1、P2-07 |
| `README.md` | 新增“它不做什么”5 条；打包示例与 `run_evals` 共用排除集合 ＋ 安装态打包警示 | C-3、P1-07 |
| `assets/share-example.md` | 追加可截图纯文本卡片版、5 条 ≤20 字标题、封面截图对应屏说明；移除包内活动标签 | P1-06 |
| `SKILL.md` frontmatter | description 补“粘贴正文/不支持链接/收藏干货”，保留全部原触发词 | P2-02、P2-03 |
| `evals/run_evals.py` | 新增 `EXCLUDE/EXCLUDE_SUFFIX/EXCLUDE_DIRS` 与 `package_preflight()`，输出 `PACK` 行；cases 上限改为 18–22；required 去掉已移出文件；高风险契约增加 Cautious 三词 | P1-07、P2-08 |
| `assets/` | 移出演示脚本至包外发布材料目录 | P2-01、P2-05 |
| 发布材料 | 清单、落位、笔记 3 版、宣传、差异化、证据台账全部迁至包外（版本统一 1.2.0），不随包交付 | 包外 |

### 本轮实跑（EXIT）

- `pack.bytes` 为内存预演的近似值，会随 zip 头时间戳浮动；硬约束只认 `entries ≤ 30` 与根 `SKILL.md`。
- `python evals/run_evals.py` → EXIT=0，`EVAL: 20/20 PASS | script/fixture=13 | static-contract=7`，`STATIC: PASS | files=29`，`PACK: entries=29 | root=OK`；精确字节以 `last-results.json` 为准。
- 打包预演排除验证：目录内放入 `SKILL.reactive.json` 后仍为 `entries=29`；再加 6 个文件 → `entries=35`（>30 触发 error）。
- 按 README 打包到系统临时目录下的 experience-fitting.zip → 29 条目、根 `SKILL.md`、无路径穿越、`testzip()` 无坏 CRC；字节数见 `last-results.pack.bytes`。
- 解压到不同名目录复跑 → EXIT=0，`20/20 PASS`，`STATIC: WARN | files=29`，唯一 WARN 为“目录名与 slug 不同”。

### 仍开放

| 项 | 状态 |
|---|---|
| 触发冒烟 8 条 | 未做；平台无触发日志，人工观察也不可复算 |
| 真实用户实践 | 无；所有结果仍标“待验证” |
| `risk_level` 脚本硬校验 | 未加；按计划只作可选字段与文档规则 |
| Cautious 语义是否过度收紧 | 未测；靠人工抽检，若连普通背单词也加风险区则回滚 `method.md` 第五节 |

### 不可观测

- 20 条查询的真实自动触发准确率（平台无日志）。
- 安装态是否保留 `references/` 与 `assets/`（P2-06）。
- 模型不可用降级、真实断网；仅以“无网络导入 + 代理黑洞”近似验证过。
- 3 次历史 Agent 运行的原始会话：不可获取、不可复现，只能保留摘要级记录（见包外证据台账）。

### 未伪造声明

本轮未新增任何真实用户或真实 Agent 运行记录；未补写会话 ID、时间戳与模型名。fixture 通过仍只证明结构与可计算约束成立。
