# agent-handoff test suite

Parallel batch verifier for `/handoff` + `/resume` skill patterns.

Runs deterministic simulations of every SKILL.md step and verifies all output patterns.

## Quick start

```bash
cd tests
python run_tests.py                     # 12 scenarios × 3 runs, 4 workers
python run_tests.py --workers 8 --runs 5  # heavier workload
python run_tests.py --scenario 01-basic-handoff  # single scenario
```

Requires **Python 3.8+**, stdlib only — no pip installs needed.

## What is tested

| Category | Checks |
|----------|--------|
| XML structure | root tag, version, all required elements |
| Slug format | `[a-z0-9][a-z0-9-]*[a-z0-9]` regex |
| Timestamp | ISO-8601 with timezone offset |
| `<status>` | one of: `in_progress`, `completed`, `blocked` |
| `<next_action>` | non-empty |
| `<platform>` | `vscode-copilot` |
| Index | updated, has entry, all 7 fields present |
| Transcript | exists, non-empty, has H1 header, has timestamp |
| Memory (project) | valid XML, `status` in active/superseded, confidence, session attr |
| Memory (user) | same as project |
| Collision | second handoff with same tag → `<name>-2` |
| Dedup | repeated fact → prior entry marked `status=superseded` |
| Resume exact | exact tag → loads correct session |
| Resume partial | substring tag → newest match wins |
| Resume no-match | unknown tag → `found=False` + available list |

## Output example

```
══════════════════════════════════════════════════════════════
  agent-handoff test runner
  12 scenarios × 3 runs = 36 jobs  (workers=4)
══════════════════════════════════════════════════════════════

  [  1/36] ✓ 01-basic-handoff                        r=1 (22/22) 14ms
  [  2/36] ✓ 02-auto-tag                             r=1 (20/20) 11ms
  ...
══════════════════════════════════════════════════════════════
  SCENARIO RESULTS
══════════════════════════════════════════════════════════════
  ✓ 01-basic-handoff                          3/3 runs   66/66 checks
  ✓ 02-auto-tag                               3/3 runs   60/60 checks
  ...
──────────────────────────────────────────────────────────────
  Runs:   36 PASS  0 FAIL  0 ERROR  / 36
  Checks: 756/756 (100.0%)
  Time:   1.23s
══════════════════════════════════════════════════════════════
```

## Architecture

```
tests/
├── run_tests.py    # CLI runner — ProcessPoolExecutor, statistics
├── simulate.py     # Deterministic SKILL.md step executor
├── verify.py       # Pattern checkers (~20 checks per handoff run)
├── scenarios.py    # 12 test scenario definitions
└── results/        # gitignored output (optional --output flag)
```
