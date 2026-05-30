---
name: handoff
description: >-
  Save the current session state for later resumption. Captures session progress,
  decisions, blockers, next actions, and memory extractions into a structured XML
  file. Use when the user says "handoff", "save session", "wrap up", or "end session".
argument-hint: "[tag-name]"
allowed-tools: Read Write Bash(git *)
disable-model-invocation: true
---

# /handoff — Save Current Session State

You are an AI assistant running inside VS Code Copilot. Your job is to save the
current chat session state to a portable, structured XML file so it can be resumed
later. Follow each step **in order**. Do not skip steps.

---

## Step 0: Extract Tag Name

The user invoked this skill as `/handoff [tag-name]`.

The **tag name** is the text the user typed after `/handoff`. It is available in the
user's message as the word(s) following the `/handoff` command. Extract it exactly.

**Cases:**

| User types | Tag name |
|------------|----------|
| `/handoff auth-refactor` | `auth-refactor` |
| `/handoff my project` | `my-project` (slugify: lowercase, spaces→hyphens) |
| `/handoff` (nothing after) | Auto-generate from session topic: `<topic>-YYYY-MM-DD` |

**Slugification rules:** lowercase only, spaces and underscores → hyphens, strip
non-alphanumeric except hyphens. Pattern must match `[a-z0-9][a-z0-9-]*[a-z0-9]`.

**If no tag was given:** generate a slug from the main topic of this conversation,
appended with today's date in `YYYY-MM-DD` format (UTC+8 timezone).

---

## Step 1: Create Directory Structure

Run in terminal:

```bash
mkdir -p .github/skills/handoff/data/sessions
mkdir -p .github/skills/handoff/data/memory
```

---

## Step 2: Capture Git State

Run these commands and remember the output for Step 3:

```bash
git branch --show-current 2>/dev/null || echo "no-git"
git status --short 2>/dev/null || echo "no-git"
git diff --staged --name-only 2>/dev/null || echo "no-git"
git log --oneline -5 2>/dev/null || echo "no-git"
```

---

## Step 3: Write Handoff XML

Write a completed XML file to:
**`.github/skills/handoff/data/sessions/<name>.xml`**

Fill in ALL fields marked REQUIRED. For OPTIONAL fields, either fill them or remove
the element entirely (no empty tags). Use your full context window to extract content.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
  Handoff file v1.0. Written by /handoff skill.
  Resume this session with: /resume <name>
-->
<handoff version="1.0">

  <!-- ═══ SESSION METADATA ════════════════════════════════════════ -->
  <session>
    <name>REQUIRED: replace with session name slug</name>
    <timestamp>REQUIRED: ISO-8601 with offset, e.g., 2026-05-30T21:00:00+08:00</timestamp>
    <platform>vscode-copilot</platform>
    <transcript_ref>sessions/REPLACE-NAME.transcript.md</transcript_ref>
  </session>

  <!-- ═══ CURRENT STATE ═══════════════════════════════════════════ -->
  <state>
    <goal>REQUIRED: Primary goal of this session in one sentence</goal>
    <status>REQUIRED: in_progress | completed | blocked</status>
    <branch>REQUIRED: current git branch name, or "none" if no git repo</branch>

    <modified_files>
      <!-- One <file> per modified/new/deleted file from git status output -->
      <!-- status attribute: staged | unstaged | new | deleted -->
      <!-- Example: <file status="staged">src/auth/jwt.ts</file> -->
    </modified_files>

    <todos>
      <!-- One <todo> per active task in the agent's todo list -->
      <!-- status attribute: pending | in_progress | done | blocked -->
      <!-- Example: <todo status="pending">Write unit tests for JWT module</todo> -->
    </todos>
  </state>

  <!-- ═══ PROGRESS ════════════════════════════════════════════════ -->
  <progress>
    <completed>
      <!-- One <item> per thing completed and verified this session -->
    </completed>

    <remaining>
      <!-- One <item priority="high|medium|low"> per remaining task, ordered by priority -->
    </remaining>

    <!--
      REQUIRED. The single most important first step for a fresh agent picking this up.
      Must be specific and actionable. REJECT vague phrases like "continue the work".
      Good example: "Open src/auth/jwt.ts line 47 and implement validateToken()"
    -->
    <next_action>REQUIRED: exact first step</next_action>
  </progress>

  <!-- ═══ KEY DECISIONS ════════════════════════════════════════════ -->
  <!-- Architectural or design decisions made this session that affect future work -->
  <decisions>
    <!-- Example:
    <decision>
      <what>Use RS256 instead of HS256 for JWT signing</what>
      <why>Multi-service verification needed; RS256 allows public key distribution</why>
      <alternatives_rejected>HS256 rejected — shared secret doesn't scale to microservices</alternatives_rejected>
    </decision>
    -->
  </decisions>

  <!-- ═══ BLOCKERS ═════════════════════════════════════════════════ -->
  <!-- Things that blocked progress or remain unresolved -->
  <blockers>
    <!-- type attribute: technical | external | design | unclear -->
    <!-- Example: <blocker type="external">Waiting for API key from vendor X</blocker> -->
  </blockers>

  <!-- ═══ GOTCHAS ══════════════════════════════════════════════════ -->
  <!-- Non-obvious behaviors, side effects, or traps a fresh agent MUST know -->
  <gotchas>
    <!-- Example: <gotcha>decodeToken() mutates the input object — side effect at jwt.ts:23</gotcha> -->
  </gotchas>

  <!-- ═══ MEMORY EXTRACTIONS ══════════════════════════════════════ -->
  <!--
    Stable facts to persist across sessions.
    - project_fact: facts about THIS codebase (tech stack, conventions, architecture)
    - user_preference: patterns about HOW THIS USER prefers to work
    - confidence: high (confirmed multiple times) | medium (probable) | low (tentative)
    - Only extract stable, reusable facts. NOT session-specific state.
  -->
  <memory_extractions>
    <!-- Examples:
    <project_fact confidence="high">Uses pnpm not npm for package management</project_fact>
    <project_fact confidence="high">All API routes are in src/api/ directory</project_fact>
    <user_preference confidence="medium">Prefers early returns over deeply nested if-else</user_preference>
    -->
  </memory_extractions>

