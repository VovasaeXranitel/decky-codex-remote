# Codex Remote v0.1.13

Chat picker and title fix.

## Highlights

- Adds a `Chat` picker for switching Codex threads from the Steam Deck panel.
- Uses Codex thread names/previews instead of raw UUID thread ids.
- Adds clearer spacing between compact buttons.
- Keeps the panel focused on chat, task, activity, approvals, and reply.
- Verified through package builds and live Steam Deck QuickAccess screenshots.

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
