# Codex Remote v0.1.1

Patch release for the first Steam Deck install test.

## Highlights

- Fixes backend startup under Decky Loader v3.2.4.
- Keeps bundled Python modules importable from the installed plugin folder.
- Keeps Codex App Server client state compatible with Decky's plugin invocation model.

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
