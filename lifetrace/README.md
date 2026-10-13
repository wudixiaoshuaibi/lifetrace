# LifeTrace · 人生有迹 V1.0

面向普通成年人的开源 Agent Skill：陪伴日常回顾，并从本人确认的记忆中逐步形成动态大纲与传记草稿。默认采用**平衡记录模式**。本仓库的人物和经历示例均为虚构。

## 安装

将整个 `lifetrace` 文件夹复制到支持 [Agent Skills](https://agentskills.io/) 的宿主的 Skills 目录。在 Codex 中，可放入 `~/.codex/skills/lifetrace`，重启或刷新技能列表后调用 `$lifetrace`。其他宿主需按各自的 Skill 加载方式安装；它们是否执行脚本、保留文件或延续会话，应在该宿主中分别验证。

项目根目录的 `SKILL.md` 是入口；`references/` 是访谈、写作与档案方法；`schema/` 是 JSON Schema；`scripts/archive.py` 是仅依赖 Python 3.10+ 标准库的本地工具。可直接复制本文件夹，也可解压发布包后安装。

## 使用方式

先与用户自然交谈。需要保存时，向用户展示候选记忆的**准确措辞、时间、来源和私密范围**，获得明确确认后才写入档案。未经确认的候选内容不能进入 JSON。

```text
python scripts/archive.py init my-archive.json --name "示例姓名"
python scripts/archive.py validate my-archive.json
python scripts/archive.py add my-archive.json my-archive-v2.json --confirmed --title "一次搬家" --content "我在 2018 年前后搬到了新城市。" --when-text "2018 年前后" --source-ref "本人确认的访谈"
python scripts/archive.py merge my-archive-v2.json other-export.json merged.json
python scripts/archive.py delete merged.json without-one-entry.json --id ENTRY_UUID --reason "本人要求删除"
```

以上 `--confirmed` 只是命令行的显式标志，不能替代真实的用户确认。工具不会覆写已有输出文件。`merge` 只接受同一个 `archive_id`，对同 ID 的不同内容报冲突，删除标记会压过旧导出中的条目。JSON 为明文；`visibility` 是写作和分享提示，不是加密或权限控制。

导入是提供 JSON 文件并校验；导出是复制经过校验的 JSON 文件。人物档案属于用户，请由用户选择存放位置和分享范围。删除当前文件中的条目不能清除既有导出、副本或宿主日志。

## 验证

在项目根目录运行：

```text
python -m unittest discover -s tests -v
python scripts/archive.py validate examples/fictional-profile.json
```

另可用 Codex 的 `skill-creator` 提供的 `quick_validate.py` 检查 Skill 入口格式。测试验证本地 JSON 工具；不会证明某个宿主已经实现跨会话持久化、自动记忆、加密或端到端访谈质量。

## 范围与限制

V1 是文件驱动的 Skill，没有后台服务或云账号。跨会话继续使用时，需要用户重新提供档案，或由宿主明确保存并重新开放该文件。写作输出应保留条目 ID 的依据，推断和文学化表达不能自行变成事实记忆。详见 [`references/archive-method.md`](references/archive-method.md) 与 [`references/conversation-and-writing.md`](references/conversation-and-writing.md)。

许可：MIT，见 [`LICENSE`](LICENSE)。
