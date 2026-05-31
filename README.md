# Codex Remote

Decky Loader plugin for controlling a Codex App session from the Steam Deck quick access panel.

The plugin is designed to be account-neutral. It does not include an OpenAI API key, does not ship with a developer account, and does not store OpenAI credentials. Each user connects it to their own Codex App Server endpoint.

> Alpha status: Codex App Server WebSocket support is currently experimental upstream. This plugin is usable for testing, but the protocol may change.

## Current MVP

- Codex-style Decky side panel.
- Host, port, token, and auto-refresh settings.
- LAN scan for Codex App Server discovery.
- ChatGPT device-code login through Codex App Server.
- Chat picker with user-facing Codex thread names/previews.
- Current chat/status/task view.
- Scrollable transcript with structured Codex, user, reasoning, command, tool, file-change, approval, and error cards.
- Native Decky transcript scrolling with focusable transcript cards that scroll into view during gamepad navigation.
- Transcript auto-scrolls to the latest message during refresh and streaming.
- Controller-friendly `Approve`, `Deny`, `Pause`, and `Reply` actions.
- Python backend for persisted plugin settings.
- Direct Codex App Server WebSocket JSON-RPC client in the plugin backend.

The current MVP can connect to Codex App Server, list/read/select threads, send replies, interrupt an active turn, and answer App Server approval requests that are routed to this client.

## Target Connection

```text
Steam Deck Decky plugin
  -> WebSocket JSON-RPC
  -> Codex App Server on the user's PC
  -> the user's Codex App session
```

No separate bridge service is planned.

## User Setup

1. Install Decky Loader on the Steam Deck.
2. Download the latest `CodexRemote.zip` release and extract it.
3. Copy the extracted `CodexRemote` folder to `/home/deck/homebrew/plugins/CodexRemote`.
4. Restart Decky Loader.
5. Start Codex App Server on the PC where Codex App is running.
6. Open the plugin settings on Steam Deck.
7. Press `Scan LAN`, or enter the PC host and port manually.
8. Enter the App Server token for the user's own Codex App Server.
9. Press `Connect`.
10. If Codex is not signed in, press `Sign in ChatGPT`, then open the shown URL and enter the shown code.

Restart Decky Loader:

```bash
systemctl --user restart plugin_loader.service
```

Codex App Server example:

```bash
codex app-server --listen ws://0.0.0.0:43871 --ws-auth capability-token --ws-token-file /path/to/token.txt
```

Keep the listener on a trusted LAN and use a strong token.

## Connection Flow

1. Steam Deck discovers or selects the user's PC.
2. The plugin connects to Codex App Server with the App Server token.
3. Codex App Server owns ChatGPT/OpenAI authentication.
4. If sign-in is needed, the plugin starts the official ChatGPT device-code flow and displays the URL/code.

Legacy manual setup:

1. Install Decky Loader on the Steam Deck.
2. Install this plugin into Decky.
3. Start Codex App Server on the PC where Codex App is running.
4. Open the plugin settings on Steam Deck.
5. Press `Scan LAN`, or enter the PC host and port manually.
6. Enter the App Server token for the user's own Codex App Server.
7. Press `Connect`.
8. If Codex is not signed in, press `Sign in ChatGPT`, then open the shown URL and enter the shown code.

Default port placeholder:

```text
43871
```

The plugin should not ask for an OpenAI username, password, API key, or ChatGPT session. Codex App on the PC owns OpenAI authentication. The Decky plugin only authenticates to the user's own Codex App Server using the App Server token.

For ChatGPT sign-in, the plugin uses Codex App Server's official device-code flow. The Steam Deck only displays the `verificationUrl` and `userCode`; the actual ChatGPT login happens in the browser on the user's chosen device.

## Development

Install dependencies:

```bash
pnpm install
```

Build the Decky frontend:

```bash
pnpm run build
```

Create an installable Decky package:

```powershell
pnpm run package
```

The package command creates:

```text
build/CodexRemote/
build/CodexRemote.zip
```

The installable folder includes only the runtime files Decky needs:

```text
plugin.json
package.json
main.py
codex_app_client.py
README.md
LICENSE
dist/index.js
```

## Manual Install On Steam Deck

Copy the packaged folder to the Decky plugins directory:

```bash
scp -r build/CodexRemote deck@steamdeck:/home/deck/homebrew/plugins/
```

Restart Decky Loader:

```bash
systemctl --user restart plugin_loader.service
```

After restart, the plugin should appear in the Decky quick access menu.

## Local Preview

The optional browser preview is for desktop UI iteration only:

```text
preview/index.html
```

It is not included in the Decky package.
