# Security

Codex Remote does not ask for or store an OpenAI password, ChatGPT session cookie, or OpenAI API key.

The plugin stores only the Codex App Server host, port, and App Server capability token configured by the user. Treat that token like a local remote-control secret.

Recommended setup:

- Run Codex App Server only on a trusted LAN.
- Use a strong capability token.
- Do not expose the App Server port to the public internet.
- Rotate the token if the Steam Deck or token file is lost.
- Prefer a private firewall profile and a single inbound rule for the chosen App Server port.
- Do not publish screenshots or logs that contain the App Server token.

Please report security issues privately rather than opening a public issue.
