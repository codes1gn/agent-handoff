"""Pattern verification for agent-handoff outputs.

Each check is named (e.g. 'xml/session-name-slug') so failures are
precisely identified in test output.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

# Pattern constants (mirror SKILL.md rules)
SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')
ISO8601_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
VALID_STATUS = {'in_progress', 'completed', 'blocked'}
VALID_CONFIDENCE = {'high', 'medium', 'low'}
VALID_MEM_STATUS = {'active', 'superseded'}


class CheckList:
    """Collects named pass/fail results."""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def check(self, name: str, condition: bool, message: str = '') -> bool:
        self.results.append({'name': name, 'passed': bool(condition), 'message': message})
        return bool(condition)

    def summary(self) -> Dict[str, int]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        return {'total': total, 'passed': passed, 'failed': total - passed}


# ─── /handoff verifier ───────────────────────────────────────────────────────

class HandoffVerifier(CheckList):
    """Verifies all /handoff output files match expected patterns."""

    def __init__(self, base_dir: Path, handoff_result: dict):
        super().__init__()
        self.base = base_dir
        self.r = handoff_result  # from simulate_handoff()

    def run_all_checks(self):
        self._check_xml()
        self._check_index()
        self._check_transcript()
        self._check_memory('project', Path(self.r['project_mem_path']), 'project_memory', 'fact')
        self._check_memory('user', Path(self.r['user_mem_path']), 'user_memory', 'preference')

    # ── XML ──────────────────────────────────────────────────────────────────

    def _check_xml(self):
        xml_path = Path(self.r['xml_path'])
        prefix = 'xml'

        if not self.check(f'{prefix}/file-exists', xml_path.exists(), str(xml_path)):
            return

        try:
            tree = ET.parse(str(xml_path))
            root = tree.getroot()
            self.check(f'{prefix}/parseable', True)
        except ET.ParseError as e:
            self.check(f'{prefix}/parseable', False, str(e))
            return

        # Root
        self.check(f'{prefix}/root-tag', root.tag == 'handoff', f"got <{root.tag}>")
        self.check(f'{prefix}/version-attr', root.get('version') == '1.0', 'missing version=1.0')

        # <session>
        session = root.find('session')
        self.check(f'{prefix}/section-session', session is not None, 'missing <session>')
        if session is not None:
            name_el = session.find('name')
            self.check(f'{prefix}/session-name-present',
                       name_el is not None and bool(name_el.text), 'missing <name>')
            if name_el is not None and name_el.text:
                slug = name_el.text.strip()
                self.check(f'{prefix}/session-name-slug',
                           bool(SLUG_RE.match(slug)), f"'{slug}' fails slug pattern")
                # Matches our expected name
                self.check(f'{prefix}/session-name-consistent',
                           slug == self.r['name'],
                           f"XML name '{slug}' != result name '{self.r['name']}'")

            ts_el = session.find('timestamp')
            self.check(f'{prefix}/session-timestamp-present',
                       ts_el is not None and bool(ts_el.text), 'missing <timestamp>')
            if ts_el is not None and ts_el.text:
                self.check(f'{prefix}/session-timestamp-iso8601',
                           bool(ISO8601_RE.match(ts_el.text.strip())),
                           f"'{ts_el.text.strip()}' not ISO-8601+offset")

            plat = session.find('platform')
            self.check(f'{prefix}/session-platform',
                       plat is not None and plat.text == 'vscode-copilot',
                       f"got '{(plat.text if plat is not None else None)}'")

            tref = session.find('transcript_ref')
            self.check(f'{prefix}/session-transcript-ref',
                       tref is not None and bool(tref.text), 'missing <transcript_ref>')

        # <state>
        state = root.find('state')
        self.check(f'{prefix}/section-state', state is not None, 'missing <state>')
        if state is not None:
            goal_el = state.find('goal')
            self.check(f'{prefix}/state-goal',
                       goal_el is not None and bool((goal_el.text or '').strip()),
                       'missing/empty <goal>')

            status_el = state.find('status')
            self.check(f'{prefix}/state-status-present',
                       status_el is not None and bool(status_el.text), 'missing <status>')
            if status_el is not None and status_el.text:
                self.check(f'{prefix}/state-status-valid',
                           status_el.text.strip() in VALID_STATUS,
                           f"invalid status '{status_el.text.strip()}'")

            branch_el = state.find('branch')
            self.check(f'{prefix}/state-branch',
                       branch_el is not None and bool(branch_el.text), 'missing <branch>')

            self.check(f'{prefix}/state-modified-files',
                       state.find('modified_files') is not None, 'missing <modified_files>')

        # <progress>
        progress = root.find('progress')
        self.check(f'{prefix}/section-progress', progress is not None, 'missing <progress>')
        if progress is not None:
            na = progress.find('next_action')
            self.check(f'{prefix}/progress-next-action',
                       na is not None and bool((na.text or '').strip()),
                       'missing/empty <next_action>')
            self.check(f'{prefix}/progress-completed',
                       progress.find('completed') is not None, 'missing <completed>')
            self.check(f'{prefix}/progress-remaining',
                       progress.find('remaining') is not None, 'missing <remaining>')

        # Optional sections should be present (even if empty)
        for section in ('decisions', 'blockers', 'gotchas', 'memory_extractions'):
            self.check(f'{prefix}/section-{section}',
                       root.find(section) is not None, f'missing <{section}>')

    # ── Index ─────────────────────────────────────────────────────────────────

    def _check_index(self):
        index_path = Path(self.r['index_path'])
        prefix = 'index'

        if not self.check(f'{prefix}/file-exists', index_path.exists(), str(index_path)):
            return

        try:
            tree = ET.parse(str(index_path))
            root = tree.getroot()
            self.check(f'{prefix}/parseable', True)
        except ET.ParseError as e:
            self.check(f'{prefix}/parseable', False, str(e))
            return

        self.check(f'{prefix}/root-tag', root.tag == 'index', f"got <{root.tag}>")
        self.check(f'{prefix}/updated-attr', bool(root.get('updated')), 'missing updated attr')

        sessions = root.findall('session')
        self.check(f'{prefix}/has-sessions', len(sessions) > 0, 'empty index')

        our_name = self.r['name']
        matching = [s for s in sessions
                    if s.findtext('name') == our_name]
        self.check(f'{prefix}/has-our-session', len(matching) > 0,
                   f"session '{our_name}' not in index")

        # Newest-first: our session should be the first entry (or at least present)
        if sessions:
            first_name = sessions[0].findtext('name') or ''
            self.check(f'{prefix}/newest-first',
                       first_name == our_name or len(sessions) > 1,
                       f"expected '{our_name}' first, got '{first_name}'")

        if matching:
            entry = matching[0]
            for field in ('name', 'timestamp', 'platform', 'status', 'goal', 'file', 'transcript'):
                el = entry.find(field)
                self.check(f'{prefix}/entry-{field}',
                           el is not None and bool(el.text),
                           f"missing <{field}> in index entry")

    # ── Transcript ────────────────────────────────────────────────────────────

    def _check_transcript(self):
        tp = Path(self.r['transcript_path'])
        prefix = 'transcript'

        if not self.check(f'{prefix}/file-exists', tp.exists(), str(tp)):
            return

        content = tp.read_text(encoding='utf-8')
        self.check(f'{prefix}/non-empty', len(content.strip()) > 0)
        self.check(f'{prefix}/has-h1', content.startswith('# '), 'no H1 header')
        self.check(f'{prefix}/has-timestamp-ref', 'Captured at' in content, "no 'Captured at'")
        self.check(f'{prefix}/has-platform-ref', 'VS Code Copilot' in content)

    # ── Memory ────────────────────────────────────────────────────────────────

    def _check_memory(self, label: str, path: Path, root_tag: str, entry_tag: str):
        prefix = f'memory/{label}'

        if not path.exists():
            # Acceptable if no entries were expected
            return

        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
            self.check(f'{prefix}/parseable', True)
        except ET.ParseError as e:
            self.check(f'{prefix}/parseable', False, str(e))
            return

        self.check(f'{prefix}/root-tag', root.tag == root_tag, f"got <{root.tag}>")
        self.check(f'{prefix}/version-attr', root.get('version') == '1.0')

        entries = root.findall(entry_tag)
        for i, entry in enumerate(entries):
            ep = f'{prefix}/entry[{i}]'
            self.check(f'{ep}/status',
                       entry.get('status') in VALID_MEM_STATUS,
                       f"invalid status '{entry.get('status')}'")
            self.check(f'{ep}/confidence',
                       entry.get('confidence') in VALID_CONFIDENCE,
                       f"invalid confidence '{entry.get('confidence')}'")
            self.check(f'{ep}/session', bool(entry.get('session')), 'missing session attr')
            self.check(f'{ep}/timestamp', bool(entry.get('timestamp')), 'missing timestamp attr')
            self.check(f'{ep}/text',
                       entry.text is not None and len(entry.text.strip()) > 0,
                       'empty entry text')

    # ── Memory dedup check ────────────────────────────────────────────────────

    def check_memory_dedup(self, facts: List[str]):
        """After two sequential handoffs with same facts, verify superseded entries exist."""
        pm = Path(self.r['project_mem_path'])
        if not pm.exists() or not facts:
            return
        try:
            root = ET.parse(str(pm)).getroot()
        except ET.ParseError:
            return
        superseded = [e for e in root.findall('fact') if e.get('status') == 'superseded']
        self.check('memory/dedup/has-superseded-entries',
                   len(superseded) > 0,
                   f"expected superseded entries after dedup, found {len(superseded)}")
        active = [e for e in root.findall('fact') if e.get('status') == 'active']
        self.check('memory/dedup/active-entries-preserved',
                   len(active) >= len(facts),
                   f"expected {len(facts)} active entries, found {len(active)}")


# ─── /resume verifier ────────────────────────────────────────────────────────

class ResumeVerifier(CheckList):
    """Verifies /resume simulation output matches expected patterns."""

    def __init__(self, base_dir: Path, resume_spec: dict):
        super().__init__()
        self.base = base_dir
        self.spec = resume_spec

    def run_all_checks(self):
        from simulate import simulate_resume
        output = simulate_resume(self.spec, self.base)
        self._check_output(output)

    def _check_output(self, output: dict):
        expect_not_found = self.spec.get('expect_not_found', False)

        if expect_not_found:
            self.check('resume/expected-not-found',
                       not output.get('found', True),
                       'expected not-found but session was found')
            self.check('resume/not-found-has-available',
                       'available' in output,
                       'missing available list on not-found response')
            self.check('resume/not-found-has-error',
                       bool(output.get('error')), 'missing error message')
            return

        self.check('resume/found', output.get('found', False),
                   output.get('error', 'session not found'))
        if not output.get('found'):
            return

        expected_name = self.spec.get('expected_name')
        if expected_name is not None:
            self.check('resume/name-match',
                       output.get('name') == expected_name,
                       f"expected '{expected_name}', got '{output.get('name')}'")

        self.check('resume/has-goal', bool(output.get('goal')), 'no goal loaded')
        self.check('resume/has-next-action', bool(output.get('next_action')), 'no next_action')
        self.check('resume/has-status', output.get('status') in VALID_STATUS,
                   f"invalid status '{output.get('status')}'")
        self.check('resume/has-branch', bool(output.get('branch')), 'no branch')
        self.check('resume/memory-loaded', output.get('memory_loaded', False))
