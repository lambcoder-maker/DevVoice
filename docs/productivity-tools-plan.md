# Productivity Tools — Phased Delivery Plan

Branch: `productivity-tools`
Last updated: 2026-02-27

Ticket sizes:
- **S** — a few hours, single file or simple addition
- **M** — half to one day, a few files
- **L** — two to three days, new subsystem or significant UI
- **XL** — four or more days, major feature with multiple moving parts

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Pre-Phase — Quick Wins (ship on existing hotkey + app flow)

These are self-contained, no new windows, no new data layer.

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| QW-1 | Undo last transcription | **S** | New hotkey `Ctrl+Shift+Z` backspaces the last typed block. Store char count in `keyboard_typer.py`, handle in `hotkey_manager.py`. Status shown in control window. |
| QW-2 | Custom word substitution | **S** | `word_map` dict in `config.py` (persisted to settings.json). Single-pass replace in `app.py` before typing. Settings row in a future settings dialog. |
| QW-3 | Voice commands — punctuation | **S** | Post-process transcription: "comma" → `,`, "period" / "full stop" → `.`, "question mark" → `?`, "exclamation mark" → `!`, "new line" → `\n`, "new paragraph" → `\n\n`. Table-driven, lives in `voice_commands.py`. |
| QW-4 | Voice commands — control words | **M** | "scratch that" → backspace entire last block (reuses QW-1 logic). "select all" → Ctrl+A. "copy that" → Ctrl+C. Configurable mapping stored in settings. |

---

## Phase 1 — Local TODO Manager

No network, no integrations. A standalone task manager triggered by voice.

### 1A — Data Layer

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P1-1 | SQLite schema + migrations | **S** | `todos/db.py`: create tables `tasks`, `stakeholders`, `task_stakeholders`, `messages` on first run. Pure Python, no ORM. Helper functions: `create_task`, `get_tasks`, `update_task`, `delete_task`. |
| P1-2 | Data models | **S** | `todos/models.py`: dataclasses `Task`, `Stakeholder`, `TaskStakeholder`, `Message`. Enums for `TaskStatus` and `Platform`. |

### 1B — Core TODO UI

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P1-3 | TODO window shell | **M** | `ui/todo_window.py`: QMainWindow with scrollable task list, "New Task" button at top. Accessible from tray menu "Open Tasks". Shows empty state message when no tasks exist. |
| P1-4 | Task card widget | **L** | `ui/todo_card.py`: QFrame card showing title (editable inline), created timestamp, status chip (Open / In Progress / Blocked / Done clickable cycle), ETA date picker, colour border (red=overdue, orange=due today, grey=future/none). Expand/collapse notes field. |
| P1-5 | New task dialog | **M** | `ui/todo_create.py`: small dialog with title field (pre-filled from last transcription if triggered by voice), optional ETA date picker, optional notes. "Create Task" confirms, "Cancel" discards. |
| P1-6 | Inline status transitions | **S** | Clicking the status chip on a card cycles through statuses and persists immediately to DB. Visual feedback (chip colour changes). |
| P1-7 | Task deletion | **S** | Delete button on card (with confirmation). Soft-delete or hard-delete (decide at impl time). |
| P1-8 | ETA colour coding | **S** | Card border / background tint: red if ETA < today, amber if ETA == today, default if future or unset. Recalculated on window open. |

### 1C — Voice Integration

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P1-9 | "Create a task" voice command | **M** | Detect configurable trigger phrase in transcription post-processing. Fire `create_task_requested(prefill_text)` signal in `app.py`. Opens `TodoCreateDialog` with title pre-filled. Does NOT type the trigger phrase at cursor. |
| P1-10 | Tray menu entry | **S** | Add "Open Tasks" to system tray menu above "Change Model…". Opens `TodoWindow` (create if not exists, show/raise if already open). |

---

## Phase 2 — Slack Integration

Requires user to create a Slack app and provide tokens. No public URL needed
(Socket Mode).

### 2A — Settings & Auth

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P2-1 | Slack settings UI | **M** | New "Integrations" tab in a settings dialog (or dedicated dialog from tray). Fields: Bot Token, App Token. "Test Connection" button calls `auth.test` and shows workspace name on success. Tokens persisted (encrypted with `keyring` or plaintext in settings.json with a warning). |
| P2-2 | `integrations/slack_client.py` | **M** | Thin wrapper: `SlackClient(bot_token, app_token)`. Methods: `send_dm(user_id, text) → ts`, `get_user(user_id) → name+avatar`, `search_users(query) → list`. Uses `slack_sdk.WebClient`. |

### 2B — Contacts

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P2-3 | Stakeholder contact book UI | **M** | `ui/contacts_window.py` or panel inside TODO window. Lists all saved stakeholders grouped by platform. Add / remove buttons. Slack stakeholders show workspace name. |
| P2-4 | Add Slack stakeholder | **M** | Search box hits Slack `users.list`, shows results with avatar + display name. Selecting one saves to `stakeholders` table. |
| P2-5 | Attach stakeholder to task | **S** | "Add stakeholder" button on task card opens contact picker. Saves to `task_stakeholders`. Shows attached names on card. |

