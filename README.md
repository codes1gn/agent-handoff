<div align="center">

# 🔀 agent-handoff

### Session Memory Persistence for AI Coding Agents

[![Tests](https://img.shields.io/github/actions/workflow/status/codes1gn/agent-handoff/tests.yml?label=tests&style=flat-square)](https://github.com/codes1gn/agent-handoff/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/codes1gn/agent-handoff?style=flat-square&logo=github)](https://github.com/codes1gn/agent-handoff/stargazers)

[🌐 Website](https://codes1gn.github.io/agent-handoff) &bull;
[❓ Why](#why) &bull;
[📦 Install](#install) &bull;
[🚀 Usage](#usage) &bull;
[⚙️ How It Works](#how-it-works) &bull;
[🖥️ Platforms](#platforms) &bull;
[🧪 Testing](#testing)

</div>

---

---

## Why

AI coding assistants lose all context when a session ends. Starting a new session means re-explaining your codebase, the decisions you made, and what to do next — every single time.

```
Without agent-handoff:                      With agent-handoff:

  Session 1: "Help me refactor auth"         Session 1: "Help me refactor auth"
  Agent: Done!                               Agent: Done!
  --- context lost ---                       /handoff auth-refactor   ← save
                                             Saved. Tag: auth-refactor
  Session 2: "Continue auth work"
  Agent: I don't have context                Session 2:
         about what you were                 /resume auth-refactor    ← restore
         working on. Can you                 +--------------------------------+
         re-explain the project?             | RESUMED: auth-refactor         |
                                             | NEXT: Finish validateToken()   |
  Session 3: "..."                           +--------------------------------+
  --- re-explaining again ---                Agent: Continuing from line 47...
```

`/handoff` saves. `/resume` restores. Zero friction.

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

### Recommended — one-line per platform

```bash
# Clone once
git clone https://github.com/codes1gn/agent-handoff.git /tmp/ah

# VS Code Copilot (project-level)
cp -r /tmp/ah/handoff/ .github/skills/handoff/ && cp -r /tmp/ah/resume/ .github/skills/resume/

# Cursor (project-level)
cp -r /tmp/ah/handoff/ .cursor/skills/handoff/ && cp -r /tmp/ah/resume/ .cursor/skills/resume/

# Claude Code (project-level)
cp -r /tmp/ah/handoff/ .claude/skills/handoff/ && cp -r /tmp/ah/resume/ .claude/skills/resume/
```

### Personal install (all projects)

```bash
# VS Code Copilot
cp -r /tmp/ah/handoff/ ~/.copilot/skills/handoff/ && cp -r /tmp/ah/resume/ ~/.copilot/skills/resume/

# Cursor
cp -r /tmp/ah/handoff/ ~/.cursor/skills/handoff/ && cp -r /tmp/ah/resume/ ~/.cursor/skills/resume/

# Claude Code
cp -r /tmp/ah/handoff/ ~/.claude/skills/handoff/ && cp -r /tmp/ah/resume/ ~/.claude/skills/resume/
```

---

## Usage

```
/handoff                      # auto-name from topic + date
/handoff auth-refactor        # named session
/handoff "my feature work"    # spaces OK — slugified automatically

/resume                       # load most recent
/resume auth-refactor         # load by exact tag
/resume auth                  # partial match
```

---

## How It Works

The system has two layers:

```
Layer 1: Session State (per-handoff)       Layer 2: Persistent Memory (across all)
─────────────────────────────────────────  ─────────────────────────────────────────
<tag>.xml    → structured summary          project-memory.xml → stable project facts
<tag>.transcript.md → raw conversation     user-memory.xml    → user preferences

Loaded on /resume <tag>                    Loaded on every /resume automatically
```

**Data is self-contained** in `handoff/data/` — flat XML files, no database, works in any git repo.

```
handoff/data/
├── index.xml                   # session registry (newest first)
├── sessions/
│   ├── <tag>.xml               # structured session state
│   └── <tag>.transcript.md     # conversation transcript
└── memory/
    ├── project-memory.xml      # stable facts about this codebase
    └── user-memory.xml         # how this user prefers to work
```

**Memory is additive.** Conflicting facts are marked `superseded` — full audit trail preserved.

Full design: [`DESIGN.md`](DESIGN.md)

---

## Platforms

| Platform | Install path | Status |
|----------|-------------|--------|
| VS Code Copilot | `.github/skills/` or `~/.copilot/skills/` | ✅ Implemented |
| Cursor | `.cursor/skills/` or `~/.cursor/skills/` | ✅ Compatible |
| Claude Code | `.claude/skills/` or `~/.claude/skills/` | ✅ Compatible |
| OpenCode | `.opencode/skills/` | 🔜 Planned |
| Windsurf | `.windsurf/skills/` | 🔜 Planned |

---

## Testing

Verified at **7200/7200 checks passing** across 13 scenarios, 3 Python versions, 8 parallel workers:

```bash
cd tests
python run_tests.py                        # 13 scenarios x 3 runs, 4 workers
python run_tests.py --workers 8 --runs 10  # stress test (7200 checks)
python run_tests.py --list                 # list all scenario IDs
```

Requires Python 3.8+, stdlib only — zero pip installs.

CI runs automatically on every push via [GitHub Actions](.github/workflows/tests.yml).

---

## Repository Structure

```
agent-handoff/
├── README.md                     # This file
├── DESIGN.md                     # Full design document
├── LICENSE                       # MIT
├── handoff/
│   └── SKILL.md                  # /handoff skill (copy to install)
├── resume/
│   └── SKILL.md                  # /resume skill (copy to install)
├── handoff/data/                  # Self-contained data storage
│   ├── index.xml
│   ├── sessions/
│   └── memory/
├── tests/
│   ├── README.md                 # Testing guide
│   └── run_tests.py              # Parallel batch test runner
├── docs/
│   └── index.html                # GitHub Pages website
└── .github/
    └── workflows/tests.yml       # CI
```

---

## License

[MIT](LICENSE)

---

<p align="center">
  <sub>7,200/7,200 checks passing &bull; zero dependencies &bull; VS Code Copilot, Cursor, and Claude Code</sub>
</p>
