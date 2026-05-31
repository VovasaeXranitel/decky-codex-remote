# Codex Remote v0.1.19

Auto-scroll transcript tail.

## Highlights

- Automatically keeps the transcript pinned to the latest message.
- Updates the scroll position during refreshes and streaming text growth.
- Removes custom D-pad transcript scroll interception.
- Avoids relying on Steam Deck scrollbar activation.
- Keeps the transcript inside Decky's native scroll components.
- Keeps the v0.1.14 structured transcript cards and streaming behavior.
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
