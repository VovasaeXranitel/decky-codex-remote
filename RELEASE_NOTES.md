# Codex Remote v0.1.35

Complete Codex App Server handshake.

## Highlights

- Sends the required `initialized` notification after `initialize`.
- Prevents the App Server from resetting a successfully opened WebSocket session.
- Skips chats currently owned by another Codex client and opens the first available chat.
- Keeps the responsive offline controls and persisted-chat fixes from v0.1.34.
- Adds regression coverage for initialization message ordering.

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
