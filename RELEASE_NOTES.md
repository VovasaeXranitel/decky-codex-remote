# Codex Remote v0.1.26

Secure App Server setup pass.

## Highlights

- Requires an App Server capability token before opening the WebSocket control channel.
- Keeps LAN scan as `/readyz` discovery while `Link` validates the token.
- Promotes `Account` into setup and moves ChatGPT device-code login into an Account card.
- Shows token-specific feedback for `401`/`403` WebSocket handshake failures.
- Updates README setup/security notes to match OpenAI's Codex App Server documentation.
- Waits for Codex App Server `initialize` and the first thread snapshot before reporting Connected.
- Prevents stale disconnected UI immediately after a successful WebSocket link.
- Treats connection initialization as a transient state instead of a failure.
- Fixes the header Hide button so it actually closes setup when a host is configured.
- Only forces setup open when no host is configured.
- Lets the main remote screen show even if the configured Codex server is currently offline.
- Hides chat, transcript, and composer while setup is open so the bottom of the panel is not clipped.
- Keeps setup focused on Scan, Link, Account, advanced settings, and diagnostics.
- Keeps the compact transcript, clamped current task, and softer scrollbar from v0.1.21.
- Keeps searchable chats, quick commands, focused approvals, structured transcript cards, and auto-scroll from v0.1.20.
- Verified through package build, Python backend checks, Deck install, Decky logs, and live QuickAccess inspection.

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
