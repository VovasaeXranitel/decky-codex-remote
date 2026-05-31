# Codex Remote v0.1.12

Steam Deck panel density pass.

## Highlights

- Moves Setup and Sync into compact header actions.
- Keeps the default panel focused on status, current task, activity, and reply.
- Shortens connection controls to Scan, Link, ChatGPT, and More.
- Keeps manual Host/Port/Token controls in Advanced.
- Verified through live Steam Deck QuickAccess CEF screenshots.

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
