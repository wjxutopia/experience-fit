#!/usr/bin/env python3
"""经用户确认的本地画像/版本存储；仅标准库，单备份、原子写入、可降级。"""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
EMPTY = {"schema_version": 1, "records": []}


def atomic_write_bytes(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write(path, data):
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    atomic_write_bytes(path, payload)


def checked_paths(data_dir):
    if not data_dir:
        raise ValueError("需要 --data-dir，或显式使用 --session-only")
    root = Path(data_dir).expanduser().resolve()
    if root == PACKAGE_ROOT or PACKAGE_ROOT in root.parents:
        raise ValueError("用户数据不得写入 Skill 包目录")
    return root / "profile.json", root / "profile.json.bak"


def load(path):
    if not path.exists():
        return json.loads(json.dumps(EMPTY))
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("画像文件结构无效")
    return data


def portable(data, notice):
    lines = [notice, "# 可复制的个人档案卡"]
    for record in data.get("records", []):
        lines.append(f"- {record.get('id')} | {record.get('type')} | {record.get('value')} | 来源：{record.get('source')} | 范围：{record.get('scope')}")
    if not data.get("records"):
        lines.append("- 暂无已确认记录")
    return "\n".join(lines)


def restore_raw(path, payload):
    if payload is None:
        if path.exists():
            path.unlink()
    else:
        atomic_write_bytes(path, payload)


def commit_two_files(path, backup, primary_target, backup_target, current, previous_backup):
    """提交主文件和单备份；任一失败时按原始字节回滚，回滚失败保留双版本副本。"""
    primary_bytes = path.read_bytes() if path.exists() else None
    backup_bytes = backup.read_bytes() if backup.exists() else None
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, rescue_name = tempfile.mkstemp(prefix=".profile-restore-", suffix=".json", dir=str(path.parent))
    os.close(handle)
    rescue = Path(rescue_name)
    keep_rescue = False
    try:
        atomic_write(rescue, {"current": current, "previous_backup": previous_backup})
        try:
            atomic_write(path, primary_target)
            atomic_write(backup, backup_target)
        except (OSError, ValueError) as original_error:
            rollback_errors = []
            for target, payload in ((path, primary_bytes), (backup, backup_bytes)):
                try:
                    restore_raw(target, payload)
                except OSError as exc:
                    rollback_errors.append(f"{target}: {exc}")
            if rollback_errors:
                keep_rescue = True
                raise ValueError(f"写入失败且回滚未完成；双版本事务副本保留在 {rescue}；{'；'.join(rollback_errors)}") from original_error
            raise original_error
    finally:
        if not keep_rescue and rescue.exists():
            try:
                rescue.unlink()
            except OSError:
                pass  # 清理失败不改变已提交或已回滚的数据，也不伪报写失败。


def commit_update(path, backup, updated, data):
    previous_backup = load(backup) if backup.exists() else None
    commit_two_files(path, backup, updated, data, data, previous_backup)


def restore_previous(path, backup, data):
    previous = load(backup)
    commit_two_files(path, backup, previous, data, data, previous)


def get_record(args):
    if args.record_file:
        record = json.loads(Path(args.record_file).read_text(encoding="utf-8-sig"))
    elif args.record:
        record = json.loads(args.record)
    else:
        raise ValueError("upsert 需要 --record 或 --record-file")
    if not isinstance(record, dict):
        raise ValueError("record 必须是对象")
    for key in ("id", "type", "value", "source", "scope"):
        if record.get(key) in (None, "", [], {}):
            raise ValueError(f"record 缺少或为空：{key}")
    if record["type"] not in {"profile", "version"}:
        raise ValueError("record.type 仅支持 profile/version")
    record = dict(record)
    record["confirmed_at"] = datetime.now(timezone.utc).isoformat()
    return record


def main():
    parser = argparse.ArgumentParser(description="画像/版本：确认写入、单备份、恢复、删除、导出、会话降级")
    parser.add_argument("command", choices=["show", "upsert", "delete", "restore", "export"])
    parser.add_argument("--data-dir")
    parser.add_argument("--session-only", action="store_true", help="不写文件，只输出本次会话档案卡")
    parser.add_argument("--confirm", action="store_true", help="用户已明确确认本次写操作")
    parser.add_argument("--record")
    parser.add_argument("--record-file")
    parser.add_argument("--id")
    args = parser.parse_args()
    try:
        if args.session_only:
            if args.command in {"upsert", "delete", "restore"} and not args.confirm:
                raise ValueError("会话内变更也需要 --confirm")
            data = json.loads(json.dumps(EMPTY))
            if args.command == "upsert":
                data["records"].append(get_record(args))
            print(portable(data, "WARN: 会话内降级，未持久化；下次需手动带回。"))
            return 0
        path, backup = checked_paths(args.data_dir)
        data = load(path)
        if args.command == "show":
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "export":
            print(portable(data, "# 已确认的本地画像/版本导出"))
            return 0
        if not args.confirm:
            raise ValueError("写操作必须显式 --confirm；未写入")
        if args.command == "restore":
            if not backup.exists():
                raise ValueError("没有可恢复的单文件备份")
            restore_previous(path, backup, data)
            print("PASS: 已恢复上一版；恢复前状态已写入单文件备份")
            return 0
        if args.command == "upsert":
            record = get_record(args)
            updated = json.loads(json.dumps(data))
            records = [r for r in updated["records"] if r.get("id") != record["id"]]
            records.append(record)
            updated["records"] = records
            commit_update(path, backup, updated, data)
            print(f"PASS: 已确认写入 {record['id']}；单文件备份已更新")
            return 0
        if args.command == "delete":
            if not args.id:
                raise ValueError("delete 需要 --id")
            if not any(r.get("id") == args.id for r in data["records"]):
                raise ValueError(f"找不到记录：{args.id}")
            updated = json.loads(json.dumps(data))
            updated["records"] = [r for r in updated["records"] if r.get("id") != args.id]
            commit_update(path, backup, updated, data)
            print(f"PASS: 已删除 {args.id}；单文件备份已更新")
            return 0
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
