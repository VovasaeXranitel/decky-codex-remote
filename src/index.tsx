import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api";
import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  TextField,
  ToggleField,
} from "@decky/ui";
import { FC, useEffect, useMemo, useState } from "react";
import { FaCheck, FaCog, FaPause, FaTimes } from "react-icons/fa";

type CodexState = {
  status: "disconnected" | "idle" | "working" | "approval";
  thread: string;
  task: string;
  approvalText?: string;
  command?: string;
  messages: string[];
};

type Settings = {
  host: string;
  port: string;
  token: string;
  autoRefresh: boolean;
};

type ConnectionCheck = {
  ok: boolean;
  message: string;
};

type DiscoveredDevice = {
  host: string;
  port: string;
  label: string;
};

type ScanResult = ConnectionCheck & {
  devices: DiscoveredDevice[];
};

type AccountInfo = ConnectionCheck & {
  account?: {
    type: string;
    email?: string;
    planType?: string;
  } | null;
  requiresOpenaiAuth?: boolean;
};

type ChatGptLogin = ConnectionCheck & {
  type?: "chatgptDeviceCode";
  loginId?: string;
  verificationUrl?: string;
  userCode?: string;
};

const defaultState: CodexState = {
  status: "disconnected",
  thread: "Decky remote",
  task: "Not connected",
  messages: ["Set Codex App Server address to connect."],
};

const defaultSettings: Settings = {
  host: "",
  port: "43871",
  token: "",
  autoRefresh: true,
};

const getSettings = callable<[], Settings>("get_settings");
const setSettings = callable<[Settings], Settings>("set_settings");
const getState = callable<[], CodexState>("get_state");
const sendAction = callable<[string, string?], CodexState>("send_action");
const testConnection = callable<[], ConnectionCheck>("test_connection");
const connectServer = callable<[], ConnectionCheck>("connect");
const disconnectServer = callable<[], ConnectionCheck>("disconnect");
const scanLan = callable<[], ScanResult>("scan_lan");
const getAccount = callable<[], AccountInfo>("get_account");
const startChatGptLogin = callable<[], ChatGptLogin>("start_chatgpt_login");

const statusLabel: Record<CodexState["status"], string> = {
  approval: "approval",
  disconnected: "offline",
  idle: "idle",
  working: "working",
};

const statusClass: Record<CodexState["status"], string> = {
  approval: "codexRemoteStatusApproval",
  disconnected: "codexRemoteStatusOffline",
  idle: "codexRemoteStatusIdle",
  working: "codexRemoteStatusWorking",
};

const styles = `
.codexRemote {
  color: #d8d8d8;
}

.codexRemoteHeader {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 6px 0 10px;
}

.codexRemoteTitle,
.codexRemotePluginTitle {
  color: #f0f0f0;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0;
}

.codexRemoteEndpoint,
.codexRemoteMuted {
  color: #8a8a8a;
  font-size: 11px;
  letter-spacing: 0;
}

.codexRemoteIconButton {
  align-items: center;
  background: #202020;
  border: 1px solid #343434;
  border-radius: 6px;
  color: #d8d8d8;
  display: flex;
  height: 30px;
  justify-content: center;
  width: 30px;
}

.codexRemoteSettings {
  border-bottom: 1px solid #2a2a2a;
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.codexRemoteThread {
  align-items: center;
  display: flex;
  gap: 8px;
  min-height: 24px;
}

.codexRemoteDot {
  border-radius: 50%;
  display: inline-block;
  height: 7px;
  width: 7px;
}

.codexRemoteStatusApproval {
  background: #c8c8c8;
}

.codexRemoteStatusIdle {
  background: #777;
}

.codexRemoteStatusOffline {
  background: #555;
}

.codexRemoteStatusWorking {
  background: #58a66c;
}

.codexRemoteTask {
  border-top: 1px solid #2a2a2a;
  padding-top: 10px;
}

.codexRemoteLog {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.codexRemoteMessage {
  color: #d8d8d8;
  font-size: 12px;
  line-height: 1.35;
}

.codexRemoteApproval {
  background: #171717;
  border: 1px solid #343434;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 10px;
}

.codexRemoteApproval code {
  background: #0f0f0f;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  color: #d8d8d8;
  display: block;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  padding: 7px;
}

.codexRemoteActions {
  display: grid;
  gap: 8px;
  grid-template-columns: 1fr 1fr;
  width: 100%;
}
`;

