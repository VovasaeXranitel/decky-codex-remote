# Changelog

## 0.1.15 - 2026-05-31

Fix Steam Deck transcript scrolling.

- Wrap the transcript in Decky's native `ScrollPanel`/`ScrollPanelGroup`.
- Add explicit `Up` and `Down` controls for reliable gamepad scrolling.
- Keep wheel/touch scrolling available inside the focused transcript area.

## 0.1.14 - 2026-05-31

Add a scrollable professional transcript.

- Replace the single-line activity view with a scrollable transcript.
- Add structured cards for user messages, Codex messages, reasoning, commands, tools, file changes, approvals, errors, and system events.
- Keep streaming Codex deltas as a live transcript item instead of spamming separate log rows.
- Render command/tool/file payloads in compact monospace blocks with statuses.

## 0.1.13 - 2026-05-31

Add chat selection and fix thread titles.

- Add a Steam Deck chat picker for switching Codex threads.
- Use Codex thread `name` and `preview` instead of showing raw thread ids.
- Improve button spacing in compact Decky grids.
- Refocus the panel around Codex mobile's chat, task, activity, approval, and reply flow.

## 0.1.12 - 2026-05-31

Tighten the real Steam Deck panel layout.

- Move Setup and Sync into compact header actions.
- Shorten setup actions to Scan, Link, ChatGPT, and More.
- Reduce activity height so the composer and action buttons stay reachable.
- Keep the layout focused on Codex mobile's status, task, activity, and reply flow.

## 0.1.11 - 2026-05-31

Make Setup compact by default.

- Keep the Setup drawer focused on scan, connect, ChatGPT, and advanced settings.
- Move Host, Port, Token, Check, Account, Disconnect, and live updates into Advanced.
- Reduce the default Setup height so work and composer stay visible.

## 0.1.10 - 2026-05-31

Tighten the live Steam Deck panel controls.

- Force Decky focusable buttons to compact 32px rows.
- Reduce the message input height while keeping the dark focused styling.
- Recheck the layout through the live QuickAccess CEF screenshot path.

## 0.1.9 - 2026-05-31

Fix the live Decky message input styling.

- Inspect the real QuickAccess DOM for Decky `TextField`.
- Override Decky `DialogInput` focus styles inside the Codex composer.
- Keep the input dark when focused on Steam Deck.

## 0.1.8 - 2026-05-31

Fix real Steam Deck panel layout.

- Debug the live QuickAccess CEF tab on the Steam Deck.
- Remove two-column Decky button grids that overflow the panel row width.
- Clamp activity messages so the composer stays reachable.
- Reduce button height and force button widths to fit the Decky row.

## 0.1.7 - 2026-05-31

Move the panel toward the Codex mobile control-surface model.

- Remove the local attachment photo folder from the workspace.
- Rework the Decky panel around current work, activity, approvals, and the composer.
- Collapse connection and account controls into a secondary Setup area.
- Add clearer button hierarchy for primary, quiet, and deny actions.
- Refresh the local Steam Deck preview to match the new structure.

## 0.1.6 - 2026-05-31

Fix Decky callable runtime on Steam Deck.

- Declare Decky `api_version: 1` in the plugin manifest.
- Unblock index-based callable arguments used by `@decky/api`.
- Restore settings, scan, connect, disconnect, refresh, and action button calls.

## 0.1.5 - 2026-05-31

Fix LAN discovery and Steam Deck panel usability.

- Remove localhost discovery candidates from the production LAN scanner.
- Scan SteamOS IPv4 LAN prefixes even when a saved host is present.
- Keep the saved host as a normal prioritized candidate, not a scan shortcut.
- Replace broken localized labels with stable ASCII UI text.
- Add gamepad OK handling to the custom dark Decky buttons.
- Refresh the local Steam Deck panel preview.

## 0.1.4 - 2026-05-31

Fix LAN scan feedback.

- Check the configured host first before scanning the subnet.
- Return a fast successful scan result when the current host is reachable.
- Show the actual frontend scan error instead of a generic failure message.

## 0.1.3 - 2026-05-31

Fix Steam Deck panel readability.

- Replace bright Steam `Button` controls with dark custom `Focusable` controls.
- Keep gamepad focus behavior without white button backgrounds.
- Improve LAN scanner address discovery on SteamOS using `ip` route/address fallbacks.

## 0.1.2 - 2026-05-31

Improve Steam Deck usability.

- Replace the custom settings icon button with a native Decky `ButtonItem`.
- Remove nested grid button groups that were unreliable with Steam Deck focus/navigation.
- Show approval and pause actions only when they can actually be used.
- Save current connection settings before connection, scan, account, and login actions.
- Shorten and localize the panel controls for the Decky side panel.

## 0.1.1 - 2026-05-31

Fix Decky runtime startup on Steam Deck.

- Ensure the Python backend can import bundled plugin modules from its own directory.
- Store the Codex App Server client as Decky-compatible plugin class state.

## 0.1.0 - 2026-05-31

Initial alpha release.

- Decky Loader side-panel UI inspired by Codex App.
- Settings for Codex App Server host, port, token, and refresh behavior.
- LAN scan for Codex App Server discovery.
- ChatGPT device-code login flow through Codex App Server.
- Direct WebSocket JSON-RPC client implemented in the Python backend.
- Active thread status and compact activity view.
- Reply, pause, approve, and deny actions.
- Installable Decky package generation with `pnpm run package`.
