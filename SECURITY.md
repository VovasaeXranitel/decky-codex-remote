# Security

Codex Remote does not ask for or store an OpenAI password, ChatGPT session cookie, or OpenAI API key.

The plugin stores only the Codex App Server endpoint settings and App Server capability token configured by the user. Treat that token like a remote-control secret.

Recommended setup:

- Run Codex App Server only on a trusted LAN unless you are using a deliberate private remote setup.
- Use a strong capability token.
- Do not expose the App Server port to the public internet.
- Rotate the token if the Steam Deck or token file is lost.
- Prefer a private firewall profile and a single inbound rule for the chosen App Server port.
- Do not publish screenshots or logs that contain the App Server token.
- Do not commit VPN subscription URLs, proxy credentials, App Server tokens, or generated configs that contain provider node credentials.
- If using `Server URL`, prefer `wss://` and keep the remote endpoint behind your own authentication and network controls.
- If using VPN proxy mode, remember that WebSocket control traffic may leave the LAN. Keep Steam, LAN, and private IP ranges direct in the VPN client.
- The plugin does not ask for OpenAI account credentials, ChatGPT cookies, or OpenAI API keys. Codex App Server owns ChatGPT/OpenAI authentication.

Please report security issues privately rather than opening a public issue.
