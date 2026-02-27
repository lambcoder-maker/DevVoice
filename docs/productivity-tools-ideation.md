# Productivity Tools — Feature Ideation

Branch: `productivity-tools`
Date: 2026-02-27

---

## Overview

DevVoice currently does one thing well: record → transcribe → type at cursor.
This document captures ideas for turning it into a broader productivity layer
built on top of that foundation.

---

## 1. Voice Commands

Let users speak control words that trigger actions instead of typing text.

| Spoken phrase | Action |
|---|---|
| "new line" / "new paragraph" | Insert `\n` or `\n\n` |
| "comma", "period", "question mark" | Insert punctuation |
| "delete that" | Delete the last transcription |
| "select all" | Ctrl+A |
| "undo" | Ctrl+Z |
| "copy that" | Ctrl+C |
| "scratch that" | Erase the last typed block |

**Implementation notes:**
- Maintain a list of user-configurable command→action mappings in `config.py`
- Post-process transcription text: scan for known command tokens before typing
- Commands could be exact-match or fuzzy (e.g., tolerate "new line" vs "newline")
- UI: a "Commands" tab in settings where users can add/edit/remove mappings

---

## 2. Text Post-Processing Profiles

After transcription, apply a transformation pipeline before the text is typed.

### Built-in transforms
- **Auto-capitalise** — capitalise first word of each sentence
- **Auto-punctuate** — use a small local model or heuristic to add missing periods/commas
- **Smart quotes** — replace `"` with `"` / `"`
- **Trim filler words** — strip "um", "uh", "like", "you know" automatically

### Profile examples
| Profile | Transforms active |
|---|---|
| Raw | None — type exactly as transcribed |
| Clean prose | Auto-capitalise + Auto-punctuate + Trim fillers |
| Code | No capitalisation changes, preserve exact spacing |
| Email | Smart quotes + Auto-capitalise |

**Implementation notes:**
- Profiles stored in `settings.json` as ordered lists of transform IDs
- Selector in the control window or tray menu: "Profile: Clean prose ▾"
- Each transform is a pure function `(str) -> str` registered in a `transforms.py` module

---

## 3. Custom Word Dictionary / Substitutions

Map spoken words or phrases to specific output strings — great for technical jargon,
brand names, code symbols.

**Examples:**
| Say | Type |
|---|---|
| "dev voice" | `DevVoice` |
| "open paren" | `(` |
| "arrow" | `->` |
| "at sign" | `@` |
| "git commit" | `git commit -m ""` (cursor between quotes) |

**Implementation notes:**
- Dictionary stored in `settings.json` as a `{spoken: typed}` map
- Applied after transcription, before typing
- UI: dedicated "Dictionary" section in settings with add/edit/delete rows
- Support regex substitutions for power users

---

## 4. Undo Last Transcription

A dedicated hotkey (e.g., `Ctrl+Shift+Z`) that erases whatever was last typed.

**How it works:**
- After `keyboard_typer.type_text(text)`, store `len(text)` characters
- On undo hotkey: simulate `Backspace × len(last_text)`
- Show "Undone" in control window status

**Considerations:**
- Only works reliably in apps that accept backspace (not terminals, some IDEs)
- Could offer clipboard-restore as a fallback
- Stack depth: probably 1–3 levels is enough

---

## 5. Continuous / Hands-Free Mode

Instead of press-to-talk, the app automatically starts and stops recording based
on voice activity detection (VAD).

**Flow:**
1. User enables "Hands-free" from tray menu
2. App listens continuously on mic
3. When speech is detected, starts accumulating audio
4. When silence ≥ N seconds, auto-submits for transcription
5. Result is typed immediately

**Implementation notes:**
- Use `webrtcvad` or `silero-vad` (small, offline) for VAD
- Configurable silence threshold (0.5 s – 3 s)
- Configurable max utterance length to avoid runaway recording
- Visual indicator in control window: pulsing mic animation while listening

---

## 6. App-Aware Profiles (Context Switching)

Automatically switch transcription profile based on which window is in focus.

**Examples:**
| Focused app | Auto-profile |
|---|---|
| VS Code / any `.py` / `.js` window | Code |
| Outlook, Thunderbird | Email |
| Word, Notion, Obsidian | Clean prose |
| Everything else | Raw |

**Implementation notes:**
- Windows: `win32gui.GetForegroundWindow()` + `GetWindowText()`
- macOS: `AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()`
- Map process names / window title patterns to profiles in settings
- Override always available from control window

---

## 7. Session History & Export

Extend the existing transcription history window with export and search.

