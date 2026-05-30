# agent-handoff — Design Document

> Socratic design, 2026-05-30. Full discussion in [codes1gn/my-plan](https://github.com/codes1gn/my-plan).

## Design Principles

1. **Transcript as programmatic truth** — raw conversation captured immutably; all derived structures (summary, memory) can be regenerated from it
2. **Progressive disclosure** — on resume, load summary first (small, fast); transcript is fallback for edge cases
3. **XML as storage format** — Claude-series models parse XML reliably; template-as-harness produces consistent structured output
4. **Human UX via rendered reports** — users don't read XML files directly; they see formatted output at `/resume` time
5. **Zero database** — at personal scale (1-2 sessions/day, 20-50 memory facts), flat files outperform any DB by every metric
6. **Correction through conversation** — no `/forget` command; user states correction, agent updates memory in-place

## API

```
/handoff [tag-name]   — capture session state, write to XML + transcript
/resume  [tag-name]   — load context, render visual summary report
```

- `/handoff` with no tag → agent generates slug from session topic + date
- `/resume` with no tag → load most recent session from index.xml
- `/resume <partial>` → substring match, newest match wins

## Storage Structure

```
handoff/data/
├── index.xml                   # registry, newest first
├── sessions/
│   ├── <tag>.xml               # structured handoff (source of truth)
│   └── <tag>.transcript.md    # raw conversation (best-effort, immutable)
└── memory/
    ├── project-memory.xml      # facts about THIS codebase
    └── user-memory.xml         # how THIS user works
```

## Handoff XML Schema

Seven sections: `session` (metadata), `state` (git + todos + goal), `progress` (completed/remaining/next_action), `decisions`, `blockers`, `gotchas`, `memory_extractions` (project_fact + user_preference).

The full annotated template is embedded in `handoff/SKILL.md`.

## Memory Lifecycle

| Event | Action |
|-------|--------|
| `/handoff` | Extract facts → append `status=active` entries |
| New fact contradicts existing | Old: `status=superseded, superseded_by=<tag>` → New: `status=active` |
| User says "that's wrong" | Agent updates from conversation context |
| `/resume` | Load only `status=active` entries |

## Platform Notes

| Dimension | Cursor | VS Code Copilot | Claude Code |
|-----------|--------|-----------------|-------------|
| Project path | `.cursor/skills/` | `.github/skills/` | `.claude/skills/` |
| Personal path | `~/.cursor/skills/` | `~/.copilot/skills/` | `~/.claude/skills/` |
| Argument passing | Text appended, parsed in body | `argument-hint` field + text | `$ARGUMENTS` |
| Shell/git | Terminal tool (prose instructions) | Terminal tool (prose instructions) | `Bash` tool + `!backtick` injection |
| Skill-dir var | Not available | Not available | `${CLAUDE_SKILL_DIR}` |
| Interactive UI | `AskQuestion` | `#vscode/askQuestions` | `AskUserQuestion` |

## Competitive Gap

No existing GitHub project combines handoff + memory in a single portable skill file (GitHub search for "cursor memory SKILL.md" = 0 results as of 2026-05-30).

Key differentiators vs existing tools (baton, KimYx0207/3-layer, handoffkit, mem0):
- Combined handoff + memory in one skill
- XML template-as-harness (consistent agent output)
- Cross-platform single SKILL.md
- Visual rendered box at `/resume` (human UX)
- Transcript as immutable ground truth
