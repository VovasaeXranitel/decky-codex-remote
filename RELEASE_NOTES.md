# Codex Remote v0.1.17

Transcript focus scrolling fix.

## Highlights

- Restores a real overflow container inside the native Decky scroll area.
- Makes transcript navigation use vertical focus flow.
- Scrolls each focused transcript card into view on Steam Deck gamepad focus.
- Keeps the temporary `Up` and `Down` buttons removed.
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
