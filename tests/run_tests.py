#!/usr/bin/env python3
"""agent-handoff parallel batch test runner.

Runs deterministic simulations of SKILL.md steps in isolated temp dirs,
then verifies all output patterns. Uses ProcessPoolExecutor for parallelism.

Usage:
  python run_tests.py                          # all scenarios, 4 workers, 3 runs each
  python run_tests.py --workers 8 --runs 5    # heavier workload
  python run_tests.py --scenario 01-basic-handoff  # single scenario
  python run_tests.py --list                  # list scenario IDs
"""
import argparse
import concurrent.futures
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure tests/ is on sys.path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulate import simulate_handoff, simulate_resume
from verify import HandoffVerifier, ResumeVerifier
from scenarios import SCENARIOS


# --- worker (must be module-level for ProcessPoolExecutor pickling) ----------

def _run_worker(args: Tuple[dict, int]) -> Dict[str, Any]:
    """Execute one scenario run in an isolated temp directory."""
    scenario, run_id = args
    start = time.perf_counter()

    try:
        with tempfile.TemporaryDirectory(
            prefix=f'aht-{scenario["id"][:12]}-r{run_id}-'
        ) as tmpdir:
            base = Path(tmpdir)
            scenario_type = scenario.get('type', 'handoff')
            all_checks = []

            if scenario_type == 'collision':
                # Run handoff twice with the same tag
                r1 = simulate_handoff(scenario, base)
                r2 = simulate_handoff(scenario, base)  # identical tag -> collision

                v = HandoffVerifier(base, r1)
                v.run_all_checks()
                # Collision-specific checks
                expected_suffix = f"{r1['name']}-2"
                v.check('collision/names-differ',
                        r1['name'] != r2['name'],
                        f"both got name='{r1['name']}'")
                v.check('collision/second-gets-suffix',
                        r2['name'] == expected_suffix,
                        f"expected '{expected_suffix}', got '{r2['name']}'")
                all_checks = v.results

            elif scenario_type == 'dedup':
                # First handoff
                r1 = simulate_handoff(scenario, base, enable_dedup=False)
                # Second handoff with same facts, dedup enabled
                scenario2 = {**scenario, 'tag': scenario['tag'] + '-v2'}
                r2 = simulate_handoff(scenario2, base, enable_dedup=True)

                v = HandoffVerifier(base, r2)
                v.run_all_checks()
                v.check_memory_dedup(scenario.get('project_facts', []))
                all_checks = v.results

            else:  # default: single handoff + optional resume
                result = simulate_handoff(scenario, base)
                v = HandoffVerifier(base, result)
                v.run_all_checks()
                all_checks = list(v.results)

                if 'resume' in scenario:
                    rv = ResumeVerifier(base, scenario['resume'])
                    rv.run_all_checks()
                    all_checks.extend(rv.results)

            total = len(all_checks)
            passed = sum(1 for c in all_checks if c['passed'])
            failed = total - passed
            elapsed_ms = round((time.perf_counter() - start) * 1000)

            return {
                'scenario': scenario['id'],
                'run_id': run_id,
                'status': 'PASS' if failed == 0 else 'FAIL',
                'total': total,
                'passed': passed,
                'failed': failed,
                'elapsed_ms': elapsed_ms,
                'failures': [c for c in all_checks if not c['passed']],
            }

    except Exception:
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        return {
            'scenario': scenario['id'],
            'run_id': run_id,
            'status': 'ERROR',
            'total': 0, 'passed': 0, 'failed': 0,
            'elapsed_ms': elapsed_ms,
            'error': traceback.format_exc(),
            'failures': [],
        }


# --- statistics + formatting -------------------------------------------------

