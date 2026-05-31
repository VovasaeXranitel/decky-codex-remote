# Codex Remote v0.1.3

Steam Deck readability patch.

## Highlights

- Replaces bright Steam buttons with dark focused controls.
- Keeps controller navigation through Decky `Focusable`.
- Improves SteamOS LAN address discovery with `ip` route/address fallback.
- Keeps direct LAN setup as the default path.

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
