# Codex Remote v0.1.34

Responsive offline controls and reliable persisted chats.

## Highlights

- Keeps Decky RPC responsive while an offline App Server reconnects in the background.
- Restores Scan, Link, Check, and other controls when the configured endpoint is unavailable.
- Resumes persisted App Server threads before reading them or sending a new turn.
- Shows a normal disconnected state when an action cannot reach the server.
- Adds regression coverage for the offline polling queue and persisted chats.

## Install

Download `CodexRemote.zip` from the release, extract it, and copy the `CodexRemote` folder to:

```text
/home/deck/homebrew/plugins/CodexRemote
```

Then restart Decky Loader:

```bash
sudo systemctl restart plugin_loader.service
```

## Notes

This is an alpha release. Codex App Server WebSocket support is experimental upstream, so expect protocol changes.