def _print_stats(all_results: List[dict], elapsed: float) -> bool:
    """Print per-scenario stats. Returns True if all runs passed."""
    by_sid: Dict[str, dict] = {}
    for r in all_results:
        sid = r['scenario']
        if sid not in by_sid:
            by_sid[sid] = {
                'runs': 0, 'passed_runs': 0,
                'total_checks': 0, 'passed_checks': 0,
                'failures': {},  # name -> message (deduped)
                'errors': [],
            }
        s = by_sid[sid]
        s['runs'] += 1
        if r['status'] == 'PASS':
            s['passed_runs'] += 1
        s['total_checks'] += r['total']
        s['passed_checks'] += r['passed']
        for f in r.get('failures', []):
            s['failures'][f['name']] = f.get('message', '')
        if r['status'] == 'ERROR':
            s['errors'].append(r.get('error', ''))

    W = 62
    print(f"\n{'='*W}")
    print(f"  SCENARIO RESULTS")
    print(f"{'='*W}")

    for sid, s in by_sid.items():
        run_rate = s['passed_runs'] / s['runs'] * 100
        icon = '[ok]' if run_rate == 100 else ('[~~]' if run_rate > 0 else '[!!]')
        print(
            f"  {icon} {sid:<40s} "
            f"{s['passed_runs']:2d}/{s['runs']} runs  "
            f"{s['passed_checks']:4d}/{s['total_checks']:4d} checks"
        )
        for name, msg in s['failures'].items():
            tail = f': {msg}' if msg else ''
            print(f"      FAIL {name}{tail}")
        for err in s['errors'][:1]:  # show first error per scenario
            for line in err.splitlines()[-5:]:
                print(f"      | {line}")

    total_runs = len(all_results)
    pass_runs = sum(1 for r in all_results if r['status'] == 'PASS')
    fail_runs = sum(1 for r in all_results if r['status'] == 'FAIL')
    err_runs = sum(1 for r in all_results if r['status'] == 'ERROR')
    total_checks = sum(r['total'] for r in all_results)
    passed_checks = sum(r['passed'] for r in all_results)
    pct = passed_checks / max(total_checks, 1) * 100
    avg_ms = sum(r['elapsed_ms'] for r in all_results) / max(total_runs, 1)

    print(f"\n{'-'*W}")
    print(f"  Runs  :  {pass_runs} PASS  {fail_runs} FAIL  {err_runs} ERROR  / {total_runs} total")
    print(f"  Checks:  {passed_checks}/{total_checks} ({pct:.1f}%)")
    print(f"  Time  :  {elapsed:.2f}s wall  ({avg_ms:.0f}ms avg per run)")
    print(f"{'='*W}\n")

    return fail_runs == 0 and err_runs == 0


# --- main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='agent-handoff parallel batch test runner'
    )
    parser.add_argument('--workers', type=int, default=4,
                        help='Parallel worker processes (default: 4)')
    parser.add_argument('--runs', type=int, default=3,
                        help='Runs per scenario for isolation/consistency check (default: 3)')
    parser.add_argument('--scenario', type=str, default=None,
                        help='Run a specific scenario by ID')
    parser.add_argument('--list', action='store_true',
                        help='List all scenario IDs and exit')
    args = parser.parse_args()

    if args.list:
        print('Available scenarios:')
        for s in SCENARIOS:
            print(f"  {s['id']:<42s}  {s.get('type', 'handoff'):<10s}  {s['description'][:60]}")
        return

    scenarios = SCENARIOS
    if args.scenario:
        scenarios = [s for s in SCENARIOS if s['id'] == args.scenario]
        if not scenarios:
            print(f"ERROR: scenario '{args.scenario}' not found. Use --list to see all.")
            sys.exit(1)

    # Build workload: (scenario, run_id) tuples -- each runs in its own process
    workload: List[Tuple[dict, int]] = [
        (s, run_id)
        for s in scenarios
        for run_id in range(1, args.runs + 1)
    ]
    total_jobs = len(workload)
    W = 62

    print(f"\n{'='*W}")
    print(f"  agent-handoff test runner")
    print(f"  {len(scenarios)} scenario(s) x {args.runs} run(s) = {total_jobs} jobs  (workers={args.workers})")
    print(f"{'='*W}\n")

    all_results: List[dict] = []
    completed = 0
    wall_start = time.perf_counter()

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        fut_map = {executor.submit(_run_worker, job): job for job in workload}
        for fut in concurrent.futures.as_completed(fut_map):
            result = fut.result()
            all_results.append(result)
            completed += 1
            icon = {'PASS': '[ok]', 'FAIL': '[!!]', 'ERROR': '[EE]'}.get(result['status'], '[??]')
            print(
                f"  [{completed:3d}/{total_jobs}] {icon} "
                f"{result['scenario']:<36s} "
                f"r={result['run_id']} "
                f"({result['passed']}/{result['total']}) "
                f"{result['elapsed_ms']}ms"
            )

    wall_elapsed = time.perf_counter() - wall_start
    success = _print_stats(all_results, wall_elapsed)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
