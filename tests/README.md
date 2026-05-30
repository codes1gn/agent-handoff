# agent-handoff test suite

Parallel batch verifier for `/handoff` + `/resume` skill patterns.

Runs deterministic simulations of every SKILL.md step and verifies all output
patterns using `ProcessPoolExecutor` for parallelism. Stdlib only — no pip
installs needed.

## Quick start

```bash
cd tests
python run_tests.py                        # 13 scenarios x 3 runs, 4 workers
python run_tests.py --workers 8 --runs 10  # stress test
python run_tests.py --scenario 01-basic-handoff  # single scenario
python run_tests.py --list                 # list all scenario IDs
```

Requires **Python 3.8+**, stdlib only.

### Windows note

If `python` is not in your PATH (common on fresh Windows installs), use the
**embeddable package** — no installation required:

```powershell
# Download and extract
Invoke-WebRequest https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip -OutFile py.zip -UseBasicParsing
Expand-Archive py.zip -DestinationPath pyembed

# Enable stdlib
(Get-Content pyembed\python311._pth) -replace '#import site','import site' | Set-Content pyembed\python311._pth

# Run tests
cd tests
..\pyembed\python.exe run_tests.py --workers 4 --runs 3
```

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
| Collision | second handoff with same tag gets `-2` suffix |
| Dedup | repeated fact marks prior entry `status=superseded` |
| Resume exact | exact tag loads correct session |
| Resume partial | substring tag — newest match wins |
| Resume no-match | unknown tag returns `found=False` + available list |

## Output example

```
==============================================================
  agent-handoff test runner
  13 scenarios x 3 runs = 39 jobs  (workers=4)
==============================================================

  [  1/39] [ok] 01-basic-handoff              r=1 (66/66) 14ms
  [  2/39] [ok] 02-auto-tag                   r=1 (53/53) 11ms
  ...

==============================================================
  SCENARIO RESULTS
==============================================================
  [ok] 01-basic-handoff          10/10 runs   660/ 660 checks
  [ok] 02-auto-tag               10/10 runs   530/ 530 checks
  ...
--------------------------------------------------------------
  Runs  :  130 PASS  0 FAIL  0 ERROR  / 130 total
  Checks:  7200/7200 (100.0%)
  Time  :  0.66s wall  (15ms avg per run)
==============================================================
```

## Architecture

```
tests/
├── run_tests.py    # CLI runner -- ProcessPoolExecutor, statistics
├── simulate.py     # Deterministic SKILL.md step executor
├── verify.py       # Pattern checkers (~20 checks per handoff run)
├── scenarios.py    # 13 test scenario definitions
└── results/        # gitignored output
```

### Scenario types

| Type | Description |
|------|-------------|
| `handoff` (default) | Single handoff, verify all XML/index/transcript/memory patterns |
| `collision` | Two handoffs with same tag — second must get `-2` suffix |
| `dedup` | Two handoffs with overlapping facts — dedup marks old entries superseded |

Scenarios 11–13 include a `resume` sub-dict for round-trip handoff→resume testing.

## Adding scenarios

Edit `scenarios.py` and add a dict to `SCENARIOS`:

```python
{
    'id': '14-my-new-scenario',
    'description': 'What this tests',
    'tag': 'my-tag',
    'topic': 'some topic',
    'git': {'branch': 'main', 'commit': 'abc1234', 'status': 'clean'},
    'todos': [{'text': 'do something', 'priority': 'high'}],
    'project_facts': ['fact about codebase'],
    'user_facts': ['user preference'],
    'next_action': 'description of next step',
    'status': 'in_progress',
}
```
