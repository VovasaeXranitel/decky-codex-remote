# Changelog

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
