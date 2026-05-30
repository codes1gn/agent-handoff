"""Deterministic simulation of /handoff and /resume SKILL.md steps.

Implements every step from SKILL.md exactly as specified.
Used as test fixture generator — not an AI, just the reference logic.
"""
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

TZ_PLUS8 = timezone(timedelta(hours=8))


# ─── helpers ────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """SKILL.md slugification: lowercase, spaces+underscores→hyphens, strip non-alnum."""
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    if len(text) < 2:
        text = ('s-' + text).strip('-') if text else 'session'
    return text


def iso_now() -> str:
    return datetime.now(TZ_PLUS8).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def today_str() -> str:
    return datetime.now(TZ_PLUS8).strftime("%Y-%m-%d")


def _pretty_xml(root: ET.Element) -> str:
    raw = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(raw)
    lines = dom.toprettyxml(indent='  ', encoding=None).split('\n')
    # Replace minidom's plain declaration with the full UTF-8 one
    if lines and lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    # Remove trailing blank lines minidom adds
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines) + '\n'


def _get_text(el: Optional[ET.Element], xpath: str) -> str:
    if el is None:
        return ''
    found = el.find(xpath)
    return (found.text or '').strip() if found is not None else ''


# ─── Step 0: tag extraction ──────────────────────────────────────────────────

def extract_tag(scenario: dict) -> str:
    """Step 0: extract and slugify tag, or auto-generate from goal+date."""
    raw_tag = scenario.get('tag', '').strip()
    if raw_tag:
        return slugify(raw_tag)
    # Auto-generate: topic slug + date
    topic = slugify(scenario.get('goal', 'session'))[:20].rstrip('-')
    return f"{topic}-{today_str()}"


# ─── collision resolution ────────────────────────────────────────────────────

def resolve_name(name: str, sessions_dir: Path) -> str:
    """If <name>.xml exists, append -2, -3, ... until unique."""
    if not (sessions_dir / f"{name}.xml").exists():
        return name
    suffix = 2
    while (sessions_dir / f"{name}-{suffix}.xml").exists():
        suffix += 1
    return f"{name}-{suffix}"


# ─── Step 5: memory update ───────────────────────────────────────────────────

def _update_memory(
    path: Path,
    root_tag: str,
    entry_tag: str,
    entries: List[str],
    session_name: str,
    timestamp: str,
    enable_dedup: bool = False,
):
    """Append memory entries. If enable_dedup, mark matching active entries superseded."""
    if not entries:
        return

    if path.exists():
        tree = ET.parse(str(path))
        root = tree.getroot()
    else:
        root = ET.Element(root_tag, version='1.0')

    for text in entries:
        if enable_dedup:
            # Mark matching active entries as superseded
            for existing in root.findall(entry_tag):
                if (existing.get('status') == 'active'
                        and existing.text
                        and existing.text.strip()[:30] == text[:30]):
                    existing.set('status', 'superseded')
                    existing.set('superseded_by', session_name)

        el = ET.SubElement(root, entry_tag,
                           confidence='high',
                           status='active',
                           session=session_name,
                           timestamp=timestamp)
        el.text = text

    path.write_text(_pretty_xml(root), encoding='utf-8')


# ─── Step 6: index update ────────────────────────────────────────────────────

def _update_index(
    path: Path,
    name: str,
    timestamp: str,
    status: str,
    goal: str,
    file_ref: str,
    transcript_ref: str,
):
    if path.exists():
        tree = ET.parse(str(path))
        root = tree.getroot()
        root.set('updated', timestamp)
    else:
        root = ET.Element('index', version='1.0', updated=timestamp)

    entry = ET.Element('session')
    ET.SubElement(entry, 'name').text = name
    ET.SubElement(entry, 'timestamp').text = timestamp
    ET.SubElement(entry, 'platform').text = 'vscode-copilot'
    ET.SubElement(entry, 'status').text = status
    ET.SubElement(entry, 'goal').text = goal[:80]
    ET.SubElement(entry, 'file').text = file_ref
    ET.SubElement(entry, 'transcript').text = transcript_ref

    root.insert(0, entry)  # newest-first
    path.write_text(_pretty_xml(root), encoding='utf-8')


