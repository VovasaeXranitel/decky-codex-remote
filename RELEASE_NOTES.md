# Codex Remote v0.1.0

Initial alpha release of Codex Remote, a Decky Loader plugin for controlling a Codex App session from the Steam Deck quick access panel.

## Highlights

- Codex-style Decky side panel.
- LAN scan for Codex App Server discovery.
- ChatGPT device-code sign-in through Codex App Server.
- Direct WebSocket JSON-RPC client in the Decky Python backend.
- Active thread status, compact activity log, reply, pause, approve, and deny controls.

## Install

Download `CodexRemote.zip` from the release, extract it, and copy the `CodexRemote` folder to:

```text
/home/deck/homebrew/plugins/CodexRemote
```

Then restart Decky Loader:

```bash
systemctl --user restart plugin_loader.service
```

## Notes

This is an alpha release. Codex App Server WebSocket support is experimental upstream, so expect protocol changes.
