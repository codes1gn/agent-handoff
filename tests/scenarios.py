"""Test scenario definitions for agent-handoff skill verification.

Each scenario exercises one or more SKILL.md behaviors.
All scenarios are designed to produce 100% passing checks.

Scenario types:
  'handoff'   (default) single handoff + optional resume check
  'collision' two handoffs same tag → second gets -2 suffix
  'dedup'     two handoffs same facts → first entries superseded
"""

SCENARIOS = [
    # ── 01: Basic handoff with explicit tag ──────────────────────────────────
    {
        'id': '01-basic-handoff',
        'description': 'Explicit tag → slug, XML schema, index, transcript all verified',
        'tag': 'auth-refactor',
        'goal': 'Refactor authentication module to use JWT instead of sessions',
        'status': 'in_progress',
        'git': {'branch': 'feature/jwt-auth', 'modified': ['src/auth/jwt.ts', 'src/auth/session.ts']},
        'next_action': 'Open src/auth/jwt.ts line 47 and implement validateToken()',
        'completed': ['Analyzed existing session-based auth code', 'Designed JWT schema'],
        'remaining': [{'text': 'Implement validateToken()', 'priority': 'high'},
                      {'text': 'Write unit tests', 'priority': 'medium'}],
        'project_facts': ['Auth module is in src/auth/', 'Uses TypeScript strict mode'],
        'user_preferences': ['Prefers early returns over deeply nested if-else'],
    },

    # ── 02: Auto-tag generation (no tag given) ───────────────────────────────
    {
        'id': '02-auto-tag',
        'description': 'No tag → auto-generated slug from goal + date',
        'tag': '',
        'goal': 'Build a caching layer for the API endpoints',
        'status': 'in_progress',
        'git': {'branch': 'main', 'modified': []},
        'next_action': 'Create src/middleware/cache.ts and implement RedisCache class',
        'project_facts': ['Redis available at localhost:6379'],
        'user_preferences': [],
    },

    # ── 03: Tag with spaces → slugified ─────────────────────────────────────
    {
        'id': '03-tag-spaces',
        'description': 'Tag with spaces/mixed case → slugified to my-feature-work',
        'tag': 'My Feature Work',
        'goal': 'Implement new payment flow with Stripe',
        'status': 'in_progress',
        'git': {'branch': 'feature/payment', 'modified': ['src/payment/stripe.ts']},
        'next_action': 'Integrate Stripe webhook handlers in src/payment/webhooks.ts',
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 04: Tag with underscores → hyphens ──────────────────────────────────
    {
        'id': '04-tag-underscores',
        'description': 'Tag with underscores → slugified (underscores→hyphens)',
        'tag': 'my_feature_v2',
        'goal': 'Second iteration of feature X',
        'status': 'in_progress',
        'git': {'branch': 'feature/x-v2', 'modified': []},
        'next_action': 'Continue from src/features/x.ts line 120',
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 05: Completed session ────────────────────────────────────────────────
    {
        'id': '05-status-completed',
        'description': 'status=completed — verified in XML and index',
        'tag': 'refactor-done',
        'goal': 'Complete the auth refactor and merge to main',
        'status': 'completed',
        'git': {'branch': 'feature/jwt-auth', 'modified': []},
        'next_action': 'Merge PR #47 to main and close the issue',
        'completed': ['Implemented JWT', 'Added tests', 'Updated docs', 'Code review passed'],
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 06: Blocked session ──────────────────────────────────────────────────
    {
        'id': '06-status-blocked',
        'description': 'status=blocked — verified in XML and index',
        'tag': 'waiting-for-api-key',
        'goal': 'Integrate with third-party payment API',
        'status': 'blocked',
        'git': {'branch': 'feature/payment-api', 'modified': []},
        'next_action': 'Resume after receiving API key from vendor (ticket #92)',
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 07: No git repo ──────────────────────────────────────────────────────
    {
        'id': '07-no-git',
        'description': 'No git repo → branch=none, no modified files',
        'tag': 'no-git-session',
        'goal': 'Work in a scratch directory without version control',
        'status': 'in_progress',
        'git': {'branch': 'none', 'modified': []},
        'next_action': 'Initialize git or continue without version control',
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 08: Rich memory extraction ───────────────────────────────────────────
    {
        'id': '08-multi-memory',
        'description': 'Multiple project facts + user preferences extracted and format-verified',
        'tag': 'multi-memory-session',
        'goal': 'Session with rich memory extraction for format verification',
        'status': 'in_progress',
        'git': {'branch': 'main', 'modified': []},
        'next_action': 'Review all loaded memory entries on next /resume',
        'project_facts': [
            'Uses pnpm not npm for package management',
            'All API routes live in src/api/ directory',
            'Database is PostgreSQL with Drizzle ORM',
            'Tests use Vitest not Jest',
        ],
        'user_preferences': [
            'Prefers small focused commits over large ones',
            'Never commits directly to main branch',
            'Prefers TypeScript strict mode always on',
        ],
    },

    # ── 09: Name collision → -2 suffix ──────────────────────────────────────
    {
        'id': '09-collision',
        'type': 'collision',
        'description': 'Same tag used twice → second handoff gets -2 suffix',
        'tag': 'collision-test',
        'goal': 'Verify collision resolution appends -2 to duplicate tag',
        'status': 'in_progress',
        'git': {'branch': 'main', 'modified': []},
        'next_action': 'Verify both session files exist in data/sessions/',
        'project_facts': [],
        'user_preferences': [],
    },

    # ── 10: Memory deduplication ─────────────────────────────────────────────
    {
        'id': '10-memory-dedup',
        'type': 'dedup',
        'description': 'Same fact in two sequential handoffs → first entry marked superseded',
        'tag': 'dedup-session',
        'goal': 'Verify memory deduplication marks prior entries as superseded',
        'status': 'in_progress',
        'git': {'branch': 'main', 'modified': []},
        'next_action': 'Check project-memory.xml for superseded + active entries',
        'project_facts': ['Uses pnpm not npm', 'TypeScript 5.0+ required'],
        'user_preferences': ['Prefers functional style over OOP'],
    },

    # ── 11: Resume exact match ───────────────────────────────────────────────
    {
        'id': '11-resume-exact',
        'description': 'Resume with exact tag → loads correct session',
        'tag': 'my-feature',
        'goal': 'Implement feature X from spec document',
        'status': 'in_progress',
        'git': {'branch': 'feature/x', 'modified': []},
        'next_action': 'Continue feature X from src/features/x.ts line 120',
        'project_facts': ['Feature X spec is in docs/feature-x.md'],
        'user_preferences': [],
        'resume': {'tag': 'my-feature', 'expected_name': 'my-feature'},
    },

    # ── 12: Resume partial match ─────────────────────────────────────────────
    {
        'id': '12-resume-partial',
        'description': 'Resume with partial tag → substring match returns correct session',
        'tag': 'auth-refactor-v2',
        'goal': 'Second pass auth refactor targeting edge cases',
        'status': 'in_progress',
        'git': {'branch': 'feature/auth-v2', 'modified': []},
        'next_action': 'Continue auth refactor from edge case analysis in auth-edge-cases.md',
        'project_facts': [],
        'user_preferences': [],
        'resume': {'tag': 'auth', 'expected_name': 'auth-refactor-v2'},
    },

    # ── 13: Resume no match ──────────────────────────────────────────────────
    {
        'id': '13-resume-no-match',
        'description': 'Resume with unknown tag → not-found response with available list',
        'tag': 'existing-session-for-no-match-test',
        'goal': 'Session created specifically to test no-match behavior',
        'status': 'in_progress',
        'git': {'branch': 'main', 'modified': []},
        'next_action': 'This session exists only to populate the index',
        'project_facts': [],
        'user_preferences': [],
        'resume': {
            'tag': 'nonexistent-xyz-abc-999',
            'expected_name': None,
            'expect_not_found': True,
        },
    },
]
