# Codex Remote v0.1.4

LAN scan feedback patch.

## Highlights

- Checks the configured host before doing a full subnet scan.
- Makes `192.168.1.81:43871` resolve immediately when reachable.
- Shows the actual Decky/frontend error if scan callable fails.
- Verified from Steam Deck against `http://192.168.1.81:43871/readyz`.

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
