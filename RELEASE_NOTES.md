# Codex Remote v0.1.5

LAN discovery and Steam Deck panel cleanup patch.

## Highlights

- Removes localhost-only discovery behavior from the production LAN scanner.
- Scans SteamOS IPv4 LAN prefixes even when a saved host is configured.
- Replaces the broken localized labels with stable ASCII labels.
- Keeps Decky buttons dark and adds gamepad OK handling.
- Verified from Steam Deck with both saved-host and blank-host LAN scans.

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
