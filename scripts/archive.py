#!/usr/bin/env python3
"""Dependency-free local operations on LifeTrace 1.0 JSON archives."""

import argparse
import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fail(message):
    raise ValueError(message)


def check_fields(obj, required, optional, where):
    if not isinstance(obj, dict):
        fail(f"{where}: expected object")
    missing = set(required) - set(obj)
    extra = set(obj) - set(required) - set(optional)
    if missing or extra:
        fail(f"{where}: missing {sorted(missing)}; unknown {sorted(extra)}")


def string(value, where, nonempty=True):
    if not isinstance(value, str) or (nonempty and not value.strip()):
        fail(f"{where}: expected nonempty string")


def number(value, where):
    if type(value) is not int or value < 1:
        fail(f"{where}: expected positive integer")


def uid(value, where):
    string(value, where)
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError):
        fail(f"{where}: invalid UUID")


def timestamp(value, where):
    string(value, where)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
    except ValueError:
        fail(f"{where}: expected timezone-aware ISO date-time")


def validate(data):
    check_fields(data, ["schema_version", "archive_id", "revision", "updated_at", "subject", "preferences", "entries", "tombstones"], [], "archive")
    if data["schema_version"] != "1.0.0":
        fail("unsupported schema_version")
    uid(data["archive_id"], "archive_id")
    number(data["revision"], "revision")
    timestamp(data["updated_at"], "updated_at")
    check_fields(data["subject"], ["display_name"], ["notes"], "subject")
    string(data["subject"]["display_name"], "display_name")
    if "notes" in data["subject"]:
        string(data["subject"]["notes"], "notes", False)
    check_fields(data["preferences"], ["recording_mode"], [], "preferences")
    if data["preferences"]["recording_mode"] not in ("balanced", "light", "deep"):
        fail("invalid recording_mode")
    if not isinstance(data["entries"], list) or not isinstance(data["tombstones"], list):
        fail("entries and tombstones must be arrays")
    ids = set()
    for i, entry in enumerate(data["entries"]):
        where = f"entries[{i}]"
        check_fields(entry, ["id", "kind", "status", "title", "content", "recorded_at", "updated_at", "version", "sources", "visibility", "history"], ["when_date", "when_text"], where)
        uid(entry["id"], where + ".id")
        if entry["id"] in ids:
            fail("duplicate entry id")
        ids.add(entry["id"])
        if entry["kind"] not in ("event", "reflection", "person", "place", "theme") or entry["status"] != "confirmed":
            fail(where + ": invalid kind or status")
        for field in ("title", "content"):
            string(entry[field], where + "." + field)
        for field in ("recorded_at", "updated_at"):
            timestamp(entry[field], where + "." + field)
        number(entry["version"], where + ".version")
        if entry["visibility"] not in ("private", "shareable"):
            fail(where + ": invalid visibility")
        if "when_date" in entry and "when_text" in entry:
            fail(where + ": choose one date representation")
        if "when_date" in entry:
            try:
                date.fromisoformat(entry["when_date"])
            except (ValueError, TypeError):
                fail(where + ": invalid when_date")
        if "when_text" in entry:
            string(entry["when_text"], where + ".when_text")
        if not isinstance(entry["sources"], list) or not entry["sources"]:
            fail(where + ": at least one source required")
        for j, source in enumerate(entry["sources"]):
            check_fields(source, ["type", "ref"], ["quote"], where + f".sources[{j}]")
            if source["type"] not in ("subject", "person", "document", "import"):
                fail(where + ": invalid source type")
            string(source["ref"], where + ".source.ref")
            if "quote" in source:
                string(source["quote"], where + ".source.quote", False)
        if not isinstance(entry["history"], list):
            fail(where + ": history must be array")
        versions = set()
        for previous in entry["history"]:
            check_fields(previous, ["version", "content", "updated_at"], [], where + ".history")
            number(previous["version"], where + ".history.version")
            string(previous["content"], where + ".history.content")
            timestamp(previous["updated_at"], where + ".history.updated_at")
            if previous["version"] >= entry["version"] or previous["version"] in versions:
                fail(where + ": invalid history version")
            versions.add(previous["version"])
    tomb_ids = set()
    for i, tomb in enumerate(data["tombstones"]):
        where = f"tombstones[{i}]"
        check_fields(tomb, ["id", "deleted_at", "version", "reason"], [], where)
        uid(tomb["id"], where + ".id")
        timestamp(tomb["deleted_at"], where + ".deleted_at")
        number(tomb["version"], where + ".version")
        string(tomb["reason"], where + ".reason")
        if tomb["id"] in tomb_ids or tomb["id"] in ids:
            fail("duplicate or live tombstoned id")
        tomb_ids.add(tomb["id"])
    return data


