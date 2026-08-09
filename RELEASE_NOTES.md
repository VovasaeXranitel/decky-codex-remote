# Codex Remote v0.1.29

Approved bottom-navigation frontend.

## Highlights

- Replaces the `DropdownItem` view picker with a persistent bottom navigation bar.
- Makes Remote the primary page for live Codex control.
- Combines current chat and current task into a compact context block.
- Gives the transcript more vertical room after removing the old view selector row.
- Keeps Chats, Auth, Setup, and Log as separate focused pages under the same navigation model.
- Keeps searchable chats, quick commands, focused approvals, structured transcript cards, and auto-scroll.
- Keeps the secure Codex App Server token flow.

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