# ─── Main simulation: /handoff ───────────────────────────────────────────────

def simulate_handoff(
    scenario: dict,
    base_dir: Path,
    enable_dedup: bool = False,
) -> dict:
    """Execute /handoff SKILL.md steps 0-7 deterministically.

    Args:
        scenario: test scenario definition dict
        base_dir: isolated temp directory root
        enable_dedup: if True, mark superseded memory entries on conflict

    Returns:
        dict with paths to all written files + final session name
    """
    # Step 0: tag
    name_base = extract_tag(scenario)

    # Step 1: mkdir
    sessions_dir = base_dir / 'handoff' / 'data' / 'sessions'
    memory_dir = base_dir / 'handoff' / 'data' / 'memory'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    # Collision resolution
    name = resolve_name(name_base, sessions_dir)
    xml_path = sessions_dir / f'{name}.xml'
    transcript_path = sessions_dir / f'{name}.transcript.md'
    timestamp = iso_now()

    # Step 2: git state
    git = scenario.get('git', {})
    branch = git.get('branch', 'none')
    modified = git.get('modified', [])

    # Step 3: write XML
    root = ET.Element('handoff', version='1.0')

    session_el = ET.SubElement(root, 'session')
    ET.SubElement(session_el, 'name').text = name
    ET.SubElement(session_el, 'timestamp').text = timestamp
    ET.SubElement(session_el, 'platform').text = 'vscode-copilot'
    ET.SubElement(session_el, 'transcript_ref').text = f'sessions/{name}.transcript.md'

    state_el = ET.SubElement(root, 'state')
    ET.SubElement(state_el, 'goal').text = scenario.get('goal', 'Test goal')
    ET.SubElement(state_el, 'status').text = scenario.get('status', 'in_progress')
    ET.SubElement(state_el, 'branch').text = branch
    mf_el = ET.SubElement(state_el, 'modified_files')
    for f in modified:
        ET.SubElement(mf_el, 'file', status='unstaged').text = f
    ET.SubElement(state_el, 'todos')

    progress_el = ET.SubElement(root, 'progress')
    completed_el = ET.SubElement(progress_el, 'completed')
    for item in scenario.get('completed', []):
        ET.SubElement(completed_el, 'item').text = item
    remaining_el = ET.SubElement(progress_el, 'remaining')
    for item in scenario.get('remaining', []):
        if isinstance(item, dict):
            ET.SubElement(remaining_el, 'item', priority=item.get('priority', 'medium')).text = item.get('text', '')
        else:
            ET.SubElement(remaining_el, 'item', priority='medium').text = item
    ET.SubElement(progress_el, 'next_action').text = scenario.get('next_action', 'Continue from current state')

    ET.SubElement(root, 'decisions')
    ET.SubElement(root, 'blockers')
    ET.SubElement(root, 'gotchas')

    mem_el = ET.SubElement(root, 'memory_extractions')
    for fact in scenario.get('project_facts', []):
        ET.SubElement(mem_el, 'project_fact', confidence='high').text = fact
    for pref in scenario.get('user_preferences', []):
        ET.SubElement(mem_el, 'user_preference', confidence='medium').text = pref

    xml_path.write_text(_pretty_xml(root), encoding='utf-8')

    # Step 4: transcript
    transcript_path.write_text(
        f'# Session Transcript: {name}\n\n'
        f'> Captured at: {timestamp}\n'
        f'> Platform: VS Code Copilot\n\n'
        f'---\n\n'
        f'**User:** {scenario.get("goal", "Test")}\n\n'
        f'**Assistant:** Session simulated for testing purposes.\n',
        encoding='utf-8',
    )

    # Step 5: memory
    project_mem = memory_dir / 'project-memory.xml'
    user_mem = memory_dir / 'user-memory.xml'
    _update_memory(project_mem, 'project_memory', 'fact',
                   scenario.get('project_facts', []), name, timestamp, enable_dedup)
    _update_memory(user_mem, 'user_memory', 'preference',
                   scenario.get('user_preferences', []), name, timestamp, enable_dedup)

    # Step 6: index
    index_path = base_dir / 'handoff' / 'data' / 'index.xml'
    _update_index(index_path, name, timestamp,
                  scenario.get('status', 'in_progress'),
                  scenario.get('goal', 'Test'),
                  f'sessions/{name}.xml',
                  f'sessions/{name}.transcript.md')

    return {
        'name': name,
        'xml_path': xml_path,
        'transcript_path': transcript_path,
        'index_path': index_path,
        'project_mem_path': project_mem,
        'user_mem_path': user_mem,
        'timestamp': timestamp,
    }


