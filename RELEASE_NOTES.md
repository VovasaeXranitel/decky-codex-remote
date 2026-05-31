# Codex Remote v0.1.18

Direct gamepad transcript scrolling.

## Highlights

- Handles Steam Deck `DIR_UP` and `DIR_DOWN` events directly on transcript cards.
- Scrolls the transcript container programmatically, without visible helper buttons.
- Keeps touch and wheel scrolling support.
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