### 2C — Pinging

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P2-6 | Ping dialog | **M** | Clicking "Ping" next to a stakeholder on a task card opens a dialog with pre-filled template (editable): task title, ETA, polite status-request wording. "Send" / "Cancel". |
| P2-7 | Send DM + persist | **M** | On confirm: `SlackClient.send_dm(user_id, text)`. Save as `Message(direction=outbound, platform_msg_id=ts)` in DB. Show "Sent" confirmation on card. |

### 2D — Reply Threading

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P2-8 | Slack Socket Mode listener | **L** | `integrations/slack_listener.py`: `SlackListenerThread(QThread)`. Opens Socket Mode connection, listens for `message` events in DMs. Matches `channel` + `user` to known outbound messages. Emits `reply_received(task_id, sender, body, ts)` signal. Handles reconnect on disconnect. |
| P2-9 | Thread accordion UI | **L** | Expandable section at bottom of task card. Shows outbound + inbound messages in chronological order with sender name, timestamp, and message body. Badge count on collapsed header ("3 replies"). Notification badge on task card when new inbound message arrives. |
| P2-10 | New reply notification | **S** | When `reply_received` fires: flash task card border, show tray notification "Reply from [Name] on task [Title]". |

---

## Phase 3 — Discord Integration

Same architecture as Slack; build on the pattern established in Phase 2.

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P3-1 | Discord settings UI | **S** | Bot Token field in Integrations settings. Test connection shows bot username. |
| P3-2 | `integrations/discord_client.py` | **M** | `DiscordClient(bot_token)`. Methods: `send_dm(user_id, text) → message_id`, `search_members(query) → list`. Uses `discord.py` (runs its event loop in a thread). |
| P3-3 | Add Discord stakeholder | **M** | Search across known servers the bot is in. Save with `platform=discord`. |
| P3-4 | Send Discord DM + persist | **S** | Reuses ping dialog from P2-6. Routes through `DiscordClient.send_dm`. Saves outbound message. |
| P3-5 | Discord gateway listener | **M** | `integrations/discord_listener.py`: `DiscordListenerThread(QThread)`. `on_message` handler matches DMs back to outbound messages. Emits same `reply_received` signal as Slack listener. Reuses thread accordion UI from P2-9. |

---

## Phase 4 — Email (stretch, build only if there is demand)

| # | Ticket | Size | Deliverable |
|---|---|---|---|
| P4-1 | Email settings UI | **S** | SMTP host/port/user/pass, IMAP host/port fields. Test send button. |
| P4-2 | Send email via SMTP | **M** | `integrations/email_client.py`. Compose with task title + ETA in subject/body. Saves `Message(direction=outbound)`. |
| P4-3 | IMAP idle listener | **L** | Background thread polls IMAP for replies to sent messages (match by `In-Reply-To` header). Emits `reply_received`. Saves inbound. |

---

## Dependency graph

```
QW-1 ──────────────────────────────────► QW-4
QW-2 ──┐
QW-3 ──┤
       └── (standalone, no deps)

P1-1 ──► P1-2 ──► P1-3 ──► P1-4 ──► P1-5
                             └──► P1-6
                             └──► P1-7
                             └──► P1-8
P1-5 ──► P1-9 (voice trigger opens create dialog)
P1-3 ──► P1-10 (tray entry opens window)

P2-1 ──► P2-2 ──► P2-4 ──► P2-5 ──► P2-6 ──► P2-7
P2-3 ──► P2-4
P2-7 ──► P2-8 ──► P2-9 ──► P2-10

P2-9 ◄─── P3-5  (Discord reuses thread accordion)
P2-6 ◄─── P3-4  (Discord reuses ping dialog)
```

---

## Recommended sprint order

### Sprint 0 — Ship quick wins (all S/M, isolated)
`QW-1` → `QW-2` → `QW-3` → `QW-4`

### Sprint 1 — TODO data + basic window
`P1-1` → `P1-2` → `P1-3` → `P1-10`

### Sprint 2 — Task cards + voice trigger
`P1-4` → `P1-5` → `P1-6` → `P1-7` → `P1-8` → `P1-9`

### Sprint 3 — Slack auth + contacts
`P2-1` → `P2-2` → `P2-3` → `P2-4` → `P2-5`

### Sprint 4 — Slack pinging
`P2-6` → `P2-7`

### Sprint 5 — Slack replies + threading UI
`P2-8` → `P2-9` → `P2-10`

### Sprint 6 — Discord
`P3-1` → `P3-2` → `P3-3` → `P3-4` → `P3-5`

### Sprint 7 (stretch) — Email
`P4-1` → `P4-2` → `P4-3`

---

## Total ticket count by size

| Size | Count | Tickets |
|---|---|---|
| S | 12 | QW-1, QW-2, QW-3, P1-6, P1-7, P1-8, P1-10, P2-5, P2-10, P3-1, P3-4, P4-1 |
| M | 14 | QW-4, P1-3, P1-5, P1-9, P2-1, P2-2, P2-3, P2-4, P2-6, P2-7, P3-2, P3-3, P3-5, P4-2 |
| L | 5 | P1-4, P2-8, P2-9, P3-5*, P4-3 |
| XL | 0 | — broken into L tickets above |
