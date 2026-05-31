# Codex Remote v0.1.2

Steam Deck usability patch.

## Highlights

- Reworks the panel around native Decky button rows.
- Removes custom/nested button layouts that were unreliable with Steam Deck focus navigation.
- Hides approval and pause actions until they are usable.
- Saves current settings before connect, scan, account, and login actions.
- Keeps the panel more compact for the Decky side drawer.

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