**Features:**
- Search / filter history by keyword
- Export to `.txt`, `.md`, or `.csv`
- Timestamps already captured — add word count per entry
- "Copy all" button to copy full session to clipboard
- Optional: auto-save session to a daily log file in a user-configured folder

---

## 8. Snippet Library (Voice-Activated Templates)

Pre-written text blocks triggered by a short spoken phrase.

**Example:**
- Say "insert greeting" → types `Hi [Name], Hope you're well. `
- Say "sign off" → types `Best regards,\nDeven`
- Say "todo" → types `TODO: `

**Implementation notes:**
- Snippets stored as `{trigger: content}` in settings
- Triggers are checked before the word dictionary
- Multi-line snippet content supported
- UI: "Snippets" tab in a settings dialog

---

## 9. Statistics & Usage Insights

A lightweight stats view (accessible from tray menu).

**Metrics:**
- Total words transcribed (all time / today)
- Average words per recording session
- Most-used words (word cloud or list)
- Time saved estimate (words ÷ average typing WPM)

**Implementation notes:**
- Append each transcription event to a local SQLite DB or JSONL file
- Stats window is a simple read-only dialog, no network needed

---

## 10. Wake-Word Activation (Stretch Goal)

Trigger recording by saying a wake word — no hotkey needed.

**Candidates:**
- `openWakeWord` (Apache 2, runs locally, 10–50 ms latency)
- Custom phrase trained in openWakeWord

**Flow:**
1. App listens in ultra-low-power mode for wake word
2. Wake word detected → start recording + play brief audio cue
3. Silence detected → auto-stop and transcribe

**Considerations:**
- Always-on mic raises privacy concerns — needs clear UI indicator
- CPU usage must be minimal (target < 2% on background thread)
- Should be opt-in, off by default

---

## Priority / Effort Matrix

| Feature | User value | Effort | Priority |
|---|---|---|---|
| Voice Commands | High | Medium | **P0** |
| Undo Last Transcription | High | Low | **P0** |
| Custom Word Dictionary | High | Low | **P0** |
| Text Post-Processing Profiles | High | Medium | **P1** |
| Continuous / Hands-Free Mode | High | High | **P1** |
| Snippet Library | Medium | Low | **P1** |
| Session Export | Medium | Low | **P2** |
| App-Aware Profiles | Medium | High | **P2** |
| Statistics | Low | Medium | **P3** |
| Wake-Word Activation | Medium | Very High | **P3** |

---

## Suggested First Sprint (P0 items)

1. **Undo last transcription** — one new hotkey, ~50 lines in `keyboard_typer.py` + `hotkey_manager.py`
2. **Custom word dictionary** — `dict` in `config.py`, single-pass replace in `app.py`, settings UI row
3. **Voice commands (basic set)** — hardcoded punctuation + line-break commands, configurable later

---

## 11. Voice-Activated TODO Assistant with Stakeholder Comms

> Idea: say "hey, create a task" → a TODO window opens, the task is pre-filled
> from whatever was just transcribed, you can set an ETA, attach stakeholders
> from Slack / Discord, ping them with a template message, and see their replies
> threaded directly inside the TODO item.

### Why this is compelling
- Zero context switching: you're already talking, so creating a task is one phrase away
- Stakeholder pinging from inside the TODO keeps all communication anchored to the task
- Thread-on-task means you never hunt through Slack history to find the status update
- Grouping contacts by platform (Slack workspace, Discord server) mirrors how people actually work

---

### Phase 1 — Local TODO Manager (no integrations)

**Voice trigger:**
- Detect "hey, create a task" (or configurable phrase) as a voice command
- Whatever was transcribed in the current session becomes the task title pre-fill
- TODO window opens immediately and focuses the title field

**TODO window UI (PyQt6):**
- Timeline view: tasks sorted by creation time, newest at top
- Each task card shows:
  - Title (editable inline)
  - Created timestamp
  - ETA date picker (optional)
  - Status chip: `Open` / `In Progress` / `Blocked` / `Done`
  - Stakeholders list (names + platform icons, added in Phase 2)
  - Thread accordion: expandable reply history (populated in Phase 2)
- Colour-coded urgency: overdue ETA → red, due today → orange, future → grey
- "New Task" button + voice command both open the same creation flow
- Tasks persist in a local SQLite DB (`~/.config/DevVoice/tasks.db` or `%APPDATA%\DevVoice\tasks.db`)

