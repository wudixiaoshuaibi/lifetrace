# LifeTrace V1.0

An open Agent Skill for ordinary adults, combining everyday reflection with biography writing. Its default is **balanced recording**. Every example person and event in this repository is fictional.

## Install

Copy the whole `lifetrace` directory into the Skills directory of an [Agent Skills](https://agentskills.io/) compatible host. For Codex, use `~/.codex/skills/lifetrace`, refresh or restart skill discovery, then invoke `$lifetrace`. Other hosts have their own loading and file-persistence behavior; verify those capabilities in that host.

`SKILL.md` is the entry point. `references/` contains methods for interviews, writing, and archives. `schema/` contains the JSON Schema. `scripts/archive.py` uses only the Python 3.10+ standard library.

## Workflow

Talk naturally first. Before saving a candidate memory, show its exact wording, date or uncertainty, source, and privacy scope. Save it only after the person explicitly confirms it. Unconfirmed candidates never belong in the JSON archive.

```text
python scripts/archive.py init my-archive.json --name "Example Name"
python scripts/archive.py validate my-archive.json
python scripts/archive.py add my-archive.json my-archive-v2.json --confirmed --title "A move" --content "I moved to a new city around 2018." --when-text "around 2018" --source-ref "confirmed interview with subject"
python scripts/archive.py merge my-archive-v2.json other-export.json merged.json
python scripts/archive.py delete merged.json without-one-entry.json --id ENTRY_UUID --reason "subject requested deletion"
```

`--confirmed` is a CLI assertion, not a substitute for the person's actual confirmation. The tool never overwrites an existing output. Merge requires the same `archive_id`, stops on divergent same-ID entries, and preserves deletion tombstones against old exports. JSON is plaintext; `visibility` is a drafting and sharing cue, not encryption or access control.

Import by providing and validating a JSON file; export by copying a validated JSON file. The person chooses the storage location and sharing scope. Deleting an entry from a new file does not erase prior exports, backups, or host logs.

## Verify

From the project root:

```text
python -m unittest discover -s tests -v
python scripts/archive.py validate examples/fictional-profile.json
```

Codex's `skill-creator` also provides `quick_validate.py` for skill structure checks. Local tests cover the JSON utility; they do not prove cross-session persistence, automatic memory, encryption, or interview quality in any host.

## Limits

V1 is file based, with no background service or cloud account. For a later session, the person must provide the archive again, or the host must explicitly preserve and reopen it. Biography drafts should retain entry-ID source notes. Interpretations and polished prose do not become factual memories without separate confirmation. See [`references/archive-method.md`](references/archive-method.md) and [`references/conversation-and-writing.md`](references/conversation-and-writing.md).

License: MIT; see [`LICENSE`](LICENSE).
