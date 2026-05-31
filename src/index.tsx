import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api";
import {
  Focusable,
  PanelSection,
  PanelSectionRow,
  TextField,
  ToggleField,
} from "@decky/ui";
import { FC, useEffect, useMemo, useState } from "react";
import { FaTerminal } from "react-icons/fa";

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
  messages: ["Open Settings, scan LAN, then connect."],
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
  color: #d7d7d9;
}

.codexRemoteHeader {
  padding: 2px 0 6px;
}

.codexRemoteTitle,
.codexRemotePluginTitle {
  color: #f1f1f2;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0;
}

.codexRemoteEndpoint,
.codexRemoteMuted {
  color: #8f9298;
  font-size: 11px;
  letter-spacing: 0;
}

.codexRemoteEndpoint {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteSettings {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.codexRemoteCompact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.codexRemoteThread {
  align-items: center;
  display: flex;
  gap: 8px;
  min-height: 24px;
  overflow: hidden;
}

.codexRemoteDot {
  border-radius: 50%;
  display: inline-block;
  flex: 0 0 auto;
  height: 7px;
  width: 7px;
}

.codexRemoteStatusApproval {
  background: #c7c7c9;
}

.codexRemoteStatusIdle {
  background: #7c818c;
}

.codexRemoteStatusOffline {
  background: #565b65;
}

.codexRemoteStatusWorking {
  background: #5fb878;
}

.codexRemoteTask {
  color: #e7e7e8;
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.codexRemoteButtonGrid {
  display: grid;
  gap: 6px;
  grid-template-columns: 1fr 1fr;
}

.codexRemoteButtonGridSingle {
  display: grid;
  gap: 6px;
  grid-template-columns: 1fr;
}

.codexRemoteButton {
  align-items: center;
  background: #171b22;
  border: 1px solid #323844;
  border-radius: 4px;
  color: #d5d8de;
  display: flex;
  font-size: 12px;
  font-weight: 500;
  justify-content: center;
  letter-spacing: 0;
  line-height: 1.15;
  min-height: 31px;
  padding: 5px 8px;
  text-align: center;
  width: 100%;
}

.codexRemoteButton:active {
  background: #212733;
  border-color: #4a5362;
}

.codexRemoteButtonFocus,
.codexRemoteButton:focus {
  background: #242b36;
  border-color: #8c98aa;
  box-shadow: inset 0 0 0 1px #8c98aa;
  color: #f3f4f7;
}

.codexRemoteButtonDisabled {
  color: #737985;
  opacity: 0.55;
}

.codexRemoteLog {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.codexRemoteMessage {
  color: #d7d7d9;
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.codexRemoteApproval {
  background: #15171c;
  border: 1px solid #303641;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 9px;
}

.codexRemoteApproval code {
  background: #0f1115;
  border: 1px solid #2a3039;
  border-radius: 4px;
  color: #d8d8d8;
  display: block;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  padding: 7px;
  white-space: pre-wrap;
  word-break: break-word;
}

.codexRemoteRow {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteTextArea input {
  min-height: 38px;
}
`;

type CodexButtonProps = {
  children: string;
  disabled?: boolean;
  onClick: () => void;
};

const CodexButton: FC<CodexButtonProps> = ({ children, disabled = false, onClick }) => {
  const activate = () => {
    if (!disabled) {
      onClick();
    }
  };

  return (
    <Focusable
      className={`codexRemoteButton${disabled ? " codexRemoteButtonDisabled" : ""}`}
      focusClassName="codexRemoteButtonFocus"
      onActivate={activate}
      onClick={activate}
      onOKButton={activate}
      role="button"
      tabIndex={0}
    >
      {children}
    </Focusable>
  );
};

const CodexRemotePanel: FC = () => {
  const [state, setState] = useState<CodexState>(defaultState);
  const [settings, setLocalSettings] = useState<Settings>(defaultSettings);
  const [reply, setReply] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [connectionMessage, setConnectionMessage] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [accountMessage, setAccountMessage] = useState("");
  const [login, setLogin] = useState<ChatGptLogin | null>(null);

  const endpoint = useMemo(
    () => (settings.host ? `ws://${settings.host}:${settings.port}` : "not configured"),
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
      return nextSettings;
    } catch (error) {
      console.warn("[Codex Remote] Failed to save settings", error);
      setConnectionMessage("Failed to save settings.");
      return nextSettings;
    }
  };

  const runConnectionTest = async () => {
    try {
      await setSettings(settings);
      const result = await testConnection();
      setConnectionMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
      await refreshState();
    } catch (error) {
      console.warn("[Codex Remote] Connection test failed", error);
      setConnectionMessage("Connection test failed.");
    }
  };

  const runConnect = async () => {
    try {
      await setSettings(settings);
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
      await setSettings(settings);
      setConnectionMessage("Scanning LAN...");
      const result = await scanLan();
      setDevices(result.devices || []);
      setConnectionMessage(result.message);
      toaster.toast({ title: "Codex Remote", body: result.message });
    } catch (error) {
      console.warn("[Codex Remote] LAN scan failed", error);
      setConnectionMessage(`LAN scan failed: ${String(error)}`);
    }
  };

  const selectDevice = async (device: DiscoveredDevice) => {
    const nextSettings = { ...settings, host: device.host, port: device.port };
    await persistSettings(nextSettings);
    setConnectionMessage(`Selected ${device.label}`);
  };

  const runGetAccount = async () => {
    try {
      await setSettings(settings);
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
      await setSettings(settings);
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
      setActionMessage("");

      if (action === "reply") {
        setReply("");
      }
    } catch (error) {
      console.warn("[Codex Remote] Action failed", error);
      setActionMessage("Action failed. Check connection.");
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
          <div className="codexRemoteTitle">Codex</div>
          <div className="codexRemoteEndpoint">{endpoint}</div>
        </div>

        <PanelSectionRow>
          <div className="codexRemoteButtonGrid">
            <CodexButton onClick={() => setShowSettings(!showSettings)}>
              {showSettings ? "Hide Settings" : "Settings"}
            </CodexButton>
            <CodexButton onClick={refreshState}>Refresh</CodexButton>
          </div>
        </PanelSectionRow>

        {showSettings && (
          <div className="codexRemoteSettings">
            <PanelSectionRow>
              <TextField
                label="Host"
                value={settings.host}
                onChange={(event) => persistSettings({ ...settings, host: event.target.value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteButtonGridSingle">
                <CodexButton onClick={runScanLan}>Scan LAN</CodexButton>
              </div>
            </PanelSectionRow>
            {devices.map((device) => (
              <PanelSectionRow key={`${device.host}:${device.port}`}>
                <div className="codexRemoteButtonGridSingle">
                  <CodexButton onClick={() => selectDevice(device)}>{device.label}</CodexButton>
                </div>
              </PanelSectionRow>
            ))}
            <PanelSectionRow>
              <TextField
                label="Port"
                value={settings.port}
                onChange={(event) => persistSettings({ ...settings, port: event.target.value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <TextField
                label="Token"
                value={settings.token}
                bIsPassword
                onChange={(event) => persistSettings({ ...settings, token: event.target.value })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <ToggleField
                label="Auto refresh"
                checked={settings.autoRefresh}
                onChange={(checked) => persistSettings({ ...settings, autoRefresh: checked })}
              />
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteButtonGrid">
                <CodexButton onClick={runConnect}>Connect</CodexButton>
                <CodexButton onClick={runDisconnect}>Disconnect</CodexButton>
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteButtonGridSingle">
                <CodexButton onClick={runConnectionTest}>Check Server</CodexButton>
              </div>
            </PanelSectionRow>
            {connectionMessage && (
              <PanelSectionRow>
                <div className="codexRemoteMessage">{connectionMessage}</div>
              </PanelSectionRow>
            )}
            <PanelSectionRow>
              <div className="codexRemoteButtonGrid">
                <CodexButton onClick={runChatGptLogin}>ChatGPT</CodexButton>
                <CodexButton onClick={runGetAccount}>Account</CodexButton>
              </div>
            </PanelSectionRow>
            {login?.verificationUrl && login?.userCode && (
              <PanelSectionRow>
                <div className="codexRemoteApproval">
                  <div>Open URL and enter code.</div>
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
          <div className="codexRemoteCompact">
            <div className="codexRemoteThread">
              <span className={`codexRemoteDot ${statusClass[state.status]}`} />
              <span className="codexRemoteRow">{state.thread}</span>
              <span className="codexRemoteMuted">{statusLabel[state.status]}</span>
            </div>
            <div className="codexRemoteTask">
              <div className="codexRemoteMuted">Current task</div>
              <div>{state.task}</div>
            </div>
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

        {state.approvalText && (
          <>
            <PanelSectionRow>
              <div className="codexRemoteButtonGridSingle">
                <CodexButton onClick={() => runAction("approve")}>Approve</CodexButton>
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteButtonGridSingle">
                <CodexButton onClick={() => runAction("deny")}>Deny</CodexButton>
              </div>
            </PanelSectionRow>
          </>
        )}

        <PanelSectionRow>
          <div className="codexRemoteTextArea">
            <TextField
              label="Message"
              value={reply}
              onChange={(event) => setReply(event.target.value)}
            />
          </div>
        </PanelSectionRow>
        <PanelSectionRow>
          <div className="codexRemoteButtonGridSingle">
            <CodexButton onClick={() => runAction("reply", reply)} disabled={!reply.trim()}>
              Send
            </CodexButton>
          </div>
        </PanelSectionRow>
        {state.status === "working" && (
          <PanelSectionRow>
            <div className="codexRemoteButtonGridSingle">
              <CodexButton onClick={() => runAction("pause")}>Pause</CodexButton>
            </div>
          </PanelSectionRow>
        )}
        {actionMessage && (
          <PanelSectionRow>
            <div className="codexRemoteMessage">{actionMessage}</div>
          </PanelSectionRow>
        )}
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
    icon: <FaTerminal />,
  };
});
