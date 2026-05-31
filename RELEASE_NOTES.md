# Codex Remote v0.1.14

Scrollable transcript and streaming pass.

## Highlights

- Replaces the one-line activity log with a scrollable transcript.
- Adds professional cards for Codex/user messages, reasoning, commands, tools, file changes, approvals, errors, and events.
- Keeps streaming Codex deltas together as one live transcript item.
- Formats command and tool payloads in compact monospace blocks with statuses.
- Verified through package builds and live Codex App Server transcript reads.

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
