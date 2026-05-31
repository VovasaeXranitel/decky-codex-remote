# Codex Remote v0.1.15

Steam Deck transcript scrolling fix.

## Highlights

- Wraps the transcript in Decky's native `ScrollPanel` and `ScrollPanelGroup`.
- Adds explicit `Up` and `Down` controls so scrolling works from the Steam Deck controls.
- Keeps wheel/touch scrolling on the focused transcript area.
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