def read(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))


def write(path, data):
    validate(data)
    target = Path(path)
    if target.exists():
        fail(f"output exists: {target}; choose a new file")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bump(data):
    data["revision"] += 1
    data["updated_at"] = now()


def add(data, args):
    if not args.confirmed:
        fail("explicit --confirmed required after user approves exact candidate")
    entry = {
        "id": str(uuid.uuid4()), "kind": args.kind, "status": "confirmed",
        "title": args.title, "content": args.content,
        "recorded_at": now(), "updated_at": now(), "version": 1,
        "sources": [{"type": args.source_type, "ref": args.source_ref}],
        "visibility": args.visibility, "history": []
    }
    if args.when_date:
        entry["when_date"] = args.when_date
    if args.when_text:
        entry["when_text"] = args.when_text
    data["entries"].append(entry)
    bump(data)
    validate(data)
    return data


def delete(data, entry_id, reason):
    matches = [e for e in data["entries"] if e["id"] == entry_id]
    if len(matches) != 1:
        fail("entry ID not found")
    entry = matches[0]
    data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
    data["tombstones"].append({"id": entry_id, "deleted_at": now(), "version": entry["version"] + 1, "reason": reason})
    bump(data)
    return validate(data)


def merge(left, right):
    if left["archive_id"] != right["archive_id"]:
        fail("archive IDs differ")
    if left["subject"] != right["subject"] or left["preferences"] != right["preferences"]:
        fail("subject or preferences conflict")
    entries = {e["id"]: e for e in left["entries"]}
    for e in right["entries"]:
        if e["id"] in entries and entries[e["id"]] != e:
            fail(f"entry conflict: {e['id']}")
        entries[e["id"]] = e
    tombstones = {t["id"]: t for t in left["tombstones"]}
    for tomb in right["tombstones"]:
        current = tombstones.get(tomb["id"])
        if current and current != tomb:
            fail(f"tombstone conflict: {tomb['id']}")
        tombstones[tomb["id"]] = tomb
    for entry_id in tombstones:
        entries.pop(entry_id, None)
    result = {**left, "entries": sorted(entries.values(), key=lambda x: x["id"]), "tombstones": sorted(tombstones.values(), key=lambda x: x["id"])}
    result["revision"] = max(left["revision"], right["revision"]) + 1
    result["updated_at"] = now()
    return validate(result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate", help="validate a JSON archive")
    p.add_argument("file")
    p = sub.add_parser("init", help="create an empty local archive")
    p.add_argument("output")
    p.add_argument("--name", required=True)
    p = sub.add_parser("add", help="add one confirmed memory to a new output file")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--kind", choices=["event", "reflection", "person", "place", "theme"], default="event")
    p.add_argument("--title", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--when-date")
    p.add_argument("--when-text")
    p.add_argument("--source-type", choices=["subject", "person", "document", "import"], default="subject")
    p.add_argument("--source-ref", required=True)
    p.add_argument("--visibility", choices=["private", "shareable"], default="private")
    p = sub.add_parser("delete", help="remove one entry and record a tombstone")
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p = sub.add_parser("merge", help="conservatively merge two exports")
    p.add_argument("left")
    p.add_argument("right")
    p.add_argument("output")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            read(args.file)
        elif args.command == "init":
            data = {"schema_version": "1.0.0", "archive_id": str(uuid.uuid4()), "revision": 1, "updated_at": now(), "subject": {"display_name": args.name}, "preferences": {"recording_mode": "balanced"}, "entries": [], "tombstones": []}
            write(args.output, data)
        elif args.command == "add":
            write(args.output, add(read(args.input), args))
        elif args.command == "delete":
            write(args.output, delete(read(args.input), args.id, args.reason))
        elif args.command == "merge":
            write(args.output, merge(read(args.left), read(args.right)))
        print("OK")
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
