# 画像、版本与反馈

## 用户数据边界

画像和版本只存用户指定的独立目录，例如用户数据目录下的 experience-fitting 子目录（脚本不展开环境变量，请先自行展开为绝对路径）或用户选择的可写目录；绝不能存进 Skill 包。每条记录含 `id`、`type`（profile/version）、`value`、`source`、`scope`、`confirmed_at`。版本记录另含 `status`，没有实践用“待验证/未执行”。

自动抽取只生成候选并展示。必须得到用户明确确认后才执行写入；禁止把“继续”“生成卡片”视为默认同意。用户可查看、修改、删除、恢复上一版和导出文本。首版只保留一个 `.bak`，不做多版本历史、云同步或跨设备。upsert/delete 在完整校验后才提交，主文件或备份写失败均按原始字节回滚。restore 与普通更新共用临时事务副本保护当前与上一版；成功或完整回滚后删除临时副本，回滚失败则保留副本并报告路径。

## 三个典型命令

```powershell
python scripts/profile_store.py show --data-dir "D:\my-experience-data"
python scripts/profile_store.py upsert --data-dir "D:\my-experience-data" --confirm --record '{\"id\":\"study_time\",\"type\":\"profile\",\"value\":\"工作日40分钟\",\"source\":\"2026-11-23回答\",\"scope\":\"learning\"}'
python scripts/profile_store.py delete --data-dir "D:\my-experience-data" --id study_time --confirm
```

PowerShell 的 JSON 引号需按终端规则转义；也可使用 `--record-file` 读取 UTF-8 JSON。恢复用 `restore --confirm`，导出用 `export`。无 `--confirm` 的 upsert/delete/restore 不写文件。

无写入目录时使用 `--session-only`，脚本只输出本次会话可复制的记录和“未持久化”提示；下次由用户手动带回，不假装跨会话记住。

## 画像冲突

新回答与画像不一致时，保留当前对话的两条事实和来源，询问本次采用哪条。用户确认修改后才覆盖并备份。模型不得自动选择“更新的一条更可信”。

## 非阻塞反馈

- 入口：有待反馈卡时仅提示一次“有 1 张待反馈经验卡”，可以忽略，绝不阻止新试穿。
- 时机：本次试穿卡、个人版和按需验证卡全部交付之后，才问最近一张旧卡；每个会话最多主动问一次。
- 选项：没执行；执行了但没记录；有记录/有结果；已放弃；不再相关。
- 更新：没执行→未执行；口述无记录→低证据/证据不足；有记录→用户确认后形成 v2；已放弃→记录原因并归档；不再相关→退役。
- 跳过：记“本次未回收”，不连续打扰；用户可关闭提醒。

未执行不能判定方法无效；一次反馈不能推广为长期或普遍结论。反馈和 v2 属于增强能力，不纳入主演示范围。
