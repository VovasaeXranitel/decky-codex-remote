# Codex Remote v0.1.28

CSS Loader-inspired Decky UX polish.

## Highlights

- Replaces the custom tab strip with a native Decky `DropdownItem` view selector.
- Uses `PanelSection` titles for the active view, closer to CSS Loader's Quick Access layout.
- Keeps compact pages for Remote, Chats, Auth, Setup, and Log.
- Keeps the Remote page focused on current chat, task, approvals, transcript, quick actions, and composer.
- Moves chat search and selection into a dedicated Chats page.
- Moves ChatGPT account checks and device-code login into a dedicated Auth page.
- Moves LAN scan, Link, Check, Disconnect, host, port, token, and live updates into Setup.
- Adds a lightweight Log page for connection, account, action, and App Server messages.
- Keeps the secure App Server token flow from v0.1.26.
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
