# agent-handoff

[![tests](https://github.com/codes1gn/agent-handoff/actions/workflows/tests.yml/badge.svg)](https://github.com/codes1gn/agent-handoff/actions/workflows/tests.yml)

> `/handoff` + `/resume` — cross-session memory and context continuity for AI coding assistants.

A portable, zero-dependency skill pair that saves and restores your AI coding session state. Works across **VS Code Copilot**, **Cursor**, and **Claude Code** via the [agentskills.io](https://agentskills.io) open standard.

---

## What It Does

**`/handoff [tag-name]`** — Save current session state:
- Captures git state, active todos, decisions, blockers, gotchas
- Extracts stable facts into persistent memory (project-level + user-level)
- Writes a structured XML file + conversation transcript
- Registers the session in an index for fast lookup

**`/resume [tag-name]`** — Restore a saved session:
- Loads the session XML + relevant memory
- Renders a visual summary box with next action highlighted
- Ready to continue immediately — no context re-explanation needed

```
+------------------------------------------------------------------+
| RESUMED: auth-refactor-2026-05-30                                |
+------------------------------------------------------------------+
| GOAL    | Refactor auth module to use JWT instead of sessions    |
| STATUS  | in_progress                                            |
| BRANCH  | feature/jwt-auth                                       |
+------------------------------------------------------------------+
| NEXT ACTION                                                      |
|   Finish validateToken() in src/auth/jwt.ts (line 47)           |
+------------------------------------------------------------------+
| MEMORY LOADED                                                    |
| 6 project facts  4 user preferences                              |
+------------------------------------------------------------------+
```

---

## Install

### VS Code Copilot (project-level)

```bash
# From your project root:
cp -r handoff/ .github/skills/handoff/
cp -r resume/  .github/skills/resume/
```

### VS Code Copilot (personal — all projects)

```bash
cp -r handoff/ ~/.copilot/skills/handoff/
cp -r resume/  ~/.copilot/skills/resume/
```

### Cursor (project-level)

```bash
cp -r handoff/ .cursor/skills/handoff/
cp -r resume/  .cursor/skills/resume/
```

### Cursor (personal)

```bash
cp -r handoff/ ~/.cursor/skills/handoff/
cp -r resume/  ~/.cursor/skills/resume/
```

### Claude Code

```bash
cp -r handoff/ .claude/skills/handoff/
cp -r resume/  .claude/skills/resume/
```

---

## Usage

```
/handoff                      # auto-name from topic + date
/handoff auth-refactor        # named session
/handoff "my feature work"    # spaces OK -- slugified automatically

/resume                       # load most recent
/resume auth-refactor         # load by exact tag
/resume auth                  # partial match
```

---

## Data Storage

All data is self-contained in the `handoff/data/` directory:

```
handoff/data/
├── index.xml                   # session registry (newest first)
├── sessions/
│   ├── <tag>.xml               # structured session state
│   └── <tag>.transcript.md    # conversation transcript (best-effort)
└── memory/
    ├── project-memory.xml      # stable facts about this codebase
    └── user-memory.xml         # how this user prefers to work
```

**Memory is additive.** Conflicting facts are marked `superseded` (not deleted) — full audit trail preserved. No database. Flat XML files work perfectly at personal scale.

---

## Design

- **XML as storage format** — Claude-series models parse XML reliably; template-as-harness produces consistent output
- **Transcript as ground truth** — raw conversation is immutable; summary XML is derived from it
- **Progressive disclosure** — `/resume` loads summary first; transcript is available for verification
- **No `/forget` command** — correction via natural conversation; agent re-reads transcript if needed
- **Zero dependencies** — file writes only; works in any git repo

Full design document: [`DESIGN.md`](DESIGN.md)

---

## Compatibility

| Platform | Path | Status |
|----------|------|--------|
| VS Code Copilot | `.github/skills/` or `~/.copilot/skills/` | Implemented |
| Cursor | `.cursor/skills/` or `~/.cursor/skills/` | Compatible (same SKILL.md) |
| Claude Code | `.claude/skills/` or `~/.claude/skills/` | Compatible + Claude Code enhancements |

---

## Testing

The `tests/` directory contains a parallel batch test suite — verified locally at **7200/7200 checks passing** across 13 scenarios:

```bash
cd tests
python run_tests.py                        # 13 scenarios x 3 runs, 4 workers
python run_tests.py --workers 8 --runs 10  # stress test
python run_tests.py --list                 # list all scenario IDs
```

Requires Python 3.8+, stdlib only — no pip installs needed.

---

## License

MIT
