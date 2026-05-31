# Codex Remote v0.1.20

Smarter Deck panel controls.

## Highlights

- Adds a searchable chat picker with loaded-chat markers.
- Adds quick commands for Continue, Explain, Retry, and Summary.
- Turns approvals into one focused card with command details and Approve/Deny actions.
- Shows a more useful current task derived from the latest Codex event.
- Keeps transcript auto-scroll and structured cards for messages, commands, tools, files, approvals, and errors.
- Verified through package build and Python backend checks.

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
