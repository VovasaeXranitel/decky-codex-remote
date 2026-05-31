# Codex Remote v0.1.16

Native transcript scrolling.

## Highlights

- Removes the temporary `Up` and `Down` scroll buttons.
- Makes transcript cards focusable so Decky scrolls the native panel as focus moves through the chat.
- Keeps the transcript inside Decky's native `ScrollPanel` and `ScrollPanelGroup`.
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