# ─── Simulation: /resume ─────────────────────────────────────────────────────

def simulate_resume(resume_spec: dict, base_dir: Path) -> dict:
    """Execute /resume SKILL.md steps 0-5 deterministically.

    Returns dict with loaded session data, or {found: False, ...} on failure.
    """
    index_path = base_dir / 'handoff' / 'data' / 'index.xml'
    if not index_path.exists():
        return {'found': False, 'error': 'index.xml not found', 'available': []}

    tree = ET.parse(str(index_path))
    root = tree.getroot()
    sessions = root.findall('session')
    if not sessions:
        return {'found': False, 'error': 'No sessions in index', 'available': []}

    requested = resume_spec.get('tag', '').strip().lower()

    # Step 0: match priority — exact → prefix → substring (case-insensitive)
    match = None
    if not requested:
        match = sessions[0]  # most recent
    else:
        # exact
        for s in sessions:
            n = (s.findtext('name') or '').lower()
            if n == requested:
                match = s
                break
        # prefix
        if match is None:
            for s in sessions:
                n = (s.findtext('name') or '').lower()
                if n.startswith(requested):
                    match = s
                    break
        # substring
        if match is None:
            for s in sessions:
                n = (s.findtext('name') or '').lower()
                if requested in n:
                    match = s
                    break

    if match is None:
        available = [s.findtext('name') or '' for s in sessions]
        return {'found': False, 'error': f"No match for '{requested}'", 'available': available}

    session_name = match.findtext('name') or ''
    file_ref = match.findtext('file') or ''
    session_xml = base_dir / 'handoff' / 'data' / file_ref

    if not session_xml.exists():
        return {'found': False, 'error': f'Session file missing: {file_ref}', 'available': []}

    # Step 2: load XML
    st = ET.parse(str(session_xml)).getroot()
    goal = _get_text(st, 'state/goal')
    status = _get_text(st, 'state/status')
    branch = _get_text(st, 'state/branch')
    next_action = _get_text(st, 'progress/next_action')

    # Step 3: load memory
    mem_dir = base_dir / 'handoff' / 'data' / 'memory'
    project_facts, user_prefs = [], []
    pm = mem_dir / 'project-memory.xml'
    if pm.exists():
        for el in ET.parse(str(pm)).getroot().findall('fact'):
            if el.get('status') == 'active':
                project_facts.append(el.text or '')
    um = mem_dir / 'user-memory.xml'
    if um.exists():
        for el in ET.parse(str(um)).getroot().findall('preference'):
            if el.get('status') == 'active':
                user_prefs.append(el.text or '')

    return {
        'found': True,
        'name': session_name,
        'goal': goal,
        'status': status,
        'branch': branch,
        'next_action': next_action,
        'project_facts': project_facts,
        'user_prefs': user_prefs,
        'memory_loaded': True,
        'project_fact_count': len(project_facts),
        'user_pref_count': len(user_prefs),
    }
