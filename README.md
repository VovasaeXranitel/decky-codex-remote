# Codex Remote

Decky Loader plugin for controlling a Codex App session from the Steam Deck quick access panel.

The plugin is designed to be account-neutral. It does not include an OpenAI API key, does not ship with a developer account, and does not store OpenAI credentials. Each user connects it to their own Codex App Server endpoint.

> Alpha status: Codex App Server WebSocket support is currently experimental upstream. This plugin is usable for testing, but the protocol may change.

## Features

- Codex-style Decky side panel.
- Compact pages for Remote, Chats, Auth, Setup, and Log.
- Secure setup mode for host, port, App Server capability token, LAN scan, and diagnostics.
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

The plugin can connect to Codex App Server, list/read/select threads, send replies, interrupt an active turn, and answer App Server approval requests that are routed to this client.

## Target Connection

```text
Steam Deck Decky plugin
  -> WebSocket JSON-RPC
  -> Codex App Server on the user's PC
  -> the user's Codex App session
```

No separate bridge service is planned.

## Install

1. Install Decky Loader on the Steam Deck.
2. Download the latest `CodexRemote.zip` release and extract it.
3. Copy the extracted `CodexRemote` folder to `/home/deck/homebrew/plugins/CodexRemote`.
4. Restart Decky Loader.

Restart Decky Loader:

```bash
sudo systemctl restart plugin_loader.service
```

## User Setup

1. Start Codex App Server on the PC where Codex App is running.
2. Open the Codex Remote plugin on Steam Deck.
3. Open the `Setup` page.
4. Press `Scan`, or enter the PC host and port manually on the `Setup` page.
5. Enter the App Server capability token for the user's own Codex App Server.
6. Press `Link`.
7. Open the `Auth` page and press `Check`.
8. If Codex is not signed in, press `Login`, then open the shown URL and enter the shown code.

Windows Firewall example for the default port:

```powershell
New-NetFirewallRule `
  -DisplayName "Codex App Server 43871" `
  -Direction Inbound `
  -Action Allow `
  -Protocol TCP `
  -LocalPort 43871 `
  -Profile Private
```

Codex App Server example:

```bash
codex app-server --listen ws://0.0.0.0:43871 --ws-auth capability-token --ws-token-file /path/to/token.txt
```

Keep the listener on a trusted LAN and use a strong token. Codex Remote requires a token before it will open the WebSocket control channel. LAN scan uses `/readyz` only to discover a reachable App Server; `Link` validates the token through the WebSocket handshake.

Codex App Server is documented by OpenAI here: https://developers.openai.com/codex/app-server

## Connection Flow

1. Steam Deck discovers or selects the user's PC.
2. The plugin connects to Codex App Server with the App Server capability token.
3. Codex App Server owns ChatGPT/OpenAI authentication.
4. If sign-in is needed, the plugin starts the official ChatGPT device-code flow and displays the URL/code.

## Planned Official Relay Mode

OpenAI already supports remote Codex control through the official ChatGPT mobile app and Codex App remote connections flow. A future version of this plugin may add an official relay mode so Steam Deck can connect through the same kind of account-based remote access instead of relying on LAN/VPN connectivity.

This is not implemented yet because OpenAI has not documented a public third-party SDK or API for registering non-ChatGPT clients with the Codex remote relay. Until that exists, Codex Remote uses the documented Codex App Server path.

Default port placeholder:

```text
43871
```

The plugin should not ask for an OpenAI username, password, API key, or ChatGPT session. Codex App on the PC owns OpenAI authentication. The Decky plugin only authenticates to the user's own Codex App Server using the App Server capability token.

For ChatGPT sign-in, the plugin uses Codex App Server's official device-code flow. The Steam Deck only displays the `verificationUrl` and `userCode`; the actual ChatGPT login happens in the browser on the user's chosen device.

## Troubleshooting

### LAN scan finds nothing

- Make sure Steam Deck and PC are on the same trusted LAN.
- Make sure Codex App Server listens on `0.0.0.0`, not only `127.0.0.1`.
- Open the App Server TCP port in the PC firewall.
- Try entering the PC LAN IP manually on the `Setup` page.
- Scan does not check the token. It only checks `/readyz`.

### Link fails

- Check that the host, port, and token match the running Codex App Server.
- Press `Check` on the `Setup` page.
- Restart Codex App Server and press `Sync`.
- If the error is `401` or `403`, rotate/copy the App Server token again.

### ChatGPT login does not appear

- Open the `Auth` page, press `Check`, then press `Login` if Codex App Server reports no ChatGPT account.
- The plugin does not collect ChatGPT credentials. It only displays the device-code URL/code returned by Codex App Server.

### Buttons look disabled

- Connect to Codex App Server first.
- Select a chat if there are multiple threads.
- `Pause` is enabled only while Codex is actively working.

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