const CodexRemotePanel: FC = () => {
  const [state, setState] = useState<CodexState>(defaultState);
  const [settings, setLocalSettings] = useState<Settings>(defaultSettings);
  const [reply, setReply] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [connectionMessage, setConnectionMessage] = useState("");
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [accountMessage, setAccountMessage] = useState("");
  const [login, setLogin] = useState<ChatGptLogin | null>(null);

  const endpoint = useMemo(
    () => settings.host ? `ws://${settings.host}:${settings.port}` : "not configured",
    [settings.host, settings.port],
  );

  const refreshState = async () => {
    try {
      setState(await getState());
    } catch (error) {
      console.warn("[Codex Remote] Failed to refresh state", error);
      setState(defaultState);
    }
  };

  useEffect(() => {
    getSettings()
      .then((nextSettings) => setLocalSettings({ ...defaultSettings, ...nextSettings }))
      .catch((error) => console.warn("[Codex Remote] Failed to load settings", error));

    refreshState();
  }, []);

  useEffect(() => {
    if (!settings.autoRefresh) {
      return;
    }

    const timer = window.setInterval(refreshState, 2500);
    return () => window.clearInterval(timer);
  }, [settings.autoRefresh]);

  const persistSettings = async (nextSettings: Settings) => {
    setLocalSettings(nextSettings);
    try {
      await setSettings(nextSettings);
    } catch (error) {
      console.warn("[Codex Remote] Failed to save settings", error);
    }
  };

  const runConnectionTest = async () => {
    try {
      const result = await testConnection();
      setConnectionMessage(result.message);
      toaster.toast({
        title: "Codex Remote",
        body: result.message,
      });
      await refreshState();
    } catch (error) {
      console.warn("[Codex Remote] Connection test failed", error);
      setConnectionMessage("Connection test failed.");
    }
  };

  const runConnect = async () => {
    try {
      const result = await connectServer();
      setConnectionMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
      await refreshState();
    } catch (error) {
      console.warn("[Codex Remote] Connect failed", error);
      setConnectionMessage("Connect failed.");
    }
  };

  const runDisconnect = async () => {
    try {
      const result = await disconnectServer();
      setConnectionMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
      await refreshState();
    } catch (error) {
      console.warn("[Codex Remote] Disconnect failed", error);
      setConnectionMessage("Disconnect failed.");
    }
  };

  const runScanLan = async () => {
    try {
      setConnectionMessage("Scanning LAN...");
      const result = await scanLan();
      setDevices(result.devices || []);
      setConnectionMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
    } catch (error) {
      console.warn("[Codex Remote] LAN scan failed", error);
      setConnectionMessage("LAN scan failed.");
    }
  };

  const selectDevice = async (device: DiscoveredDevice) => {
    const nextSettings = { ...settings, host: device.host, port: device.port };
    await persistSettings(nextSettings);
    setConnectionMessage(`Selected ${device.label}`);
  };

  const runGetAccount = async () => {
    try {
      const result = await getAccount();
      setAccountMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
      await refreshState();
    } catch (error) {
      console.warn("[Codex Remote] Account check failed", error);
      setAccountMessage("Account check failed.");
    }
  };

  const runChatGptLogin = async () => {
    try {
      const result = await startChatGptLogin();
      setLogin(result);
      setAccountMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
    } catch (error) {
      console.warn("[Codex Remote] ChatGPT login failed", error);
      setAccountMessage("ChatGPT login failed.");
    }
  };

  const runAction = async (action: string, payload?: string) => {
    try {
      const nextState = await sendAction(action, payload);
      setState(nextState);

      if (action === "reply") {
        setReply("");
      }
    } catch (error) {
      console.warn("[Codex Remote] Action failed", error);
      toaster.toast({
        title: "Codex Remote",
        body: "Action failed. Check Codex App Server connection.",
      });
    }
  };

  return (
    <div className="codexRemote">
      <style>{styles}</style>
      <PanelSection>
        <div className="codexRemoteHeader">
          <div>
            <div className="codexRemoteTitle">Codex</div>
            <div className="codexRemoteEndpoint">{endpoint}</div>
          </div>
          <button
            className="codexRemoteIconButton"
            onClick={() => setShowSettings(!showSettings)}
          >
            <FaCog />
          </button>
        </div>

        {showSettings && (
          <div className="codexRemoteSettings">
            <PanelSectionRow>
              <TextField
                label="Host"
                value={settings.host}
                onChange={(event) =>
                  persistSettings({ ...settings, host: event.target.value })
                }
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={runScanLan}>
                Scan LAN
              </ButtonItem>
            </PanelSectionRow>
            {devices.map((device) => (
              <PanelSectionRow key={`${device.host}:${device.port}`}>
                <ButtonItem layout="below" onClick={() => selectDevice(device)}>
                  {device.label}
                </ButtonItem>
              </PanelSectionRow>
            ))}
            <PanelSectionRow>
              <TextField
                label="Port"
                value={settings.port}
                onChange={(event) =>
                  persistSettings({ ...settings, port: event.target.value })
                }
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <TextField
                label="App Server token"
                value={settings.token}
                onChange={(event) =>
                  persistSettings({ ...settings, token: event.target.value })
                }
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <ToggleField
                label="Auto refresh"
                checked={settings.autoRefresh}
                onChange={(checked) =>
                  persistSettings({ ...settings, autoRefresh: checked })
                }
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteActions">
                <ButtonItem layout="below" onClick={runConnect}>
                  Connect
                </ButtonItem>
                <ButtonItem layout="below" onClick={runDisconnect}>
                  Disconnect
                </ButtonItem>
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <ButtonItem layout="below" onClick={runConnectionTest}>
                Check /readyz
              </ButtonItem>
            </PanelSectionRow>
            {connectionMessage && (
              <PanelSectionRow>
                <div className="codexRemoteMessage">{connectionMessage}</div>
              </PanelSectionRow>
            )}
            <PanelSectionRow>
              <div className="codexRemoteActions">
                <ButtonItem layout="below" onClick={runChatGptLogin}>
                  Sign in ChatGPT
                </ButtonItem>
                <ButtonItem layout="below" onClick={runGetAccount}>
                  Account
                </ButtonItem>
              </div>
            </PanelSectionRow>
            {login?.verificationUrl && login?.userCode && (
              <PanelSectionRow>
                <div className="codexRemoteApproval">
                  <div>Open this URL and enter the code.</div>
                  <code>{login.verificationUrl}</code>
                  <code>{login.userCode}</code>
                </div>
              </PanelSectionRow>
            )}
            {accountMessage && (
              <PanelSectionRow>
                <div className="codexRemoteMessage">{accountMessage}</div>
              </PanelSectionRow>
            )}
          </div>
        )}

        <PanelSectionRow>
          <div className="codexRemoteThread">
            <span className={`codexRemoteDot ${statusClass[state.status]}`} />
            <span>{state.thread}</span>
            <span className="codexRemoteMuted">{statusLabel[state.status]}</span>
          </div>
        </PanelSectionRow>

        <PanelSectionRow>
          <div className="codexRemoteTask">
            <div className="codexRemoteMuted">Current</div>
            <div>{state.task}</div>
          </div>
        </PanelSectionRow>

        <PanelSectionRow>
          <div className="codexRemoteLog">
            {state.messages.slice(-4).map((message, index) => (
              <div className="codexRemoteMessage" key={`${message}-${index}`}>
                {message}
              </div>
            ))}
          </div>
        </PanelSectionRow>

        {state.approvalText && (
          <PanelSectionRow>
            <div className="codexRemoteApproval">
              <div>{state.approvalText}</div>
              {state.command && <code>{state.command}</code>}
            </div>
          </PanelSectionRow>
        )}

        <PanelSectionRow>
          <div className="codexRemoteActions">
            <ButtonItem
              layout="below"
              onClick={() => runAction("approve")}
              disabled={!state.approvalText}
            >
              <FaCheck /> Approve
            </ButtonItem>
            <ButtonItem
              layout="below"
              onClick={() => runAction("deny")}
              disabled={!state.approvalText}
            >
              <FaTimes /> Deny
            </ButtonItem>
          </div>
        </PanelSectionRow>

        <PanelSectionRow>
          <TextField
            label="Message Codex"
            value={reply}
            onChange={(event) => setReply(event.target.value)}
          />
        </PanelSectionRow>
        <PanelSectionRow>
          <div className="codexRemoteActions">
            <ButtonItem layout="below" onClick={() => runAction("pause")}>
              <FaPause /> Pause
            </ButtonItem>
            <ButtonItem
              layout="below"
              onClick={() => runAction("reply", reply)}
              disabled={!reply.trim()}
            >
              Reply
            </ButtonItem>
          </div>
        </PanelSectionRow>
      </PanelSection>
    </div>
  );
};

export default definePlugin(() => {
  toaster.toast({
    title: "Codex Remote",
    body: "Ready to connect to Codex App Server.",
  });

  return {
    name: "Codex Remote",
    titleView: <div className="codexRemotePluginTitle">Codex</div>,
    content: <CodexRemotePanel />,
    icon: <FaCheck />,
  };
});
