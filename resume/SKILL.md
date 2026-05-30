---
name: resume
description: >-
  Resume a previously saved session. Loads context from a handoff XML file and
  renders a visual summary report so you can continue exactly where you left off.
  Use when the user says "resume", "continue session", "load session", or "resume [tag]".
argument-hint: "[tag-name]"
allowed-tools: Read Bash(git *)
disable-model-invocation: true
---

# /resume — Resume a Saved Session

You are an AI assistant running inside VS Code Copilot. Your job is to load a
previously saved session state and render a visual summary so work can continue
immediately. Follow each step **in order**.

---

## Step 0: Extract Tag Name

The user invoked this skill as `/resume [tag-name]`.

The **tag name** is the text the user typed after `/resume`. Extract it exactly.

**Cases:**

| User types | Action |
|------------|--------|
| `/resume auth-refactor` | Load session with exact tag `auth-refactor` |
| `/resume auth` | Partial match: find sessions whose tag contains "auth" |
| `/resume` (nothing after) | Load the **most recent** session (first entry in index.xml) |

**Match priority:** exact match → prefix match → substring match (case-insensitive).

---

## Step 1: Read Index

Read `.github/skills/handoff/data/index.xml`.

**If the file does not exist:**
```
No handoff sessions found. Run /handoff first to save a session.
```
Stop here.

**If a name was given but no match found**, list available sessions:
```
Session '<requested>' not found.

Available sessions:
• <name1> — <goal1> (<timestamp1>)
• <name2> — <goal2> (<timestamp2>)
...

Use /resume <name> to load one, or /resume for the latest.
```
Stop here.

---

## Step 2: Load Session XML

Read the matched session file:
**`.github/skills/handoff/data/sessions/<name>.xml`**

Parse all fields. Hold them in memory for rendering.

---

## Step 3: Load Memory (Conditional)

**Always load user preferences** (small, always relevant):
- Read `.github/skills/handoff/data/memory/user-memory.xml`
- Filter: only entries with `status="active"`
- Limit: max 20 entries

**Load project facts if the session involves project/code work:**
- Read `.github/skills/handoff/data/memory/project-memory.xml`
- Filter: only entries with `status="active"`
- Limit: max 30 entries
- Skip if file doesn't exist

Note how many entries you loaded from each file.

---

## Step 4: Render Visual Summary

Render the full resume report. Omit any section that has no data
(e.g., if no blockers, skip the BLOCKERS section entirely).

```
╔══════════════════════════════════════════════════════════════════╗
║ 📋 RESUMED: <name>                                               ║
╠══════════════════════════════════════════════════════════════════╣
║ GOAL    │ <state.goal>                                           ║
║ STATUS  │ <state.status>                                         ║
║ BRANCH  │ <state.branch>                                         ║
╠══════════════════════════════════════════════════════════════════╣
║ ▶ NEXT ACTION                                                    ║
║   <progress.next_action>                                         ║
╠══════════════════════════════════════════════════════════════════╣
║ REMAINING                                                        ║
║ [HIGH] <item>                                                    ║
║ [MED]  <item>                                                    ║
║ [LOW]  <item>                                                    ║
╠══════════════════════════════════════════════════════════════════╣
║ COMPLETED THIS SESSION                                           ║
║ ✓ <completed item>                                               ║
╠══════════════════════════════════════════════════════════════════╣
║ KEY DECISIONS                                                    ║
║ • <decision.what>                                                ║
║   └─ Why: <decision.why>                                         ║
╠══════════════════════════════════════════════════════════════════╣
║ ⚠️  GOTCHAS                                                       ║
║ • <gotcha>                                                       ║
╠══════════════════════════════════════════════════════════════════╣
║ 🚧 BLOCKERS                                                      ║
║ • [<type>] <blocker>                                             ║
╠══════════════════════════════════════════════════════════════════╣
║ 🧠 MEMORY LOADED                                                 ║
║ 📦 <N> project facts · 👤 <M> user preferences                  ║
╚══════════════════════════════════════════════════════════════════╝
```

**Rendering rules:**
- Truncate long text to fit the box width (~65 chars). Use `…` for truncation.
- If `<state.status>` is `blocked`, add a ⚠️ warning before the box:
  `⚠️  This session was saved as BLOCKED. Review blockers section before continuing.`
- If `<state.status>` is `completed`, add a note:
  `ℹ️  This session was marked COMPLETED. You may be re-opening finished work.`
- Keep the NEXT ACTION section even if everything else is empty — it is the most critical field.

---

## Step 5: Confirm Ready

After the box, output exactly:

```
Transcript available at: .github/skills/handoff/data/sessions/<name>.transcript.md
(Read it if you need to verify any detail from the original session.)

Ready to continue. What would you like to do?
```

Then wait for the user's instructions.

---

## Edge Cases

- **Malformed XML**: Report the error with the file path. Suggest the user run `/handoff` again.
- **Missing session file** (in index but file deleted): Report it and list other available sessions.
- **Memory files missing**: Silently skip. Note "0 project facts, 0 user preferences" in MEMORY LOADED.
- **Multiple partial matches**: Pick the newest (first in index.xml order). Note in output:
  `(Loaded most recent match. Other matches: <name2>, <name3>)`