</handoff>
```

---

## Step 4: Write Transcript

Write the conversation transcript to:
**`.github/skills/handoff/data/sessions/<name>.transcript.md`**

Template:

```markdown
# Session Transcript: <name>

> Captured at: <timestamp>
> Platform: VS Code Copilot
> Note: This transcript captures context visible at /handoff time. VS Code Copilot
> summarizes early context automatically — if early conversation is absent, it was
> already summarized by the platform before this capture.

---

<Write the full conversation here. Include:
- User messages (prefix with "**User:**")
- Your responses (prefix with "**Assistant:**")
- Write as much as you can see in your current context window
- If the session started with a summary (indicating prior context was compacted),
  start with: "<!-- NOTE: Session began with a context summary. Full early history not available. -->"
>
```

---

## Step 5: Extract Memory

Read `<memory_extractions>` from the XML you just wrote.

### For each `<project_fact>`:

1. Read `.github/skills/handoff/data/memory/project-memory.xml` (create if missing):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project_memory version="1.0">
  <!-- project_fact entries go here, newest first -->
</project_memory>
```

2. Check if a fact on the same topic already has `status="active"`:
   - If YES: mark it `status="superseded"` and add `superseded_by="<session-name>"` attribute
   - Then append new entry as `status="active"`
   - If NO conflict: just append new entry

3. New entry format:
```xml
<fact confidence="FILL" status="active" session="<name>" timestamp="<ISO-8601>">
  FILL: the fact text
</fact>
```

### For each `<user_preference>`:

Same logic, but use `.github/skills/handoff/data/memory/user-memory.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<user_memory version="1.0">
  <!-- user_preference entries go here, newest first -->
</user_memory>
```

Entry format:
```xml
<preference confidence="FILL" status="active" session="<name>" timestamp="<ISO-8601>">
  FILL: the preference text
</preference>
```

---

## Step 6: Update Index

Read `.github/skills/handoff/data/index.xml` (create if missing):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<index version="1.0" updated="FILL-ISO-8601">
</index>
```

**Prepend** (insert at top, inside `<index>`) a new entry — newest first:

```xml
<session>
  <name>FILL: session name slug</name>
  <timestamp>FILL: ISO-8601</timestamp>
  <platform>vscode-copilot</platform>
  <status>FILL: mirrors state.status from the handoff XML</status>
  <goal>FILL: goal shortened to max 80 characters</goal>
  <file>sessions/FILL-NAME.xml</file>
  <transcript>sessions/FILL-NAME.transcript.md</transcript>
</session>
```

Update the `updated` attribute on `<index>` to the current timestamp.

---

## Step 7: Show Confirmation

Render this confirmation box (fill in the actual values):

```
╔══════════════════════════════════════════════════════════════════╗
║ ✅ HANDOFF SAVED: <name>                                         ║
╠══════════════════════════════════════════════════════════════════╣
║ Files written:                                                   ║
║  • .github/skills/handoff/data/sessions/<name>.xml               ║
║  • .github/skills/handoff/data/sessions/<name>.transcript.md     ║
║  • .github/skills/handoff/data/index.xml (updated)               ║
║ Memory: <N> project facts, <M> user preferences extracted        ║
╚══════════════════════════════════════════════════════════════════╝
Resume this session later with: /resume <name>
```

---

## Edge Cases

- **No git repo**: Set `<branch>none</branch>`, leave `<modified_files>` and todos empty.
- **Name collision**: If `<name>.xml` already exists, append `-2`, `-3`, etc. to the name.
- **No memory extractions**: Skip Step 5. Note "0 project facts, 0 user preferences" in confirmation.
- **Large transcript**: If context window is extremely large, write a truncated transcript
  and note `<!-- Transcript truncated at <N> characters to avoid file size limits -->`.
