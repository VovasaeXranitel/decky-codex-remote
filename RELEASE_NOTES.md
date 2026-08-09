# Codex Remote v0.1.30

Backend onion architecture refactor.

## Highlights

- Keeps `main.py` as a thin Decky callable adapter.
- Adds `codex_remote/domain` for defaults and settings normalization.
- Adds `codex_remote/infrastructure` for settings persistence, LAN discovery, and WebSocket transport.
- Adds `codex_remote/application` for Codex session orchestration and transcript mapping.
- Adds Python unit tests around the backend seams.
- Packages `codex_remote/` into Decky builds.
- Builds release zips with SteamOS-friendly path separators.
- Keeps the bottom-navigation frontend from v0.1.29.

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