**Data model:**
```
Task
  id            UUID
  title         str
  created_at    datetime
  eta           date | None
  status        enum(open, in_progress, blocked, done)
  notes         str

Stakeholder
  id            UUID
  display_name  str
  platform      enum(slack, discord, email)
  platform_id   str   # Slack user ID, Discord user ID, email address

TaskStakeholder  (many-to-many)
  task_id
  stakeholder_id

Message          (the thread)
  id            UUID
  task_id
  stakeholder_id | None   # None = sent by user
  direction     enum(outbound, inbound)
  body          str
  sent_at       datetime
  platform_msg_id  str | None   # Slack ts, Discord message ID
```

**Implementation files:**
- `todos/db.py` — SQLite schema + CRUD helpers
- `todos/models.py` — dataclasses matching the schema above
- `ui/todo_window.py` — main TODO window (QMainWindow)
- `ui/todo_card.py` — single task card widget
- `ui/todo_create.py` — new-task creation dialog

---

### Phase 2 — Slack Integration

**Setup:**
- User creates a Slack app in their workspace, pastes Bot Token + App Token into DevVoice settings
- Scopes needed: `chat:write`, `im:write`, `channels:history`, `im:history`, `users:read`
- DevVoice opens a Slack Socket Mode connection in a background thread — no public URL needed

**Ping a stakeholder:**
1. User opens a task, clicks "Ping" next to a Slack stakeholder
2. DevVoice shows a pre-filled message template (editable):
   > Hi [Name], I wanted to check in on a task I'm tracking.
   > **Task:** {title}
   > **ETA:** {eta or "TBD"}
   > Could you give me a quick status update when you get a chance? Thanks!
3. User confirms → `chat.postMessage` to the stakeholder's DM
4. Message saved to the `Message` table as `outbound`

**Receive replies:**
- Socket Mode listener fires on `message` events in DMs
- Match incoming message to the original outbound `platform_msg_id`
- Save as `inbound` Message, show a notification badge on the task card
- Thread accordion expands to show the conversation in chronological order

**Implementation files:**
- `integrations/slack_client.py` — thin wrapper around `slack_sdk.WebClient` + `SocketModeClient`
- `integrations/slack_listener.py` — background QThread, emits `reply_received(task_id, body)` signal

---

### Phase 3 — Discord Integration

**Setup:**
- User creates a Discord bot, pastes Bot Token into settings
- Bot needs `Send Messages` + `Read Message History` + `Direct Messages` permissions
- DevVoice runs a `discord.py` client in a background thread (similar to Slack Socket Mode)

**Differences from Slack:**
- Pings go to Discord DMs via `user.send()`
- Reply matching via `message.reference` or author + channel correlation
- Contacts grouped under "Discord" in the stakeholder list with Discord server name shown

**Implementation files:**
- `integrations/discord_client.py`

---

### Phase 4 — Email (stretch)

- SMTP for outbound (already common in Python)
- IMAP idle for inbound reply detection
- Useful for external stakeholders who aren't on Slack/Discord

---

### Cross-platform Stakeholder Contact Book

The contact book lives in the same SQLite DB. UI is a simple list:

```
[Slack] Deven Patel      @deven  ·  Workspace: lambcoder
[Discord] Deven#1234     ·  Server: DevTeam
[Email] deven@example.com
```

- Add stakeholder from any platform at any time
- Same person can have multiple platform entries (linked by display name)
- When pinging, DevVoice picks the platform the task was originally assigned on,
  or lets the user choose if multiple platforms exist for that contact

---

### Honest complexity assessment

| Component | Effort | Risk |
|---|---|---|
| Local TODO UI + SQLite | Medium | Low |
| Voice trigger integration | Low | Low |
| Slack Socket Mode (send + receive) | Medium | Low — well-documented SDK |
| Discord bot (send + receive) | Medium | Low — `discord.py` is mature |
| Reply threading UI | Medium | Medium — need to handle edge cases (deleted msgs, edits) |
| Multi-platform contact book | Low | Low |
| Email IMAP idle | High | Medium — IMAP is finicky |

**Recommended build order:**
1. Phase 1 (local TODO) — ships a useful standalone feature immediately
2. Slack (most likely platform for the target user: developers)
3. Discord
4. Email only if there's demand

---

### Open questions
- Should the TODO window be a separate always-on-top panel (like ControlWindow) or a regular window accessed from the tray?
- Should tasks sync across devices? (Requires a backend — probably out of scope for v1)
- How do we handle Slack workspaces vs DM channels vs public channels for pinging?
- Should the voice command "hey, create a task" use the wake-word system (idea #10) or just the existing hotkey flow?
