# Backend Onion Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the Decky backend into clear onion layers while preserving the existing plugin behavior.

**Architecture:** Keep `main.py` as the Decky adapter. Move application orchestration into services, domain state/types into focused modules, and file/network/WebSocket code into infrastructure modules. Keep public callable names and frontend state shape stable.

**Tech Stack:** Python 3 standard library, Decky plugin backend API, raw WebSocket JSON-RPC, `unittest`.

## Global Constraints

- Do not change frontend callable names.
- Do not add runtime dependencies.
- Keep the installable package small and Decky-compatible.
- Keep Codex App Server token handling local to settings and WebSocket authorization.
- Preserve current frontend `CodexState`, `TranscriptItem`, and thread summary shapes.

---

### Task 1: Domain Models And Settings Store

**Files:**
- Create: `codex_remote/domain/models.py`
- Create: `codex_remote/domain/defaults.py`
- Create: `codex_remote/infrastructure/settings_store.py`
- Create: `tests/test_settings_store.py`
- Modify: `main.py`

**Interfaces:**
- Produces: `DEFAULT_SETTINGS`, `DISCONNECTED_STATE`, `normalize_settings(settings: Mapping[str, Any]) -> dict[str, Any]`
- Produces: `SettingsStore(path: Path).read() -> dict[str, Any]`, `SettingsStore.write(settings: Mapping[str, Any]) -> dict[str, Any]`

- [ ] Write failing settings tests.
- [ ] Run `python -m unittest tests.test_settings_store -v` and verify missing-module failure.
- [ ] Implement settings/default modules.
- [ ] Update `main.py` to use `SettingsStore`.
- [ ] Run the settings test and Python compile check.

### Task 2: Discovery Service

**Files:**
- Create: `codex_remote/infrastructure/discovery.py`
- Create: `tests/test_discovery.py`
- Modify: `main.py`

**Interfaces:**
- Produces: `LanDiscovery.local_ipv4_prefixes() -> list[str]`
- Produces: `LanDiscovery.scan(port: str, configured_host: str = "") -> dict[str, Any]`

- [ ] Write failing tests for configured host dedupe and readyz probe result formatting.
- [ ] Run `python -m unittest tests.test_discovery -v` and verify missing-module failure.
- [ ] Move LAN scan code from `main.py` into `LanDiscovery`.
- [ ] Update `main.py` to delegate `scan_lan`.
- [ ] Run discovery tests and Python compile check.

### Task 3: WebSocket JSON-RPC Infrastructure

**Files:**
- Create: `codex_remote/infrastructure/websocket_transport.py`
- Create: `codex_remote/infrastructure/jsonrpc_ws_client.py`
- Create: `tests/test_websocket_transport.py`
- Modify: `codex_app_client.py`

**Interfaces:**
- Produces: `WebSocketTransport.connect(host: str, port: str, token: str) -> None`
- Produces: `WebSocketTransport.send_json(payload: dict[str, Any]) -> None`
- Produces: `WebSocketTransport.receive_json(timeout: float = 1.0) -> dict[str, Any] | None`
- Produces: `JsonRpcWsClient.call(method: str, params: dict[str, Any] | None, timeout: float) -> Any`

- [ ] Write failing frame tests for masked client frames and unmasked server frames.
- [ ] Run `python -m unittest tests.test_websocket_transport -v` and verify missing-module failure.
- [ ] Move WebSocket handshake/frame code to `WebSocketTransport`.
- [ ] Move pending request handling to `JsonRpcWsClient`.
- [ ] Keep `CodexAppClient` behavior stable.
- [ ] Run websocket tests and Python compile check.

### Task 4: Codex Session Application Service

**Files:**
- Create: `codex_remote/application/codex_session.py`
- Create: `codex_remote/application/state_presenter.py`
- Create: `codex_remote/application/transcript_mapper.py`
- Create: `tests/test_transcript_mapper.py`
- Modify: `codex_app_client.py`

**Interfaces:**
- Produces: `TranscriptMapper.item_to_transcript(item: dict[str, Any]) -> dict[str, Any] | None`
- Produces: `StatePresenter.disconnected(error: str) -> dict[str, Any]`
- Produces: `CodexSession` with `connect`, `disconnect`, `state`, `send_action`, `select_thread`, `account`, `start_chatgpt_login`

- [ ] Write failing transcript mapper tests for user, command, tool, and fallback title behavior.
- [ ] Run mapper tests and verify missing-module failure.
- [ ] Move transcript parsing into `TranscriptMapper`.
- [ ] Move state assembly helpers into `StatePresenter`.
- [ ] Make `codex_app_client.py` a compatibility wrapper around `CodexSession`.
- [ ] Run all Python tests and package build.

### Task 5: Packaging And Deck Verification

**Files:**
- Modify: `scripts/package.ps1`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `package.json`

**Interfaces:**
- Package includes `codex_remote/**` in `build/CodexRemote`.

- [ ] Update packaging script to copy `codex_remote`.
- [ ] Bump version.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `pnpm package`.
- [ ] Install on Steam Deck and verify `plugin_loader.service`, backend process, package version, and Python compile.
