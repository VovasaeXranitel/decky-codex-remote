# Codex Remote v0.1.6

Decky callable runtime fix.

## Highlights

- Adds `api_version: 1` to the Decky manifest.
- Fixes settings and action buttons failing with `api_version 1 or newer is required`.
- Keeps the universal LAN scan and cleaned Steam Deck panel from v0.1.5.
- Verified against the installed plugin on Steam Deck.

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
