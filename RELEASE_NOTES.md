# Codex Remote v0.1.7

Mobile-style Codex control surface pass.

## Highlights

- Makes current work, activity, approvals, and message input the main panel flow.
- Moves connection, scan, token, and account controls into a compact Setup area.
- Adds visual hierarchy for primary, quiet, and deny actions.
- Keeps the v0.1.6 Decky callable fix and universal LAN scan.

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
