# Decky Bottom Navigation Design

## Status

Approved on 2026-08-09. Implement frontend first; backend changes are explicitly out of scope for this pass.

## Goal

Replace the current view-dropdown UI with a minimal, adaptive bottom-navigation Decky panel inspired by the approved B mockup.

## Product Direction

Codex Remote should feel like a small Steam Deck control surface, not a desktop web app compressed into the Quick Access panel. The main screen must be useful immediately while gaming: see the current Codex state, approve or deny requests, read the latest live feed, and send a short reply without digging through settings.

## Navigation Model

Use five bottom navigation destinations:

- `Remote`
- `Chats`
- `Auth`
- `Setup`
- `Log`

The bottom nav stays visible at the bottom of the plugin panel. Each item is a compact focusable control with stable dimensions and short text. The active item has a subtle Decky-style selected state. The nav must not use oversized custom tabs or a full-width dropdown.

## Remote View

Remote is the default view. It contains:

- Header row with plugin name, endpoint, and status pill.
- Current chat summary with a compact `Chats` action.
- Current task summary, clamped to avoid pushing controls off-screen.
- Inline approval block when an approval is pending, with `Approve` and `Deny`.
- Live feed/transcript with compact structured cards for Codex, user, command, tool, file, approval, and error items.
- Quick actions: `Continue`, `Explain`, `Retry`, `Summary`.
- Compact message input.
- Primary `Send` and secondary `Pause`.

Remote prioritizes action visibility over long transcript height. Transcript remains auto-scrolled to latest messages.

## Chats View

Chats contains:

- Search input at the top.
- Recent chat list with user-facing titles, active state, loaded state, and status dot.
- Selecting a chat switches back to Remote.

Raw IDs should not be used as primary titles unless no better metadata exists.

## Auth View

Auth contains:

- App Server account state.
- `Check` action.
- `Login` action for ChatGPT device-code flow.
- Device-code URL and user code when login is active.

The plugin must not ask for OpenAI password, ChatGPT session cookie, or API key.

## Setup View

Setup contains:

- LAN `Scan`.
- `Link`, `Check`, and `Disconnect`.
- Host, port, token, and live updates.
- Clear token-required notice when host/port are set but token is missing.

The capability token stays masked in UI fields.

## Log View

Log contains recent connection, account, action, and App Server messages. It is diagnostic only and should not compete with Remote.

## Visual Rules

- Use Decky-native components where practical: `PanelSection`, `PanelSectionRow`, `TextField`, `ToggleField`, and `Focusable`.
- Use compact custom controls only where native Decky controls are too tall for the Quick Access panel.
- Avoid nested cards and decorative panels.
- Keep text sizes small and stable.
- Keep button spacing at least 6px.
- Do not use large bright buttons.
- Do not use negative letter spacing.
- Every fixed-format element should have stable dimensions.
- The UI must fit Steam Deck Quick Access width without text overlap.

## Out Of Scope

- Backend protocol changes.
- New App Server RPC methods.
- Official OpenAI relay integration.
- Reworking LAN scan logic.
- Changing persisted settings shape unless required by frontend-only view state.

## Acceptance Criteria

- The frontend builds with `pnpm run build`.
- The package builds with `pnpm run package`.
- The plugin installs on Steam Deck and Decky Loader remains active.
- Fresh Decky logs contain no Codex Remote frontend/backend errors.
- Remote view shows the bottom nav and keeps primary controls visible in the Quick Access panel.
- Chats/Auth/Setup/Log are reachable from bottom nav with controller focus.
