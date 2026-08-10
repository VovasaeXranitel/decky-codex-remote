# Codex Remote v0.1.33

Connection-mode UX and diagnostics.

## Highlights

- Adds LAN/Remote URL mode selection on the Setup page.
- Shows only the relevant endpoint fields for the selected mode.
- Adds diagnostics for endpoint, token, proxy reachability, and VPN tunnel state.
- Keeps optional HTTP CONNECT proxy support for split VPN clients.
- Keeps remote endpoint hardening from v0.1.32.

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
