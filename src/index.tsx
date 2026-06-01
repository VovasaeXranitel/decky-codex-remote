import {
  callable,
  definePlugin,
  toaster,
} from "@decky/api";
import {
  DropdownItem,
  Focusable,
  PanelSection,
  PanelSectionRow,
  ScrollPanel,
  ScrollPanelGroup,
  TextField,
  ToggleField,
} from "@decky/ui";
import { FC, ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { FaTerminal } from "react-icons/fa";

type CodexState = {
  status: "disconnected" | "idle" | "working" | "approval";
  thread: string;
  threadId: string;
  threads: CodexThread[];
  task: string;
  approvalText?: string;
  command?: string;
  transcript: TranscriptItem[];
  messages: string[];
};

type TranscriptKind =
  | "assistant"
  | "approval"
  | "command"
  | "error"
  | "event"
  | "file"
  | "plan"
  | "reasoning"
  | "system"
  | "tool"
  | "user";

type TranscriptItem = {
  id: string;
  kind: TranscriptKind;
  title: string;
  body: string;
  status?: string;
};

type CodexThread = {
  id: string;
  title: string;
  status: CodexState["status"];
  active: boolean;
  loaded: boolean;
  updatedAt?: number;
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

type PageId = "remote" | "chats" | "auth" | "settings" | "activity";

const defaultState: CodexState = {
  status: "disconnected",
  thread: "Decky remote",
  threadId: "",
  threads: [],
  task: "Not connected",
  transcript: [
    {
      id: "setup",
      kind: "system",
      title: "Setup",
      body: "Open Setup, scan LAN, then connect.",
      status: "",
    },
  ],
  messages: ["Open Setup, scan LAN, then connect."],
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
const selectThread = callable<[string], CodexState>("select_thread");
const testConnection = callable<[], ConnectionCheck>("test_connection");
const connectServer = callable<[], ConnectionCheck>("connect");
const disconnectServer = callable<[], ConnectionCheck>("disconnect");
const scanLan = callable<[], ScanResult>("scan_lan");
const getAccount = callable<[], AccountInfo>("get_account");
const startChatGptLogin = callable<[], ChatGptLogin>("start_chatgpt_login");

const statusLabel: Record<CodexState["status"], string> = {
  approval: "Needs approval",
  disconnected: "Offline",
  idle: "Idle",
  working: "Working",
};

const statusClass: Record<CodexState["status"], string> = {
  approval: "codexRemoteToneApproval",
  disconnected: "codexRemoteToneOffline",
  idle: "codexRemoteToneIdle",
  working: "codexRemoteToneWorking",
};

const transcriptLabel: Record<TranscriptKind, string> = {
  approval: "Approval",
  assistant: "Codex",
  command: "Command",
  error: "Error",
  event: "Event",
  file: "Files",
  plan: "Plan",
  reasoning: "Reasoning",
  system: "System",
  tool: "Tool",
  user: "You",
};

const styles = `
.codexRemote {
  color: #d9d9dc;
}

.codexRemoteHeader {
  align-items: flex-start;
  display: flex;
  gap: 10px;
  justify-content: space-between;
  padding: 2px 0 6px;
}

.codexRemoteTitle,
.codexRemotePluginTitle {
  color: #f4f4f5;
  font-size: 14px;
  font-weight: 650;
  letter-spacing: 0;
}

.codexRemoteEndpoint,
.codexRemoteMuted,
.codexRemoteEyebrow {
  color: #9297a1;
  font-size: 11px;
  letter-spacing: 0;
}

.codexRemoteEndpoint {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  max-width: 188px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteStatusPill {
  align-items: center;
  background: #151922;
  border: 1px solid #2e3541;
  border-radius: 999px;
  color: #d9d9dc;
  display: inline-flex;
  flex: 0 0 auto;
  font-size: 11px;
  gap: 6px;
  line-height: 1;
  min-height: 23px;
  padding: 0 9px;
}

.codexRemoteHeaderActions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 6px;
}

.codexRemotePage {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.codexRemoteDot {
  border-radius: 50%;
  display: inline-block;
  flex: 0 0 auto;
  height: 7px;
  width: 7px;
}

.codexRemoteToneApproval {
  background: #d0c7a1;
}

.codexRemoteToneIdle {
  background: #8d93a0;
}

.codexRemoteToneOffline {
  background: #5e6570;
}

.codexRemoteToneWorking {
  background: #65b97b;
}

.codexRemoteToolbar,
.codexRemoteActionGrid,
.codexRemoteActionGridSingle {
  display: grid;
  column-gap: 8px;
  row-gap: 8px;
  min-width: 0;
}

.codexRemoteToolbar,
.codexRemoteActionGrid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.codexRemoteActionGridSingle {
  grid-template-columns: 1fr;
}

.codexRemoteQuickGrid {
  display: grid;
  gap: 7px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  min-width: 0;
}

.codexRemoteComposer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
}

.codexRemoteButton {
  align-items: center;
  background: #171b22;
  border: 1px solid #303744;
  border-radius: 4px;
  color: #d7dae0;
  display: flex;
  font-size: 12px;
  font-weight: 550;
  justify-content: center;
  height: 32px !important;
  letter-spacing: 0;
  line-height: 1.15;
  max-width: 100%;
  min-height: 32px !important;
  min-width: 0;
  padding: 5px 8px;
  text-align: center;
  width: auto !important;
}

.codexRemoteHeaderActions .codexRemoteButton {
  min-width: 58px;
}

.codexRemoteButtonCompact {
  font-size: 11px;
  height: 28px !important;
  min-height: 28px !important;
  padding: 4px 7px;
}

.codexRemoteButtonPrimary {
  background: #232a35;
  border-color: #4c5668;
  color: #f0f2f5;
}

.codexRemoteButtonQuiet {
  background: #11151c;
  border-color: #262c36;
  color: #bfc3cb;
}

.codexRemoteButtonDanger {
  background: #241a1d;
  border-color: #57313a;
  color: #f0d6dc;
}

.codexRemoteButton:active {
  background: #242b36;
  border-color: #536073;
}

.codexRemoteButtonFocus,
.codexRemoteButton:focus {
  background: #29313e;
  border-color: #8d98a8;
  box-shadow: inset 0 0 0 1px #8d98a8;
  color: #f5f6f8;
}

.codexRemoteButtonDisabled {
  color: #707783;
  opacity: 0.55;
}

.codexRemoteWork {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 8px;
}

.codexRemoteSection {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.codexRemoteSectionHeader {
  align-items: center;
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-bottom: 7px;
}

.codexRemoteChatSearch {
  margin-bottom: 8px;
}

.codexRemoteChatList {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.codexRemoteChatItem {
  align-items: center;
  background: #141820;
  border: 1px solid #2b323d;
  border-radius: 5px;
  color: #d9d9dc;
  display: flex;
  gap: 8px;
  min-height: 38px;
  min-width: 0;
  padding: 7px 9px;
}

.codexRemoteChatMeta {
  color: #8d93a0;
  flex: 0 0 auto;
  font-size: 10px;
  margin-left: auto;
}

.codexRemoteChatItemActive {
  background: #1d232d;
  border-color: #596477;
}

.codexRemoteChatItemFocus,
.codexRemoteChatItem:focus {
  border-color: #8d98a8;
  box-shadow: inset 0 0 0 1px #8d98a8;
}

.codexRemoteChatTitle {
  color: #eeeeef;
  font-size: 12px;
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteThreadLine {
  align-items: center;
  display: flex;
  gap: 8px;
  min-height: 22px;
  overflow: hidden;
}

.codexRemoteThread {
  color: #f0f0f1;
  font-size: 13px;
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteTask {
  color: #e6e6e8;
  font-size: 12px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}

.codexRemoteLog {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 2px;
}

.codexRemoteScrollFrame {
  border: 1px solid #222934;
  border-radius: 5px;
  max-height: 150px;
  min-height: 128px;
  overflow: hidden;
}

.codexRemoteScrollInner {
  max-height: 150px;
  min-height: 128px;
  overflow-y: auto;
  padding: 6px;
  scroll-padding: 14px 0;
  scrollbar-width: thin;
}

.codexRemoteScrollInner::-webkit-scrollbar {
  width: 5px;
}

.codexRemoteScrollInner::-webkit-scrollbar-track {
  background: #11151c;
}

.codexRemoteScrollInner::-webkit-scrollbar-thumb {
  background: #3a4250;
  border-radius: 999px;
}

.codexRemoteMessage {
  color: #d7d7da;
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.codexRemoteMessageDim {
  color: #9ba0aa;
}

.codexRemoteTranscriptHeader {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 7px;
}

.codexRemoteTranscriptCount {
  color: #707783;
  font-size: 10px;
}

.codexRemoteTranscriptItem {
  background: #12161d;
  border: 1px solid #252c36;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 8px;
}

.codexRemoteTranscriptItemFocus,
.codexRemoteTranscriptItem:focus {
  border-color: #8d98a8;
  box-shadow: inset 0 0 0 1px #8d98a8;
}

.codexRemoteTranscriptAssistant {
  background: #151922;
  border-color: #2d3440;
}

.codexRemoteTranscriptUser {
  background: #18202a;
  border-color: #384354;
}

.codexRemoteTranscriptCommand,
.codexRemoteTranscriptTool {
  background: #10141a;
  border-color: #333b48;
}

.codexRemoteTranscriptError {
  background: #21171a;
  border-color: #57313a;
}

.codexRemoteTranscriptApproval {
  background: #1b1a15;
  border-color: #5d563c;
}

.codexRemoteTranscriptTop {
  align-items: center;
  display: flex;
  gap: 7px;
  justify-content: space-between;
  min-width: 0;
}

.codexRemoteTranscriptTitle {
  color: #f0f0f1;
  font-size: 11px;
  font-weight: 650;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteTranscriptStatus {
  background: #1b2029;
  border: 1px solid #333b48;
  border-radius: 999px;
  color: #aeb4bf;
  flex: 0 0 auto;
  font-size: 9px;
  line-height: 1;
  max-width: 98px;
  overflow: hidden;
  padding: 4px 6px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteTranscriptBody {
  color: #d7d7da;
  font-size: 12px;
  line-height: 1.36;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.codexRemoteTranscriptCode {
  color: #cfd3db;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  line-height: 1.35;
}

.codexRemoteApproval {
  background: #151922;
  border: 1px solid #3a4250;
  border-left: 3px solid #d0c7a1;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 9px;
}

.codexRemoteApprovalTop {
  align-items: center;
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.codexRemoteApprovalTitle {
  color: #f0f0f1;
  font-size: 12px;
  font-weight: 650;
}

.codexRemoteApprovalActions {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.codexRemoteSetup {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 7px;
  padding-bottom: 7px;
}

.codexRemoteSetupHeader {
  align-items: center;
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.codexRemoteSetupTitle {
  color: #f0f0f1;
  font-size: 12px;
  font-weight: 650;
}

.codexRemoteInfoLine {
  align-items: center;
  background: #12161d;
  border: 1px solid #2d3440;
  border-radius: 5px;
  display: flex;
  gap: 8px;
  justify-content: space-between;
  min-height: 34px;
  padding: 7px 9px;
}

.codexRemoteInfoValue {
  color: #e3e5e9;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  min-width: 0;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteSetupNotice {
  background: #151922;
  border: 1px solid #3a4250;
  border-left: 3px solid #d0c7a1;
  border-radius: 5px;
  color: #c7cbd3;
  font-size: 11px;
  line-height: 1.35;
  padding: 8px 9px;
}

.codexRemoteAccount {
  background: #12161d;
  border: 1px solid #2d3440;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 9px;
}

.codexRemoteAccountBadge {
  background: #1d232d;
  border: 1px solid #3b4452;
  border-radius: 999px;
  color: #c9ced7;
  flex: 0 0 auto;
  font-size: 10px;
  line-height: 1;
  max-width: 90px;
  overflow: hidden;
  padding: 4px 7px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteApproval code,
.codexRemoteAccount code,
.codexRemoteCode {
  background: #0f1218;
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

.codexRemoteApproval .codexRemoteMessage {
  max-height: none;
}

.codexRemoteTextArea input {
  background: #171b22 !important;
  border: 1px solid #303744 !important;
  box-shadow: none !important;
  color: #d7dae0 !important;
  height: 42px !important;
  min-height: 42px !important;
}

.codexRemoteInput {
  background: #171b22;
  border: 1px solid #303744;
  border-radius: 4px;
  box-sizing: border-box;
  color: #d7dae0;
  font-size: 12px;
  height: 36px;
  min-width: 0;
  outline: none;
  padding: 0 9px;
  width: 100%;
}

.codexRemoteInput:focus {
  border-color: #8d98a8;
  box-shadow: inset 0 0 0 1px #8d98a8;
}

.codexRemoteTextArea .DialogInput,
.codexRemoteTextArea input.DialogInput,
.codexRemoteTextArea .DialogInput:focus {
  background: #171b22 !important;
  border: 1px solid #303744 !important;
  box-shadow: none !important;
  color: #d7dae0 !important;
  height: 42px !important;
  min-height: 42px !important;
}

.codexRemoteTextArea .DialogLabel {
  color: #9297a1 !important;
}

.codexRemoteChatSearch input,
.codexRemoteChatSearch .DialogInput {
  background: #12161d !important;
  border: 1px solid #2b323d !important;
  box-shadow: none !important;
  color: #d7dae0 !important;
  min-height: 34px !important;
}
`;

type CodexButtonProps = {
  children: ReactNode;
  disabled?: boolean;
  compact?: boolean;
  variant?: "default" | "primary" | "quiet" | "danger";
  onClick: () => void;
};

const CodexButton: FC<CodexButtonProps> = ({
  children,
  compact = false,
  disabled = false,
  variant = "default",
  onClick,
}) => {
  const activate = () => {
    if (!disabled) {
      onClick();
    }
  };

  const variantClass =
    variant === "primary"
      ? " codexRemoteButtonPrimary"
      : variant === "quiet"
        ? " codexRemoteButtonQuiet"
        : variant === "danger"
          ? " codexRemoteButtonDanger"
          : "";

  return (
    <Focusable
      className={`codexRemoteButton${compact ? " codexRemoteButtonCompact" : ""}${variantClass}${disabled ? " codexRemoteButtonDisabled" : ""}`}
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

type ChatItemProps = {
  thread: CodexThread;
  onSelect: () => void;
};

const ChatItem: FC<ChatItemProps> = ({ thread, onSelect }) => {
  const activate = () => onSelect();

  return (
    <Focusable
      className={`codexRemoteChatItem${thread.active ? " codexRemoteChatItemActive" : ""}`}
      focusClassName="codexRemoteChatItemFocus"
      onActivate={activate}
      onClick={activate}
      onOKButton={activate}
      role="button"
      tabIndex={0}
    >
      <span className={`codexRemoteDot ${statusClass[thread.status] || statusClass.idle}`} />
      <span className="codexRemoteChatTitle">{thread.title}</span>
      {thread.loaded && <span className="codexRemoteChatMeta">loaded</span>}
    </Focusable>
  );
};

type TranscriptCardProps = {
  item: TranscriptItem;
};

const TranscriptCard: FC<TranscriptCardProps> = ({ item }) => {
  const kindClass = `codexRemoteTranscript${item.kind.charAt(0).toUpperCase()}${item.kind.slice(1)}`;
  const title = item.title || transcriptLabel[item.kind] || "Event";
  const isCodeLike = item.kind === "command" || item.kind === "tool" || item.kind === "file";

  return (
    <Focusable
      className={`codexRemoteTranscriptItem ${kindClass}`}
      focusClassName="codexRemoteTranscriptItemFocus"
      onGamepadFocus={(event) => {
        (event.currentTarget as HTMLElement).scrollIntoView({ block: "nearest", behavior: "smooth" });
      }}
      onFocus={(event) => {
        (event.currentTarget as HTMLElement).scrollIntoView({ block: "nearest", behavior: "smooth" });
      }}
      role="article"
      tabIndex={0}
    >
      <div className="codexRemoteTranscriptTop">
        <div className="codexRemoteTranscriptTitle">{title}</div>
        {item.status && <div className="codexRemoteTranscriptStatus">{item.status}</div>}
      </div>
      {item.body && (
        <div className={`codexRemoteTranscriptBody${isCodeLike ? " codexRemoteTranscriptCode" : ""}`}>
          {item.body}
        </div>
      )}
    </Focusable>
  );
};

const CodexRemotePanel: FC = () => {
  const [state, setState] = useState<CodexState>(defaultState);
  const [settings, setLocalSettings] = useState<Settings>(defaultSettings);
  const [page, setPage] = useState<PageId>("remote");
  const [reply, setReply] = useState("");
  const [chatQuery, setChatQuery] = useState("");
  const [connectionMessage, setConnectionMessage] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [devices, setDevices] = useState<DiscoveredDevice[]>([]);
  const [accountMessage, setAccountMessage] = useState("");
  const [accountInfo, setAccountInfo] = useState<AccountInfo | null>(null);
  const [login, setLogin] = useState<ChatGptLogin | null>(null);
  const transcriptElementRef = useRef<HTMLDivElement | null>(null);

  const endpoint = useMemo(
    () => (settings.host ? `ws://${settings.host}:${settings.port}` : "not configured"),
    [settings.host, settings.port],
  );
  const hasEndpoint = Boolean(settings.host.trim() && settings.port.trim());
  const hasSecureToken = Boolean(settings.token.trim());
  const pages: { id: PageId; label: string }[] = [
    { id: "remote", label: "Remote" },
    { id: "chats", label: "Chats" },
    { id: "auth", label: "Auth" },
    { id: "settings", label: "Setup" },
    { id: "activity", label: "Log" },
  ];
  const pageOptions = pages.map((item) => ({ data: item.id, label: item.label }));
  const currentPageTitle = pages.find((item) => item.id === page)?.label || "Remote";
  const normalizedChatQuery = chatQuery.trim().toLowerCase();
  const visibleThreads = state.threads
    .filter((thread) => !normalizedChatQuery || thread.title.toLowerCase().includes(normalizedChatQuery))
    .slice(0, 8);
  const quickActions = [
    { label: "Continue", prompt: "Continue from the current task. Keep going without asking for more unless you are blocked." },
    { label: "Explain", prompt: "Explain what you are doing now and what the next step is." },
    { label: "Retry", prompt: "Retry the last failed step. If it needs a different approach, choose it and continue." },
    { label: "Summary", prompt: "Summarize the current progress, open risks, and the next concrete action." },
  ];
  const transcript = state.transcript?.length
    ? state.transcript
    : state.messages.map((message, index) => ({
        id: `message-${index}`,
        kind: "event" as TranscriptKind,
        title: "Activity",
        body: message,
        status: "",
      }));
  const transcriptTailKey = transcript.length
    ? `${transcript[transcript.length - 1].id}:${transcript[transcript.length - 1].body.length}:${transcript.length}`
    : "empty";

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
      .then((nextSettings) => {
        const loadedSettings = { ...defaultSettings, ...nextSettings };
        setLocalSettings(loadedSettings);
        if (!loadedSettings.host) {
          setPage("settings");
        }
      })
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

  useEffect(() => {
    const element = transcriptElementRef.current;
    if (!element) {
      return;
    }
    window.requestAnimationFrame(() => {
      element.scrollTop = element.scrollHeight;
    });
  }, [transcriptTailKey]);

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
      setAccountInfo(result);
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
      if (result.ok) {
        setAccountInfo(null);
      }
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

  const runSelectThread = async (threadId: string) => {
    try {
      const nextState = await selectThread(threadId);
      setState(nextState);
      setPage("remote");
      setActionMessage("");
    } catch (error) {
      console.warn("[Codex Remote] Select chat failed", error);
      setActionMessage("Chat switch failed.");
    }
  };

  return (
    <div className="codexRemote">
      <style>{styles}</style>
      <PanelSection title={currentPageTitle}>
        <div className="codexRemoteHeader">
          <div>
            <div className="codexRemoteTitle">Codex</div>
            <div className="codexRemoteEndpoint">{endpoint}</div>
            <div className="codexRemoteHeaderActions">
              <CodexButton compact variant="quiet" onClick={refreshState}>Sync</CodexButton>
            </div>
          </div>
          <div className="codexRemoteStatusPill">
            <span className={`codexRemoteDot ${statusClass[state.status]}`} />
            {statusLabel[state.status]}
          </div>
        </div>

        <PanelSectionRow>
          <DropdownItem
            label="View"
            menuLabel="Codex Remote view"
            rgOptions={pageOptions}
            selectedOption={page}
            onChange={(option) => setPage(option.data as PageId)}
          />
        </PanelSectionRow>

        {page === "remote" && (
          <div className="codexRemotePage">
            <PanelSectionRow>
              <div className="codexRemoteSection">
                <div className="codexRemoteSectionHeader">
                  <div>
                    <div className="codexRemoteEyebrow">Chat</div>
                    <div className="codexRemoteThread">{state.thread}</div>
                  </div>
                  <CodexButton compact variant="quiet" onClick={() => setPage("chats")}>Change</CodexButton>
                </div>
              </div>
            </PanelSectionRow>

            <PanelSectionRow>
              <div className="codexRemoteWork">
                <div>
                  <div className="codexRemoteEyebrow">Current task</div>
                  <div className="codexRemoteTask">{state.task}</div>
                </div>
              </div>
            </PanelSectionRow>

            {state.approvalText && (
              <PanelSectionRow>
                <div className="codexRemoteApproval">
                  <div className="codexRemoteApprovalTop">
                    <div>
                      <div className="codexRemoteEyebrow">Action needed</div>
                      <div className="codexRemoteApprovalTitle">Approval request</div>
                    </div>
                    <span className={`codexRemoteDot ${statusClass.approval}`} />
                  </div>
                  <div className="codexRemoteMessage">{state.approvalText}</div>
                  {state.command && <code>{state.command}</code>}
                  <div className="codexRemoteApprovalActions">
                    <CodexButton compact variant="primary" onClick={() => runAction("approve")}>Approve</CodexButton>
                    <CodexButton compact variant="danger" onClick={() => runAction("deny")}>Deny</CodexButton>
                  </div>
                </div>
              </PanelSectionRow>
            )}

            <PanelSectionRow>
              <div>
                <div className="codexRemoteTranscriptHeader">
                  <div className="codexRemoteEyebrow">Transcript</div>
                  <div className="codexRemoteTranscriptCount">{transcript.length}</div>
                </div>
                <div className="codexRemoteScrollFrame">
                  <ScrollPanelGroup>
                    <ScrollPanel>
                      <Focusable className="codexRemoteScrollInner" flow-children="column" tabIndex={0}>
                        <div
                          className="codexRemoteLog"
                          onWheel={(event) => {
                            transcriptElementRef.current?.scrollBy({ top: event.deltaY });
                          }}
                          ref={transcriptElementRef}
                        >
                          {transcript.map((item, index) => (
                            <TranscriptCard item={item} key={`${item.id}-${index}`} />
                          ))}
                        </div>
                      </Focusable>
                    </ScrollPanel>
                  </ScrollPanelGroup>
                </div>
              </div>
            </PanelSectionRow>

            <PanelSectionRow>
              <div className="codexRemoteComposer">
                <div className="codexRemoteQuickGrid">
                  {quickActions.map((action) => (
                    <CodexButton
                      key={action.label}
                      compact
                      variant="quiet"
                      onClick={() => runAction("reply", action.prompt)}
                      disabled={state.status === "disconnected" || !state.threadId}
                    >
                      {action.label}
                    </CodexButton>
                  ))}
                </div>
                <input
                  aria-label="Message"
                  className="codexRemoteInput"
                  placeholder="Message"
                  value={reply}
                  onChange={(event) => setReply(event.target.value)}
                />
                <div className="codexRemoteActionGrid">
                  <CodexButton compact variant="primary" onClick={() => runAction("reply", reply)} disabled={!reply.trim()}>
                    Send
                  </CodexButton>
                  <CodexButton
                    compact
                    variant="quiet"
                    onClick={() => runAction("pause")}
                    disabled={state.status !== "working"}
                  >
                    Pause
                  </CodexButton>
                </div>
              </div>
            </PanelSectionRow>
          </div>
        )}

        {page === "chats" && (
          <div className="codexRemotePage">
            <PanelSectionRow>
              <div className="codexRemoteSection">
                <div className="codexRemoteSectionHeader">
                  <div>
                    <div className="codexRemoteEyebrow">Current</div>
                    <div className="codexRemoteThread">{state.thread}</div>
                  </div>
                  <CodexButton compact variant="quiet" onClick={refreshState}>Refresh</CodexButton>
                </div>
                <div className="codexRemoteChatSearch">
                  <TextField
                    label="Find chat"
                    value={chatQuery}
                    onChange={(event) => setChatQuery(event.target.value)}
                  />
                </div>
                <div className="codexRemoteChatList">
                  {visibleThreads.map((thread) => (
                    <ChatItem
                      key={thread.id}
                      thread={thread}
                      onSelect={() => runSelectThread(thread.id)}
                    />
                  ))}
                  {!visibleThreads.length && (
                    <div className="codexRemoteMessage codexRemoteMessageDim">No matching Codex chats.</div>
                  )}
                </div>
              </div>
            </PanelSectionRow>
          </div>
        )}

        {page === "auth" && (
          <div className="codexRemotePage">
            <PanelSectionRow>
              <div className="codexRemoteInfoLine">
                <div>
                  <div className="codexRemoteEyebrow">Server</div>
                  <div className="codexRemoteThread">{hasEndpoint ? "Configured" : "Missing host"}</div>
                </div>
                <div className="codexRemoteInfoValue">{hasSecureToken ? "token set" : "no token"}</div>
              </div>
            </PanelSectionRow>
            {hasEndpoint && !hasSecureToken && (
              <PanelSectionRow>
                <div className="codexRemoteSetupNotice">Paste the App Server token in Setup before checking account state.</div>
              </PanelSectionRow>
            )}
            <PanelSectionRow>
              <div className="codexRemoteActionGrid">
                <CodexButton compact variant="primary" onClick={runGetAccount} disabled={!hasEndpoint || !hasSecureToken}>Check</CodexButton>
                <CodexButton compact variant="quiet" onClick={runChatGptLogin} disabled={!hasEndpoint || !hasSecureToken}>Login</CodexButton>
              </div>
            </PanelSectionRow>
            {(accountInfo?.account || accountInfo?.requiresOpenaiAuth !== undefined || login?.verificationUrl) && (
              <PanelSectionRow>
                <div className="codexRemoteAccount">
                  <div className="codexRemoteApprovalTop">
                    <div>
                      <div className="codexRemoteEyebrow">Account</div>
                      <div className="codexRemoteApprovalTitle">
                        {accountInfo?.account?.email || accountInfo?.account?.type || "ChatGPT sign-in"}
                      </div>
                    </div>
                    {accountInfo?.account?.planType && (
                      <span className="codexRemoteAccountBadge">{accountInfo.account.planType}</span>
                    )}
                  </div>
                  {accountInfo && !accountInfo.account && (
                    <div className="codexRemoteMessage codexRemoteMessageDim">Not signed in on Codex App Server.</div>
                  )}
                  {login?.verificationUrl && login?.userCode && (
                    <>
                      <div className="codexRemoteMessage codexRemoteMessageDim">Open this URL and enter the code.</div>
                      <code>{login.verificationUrl}</code>
                      <code>{login.userCode}</code>
                    </>
                  )}
                  <div className="codexRemoteActionGrid">
                    <CodexButton compact variant="quiet" onClick={runGetAccount} disabled={!hasEndpoint || !hasSecureToken}>Refresh</CodexButton>
                    <CodexButton compact variant="primary" onClick={runChatGptLogin} disabled={!hasEndpoint || !hasSecureToken}>Login</CodexButton>
                  </div>
                </div>
              </PanelSectionRow>
            )}
            {accountMessage && (
              <PanelSectionRow>
                <div className="codexRemoteMessage codexRemoteMessageDim">{accountMessage}</div>
              </PanelSectionRow>
            )}
          </div>
        )}

        {page === "settings" && (
          <div className="codexRemotePage">
            <PanelSectionRow>
              <div className="codexRemoteSetupHeader">
                <div>
                  <div className="codexRemoteSetupTitle">Connection</div>
                  <div className="codexRemoteMuted">{endpoint}</div>
                </div>
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteActionGrid">
                <CodexButton compact variant="primary" onClick={runScanLan}>Scan</CodexButton>
                <CodexButton compact variant="primary" onClick={runConnect} disabled={!hasEndpoint || !hasSecureToken}>Link</CodexButton>
                <CodexButton compact variant="quiet" onClick={runConnectionTest}>Check</CodexButton>
                <CodexButton compact variant="quiet" onClick={runDisconnect}>Disconnect</CodexButton>
              </div>
            </PanelSectionRow>
            {hasEndpoint && !hasSecureToken && (
              <PanelSectionRow>
                <div className="codexRemoteSetupNotice">Paste the App Server token to enable Link and Account.</div>
              </PanelSectionRow>
            )}
            {devices.map((device) => (
              <PanelSectionRow key={`${device.host}:${device.port}`}>
                <div className="codexRemoteActionGridSingle">
                  <CodexButton variant="quiet" onClick={() => selectDevice(device)}>
                    {device.label}
                  </CodexButton>
                </div>
              </PanelSectionRow>
            ))}
            <PanelSectionRow>
              <TextField
                label="Host"
                value={settings.host}
                onChange={(event) => persistSettings({ ...settings, host: event.target.value })}
              />
            </PanelSectionRow>
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
                label="Live updates"
                checked={settings.autoRefresh}
                onChange={(checked) => persistSettings({ ...settings, autoRefresh: checked })}
              />
            </PanelSectionRow>
            {connectionMessage && (
              <PanelSectionRow>
                <div className="codexRemoteMessage codexRemoteMessageDim">{connectionMessage}</div>
              </PanelSectionRow>
            )}
          </div>
        )}

        {page === "activity" && (
          <div className="codexRemotePage">
            <PanelSectionRow>
              <div className="codexRemoteInfoLine">
                <div>
                  <div className="codexRemoteEyebrow">Status</div>
                  <div className="codexRemoteThread">{statusLabel[state.status]}</div>
                </div>
                <div className="codexRemoteInfoValue">{state.messages.length} event(s)</div>
              </div>
            </PanelSectionRow>
            <PanelSectionRow>
              <div className="codexRemoteLog">
                {connectionMessage && <div className="codexRemoteMessage">Connection: {connectionMessage}</div>}
                {accountMessage && <div className="codexRemoteMessage">Account: {accountMessage}</div>}
                {actionMessage && <div className="codexRemoteMessage">Action: {actionMessage}</div>}
                {state.messages.map((message, index) => (
                  <div className="codexRemoteMessage codexRemoteMessageDim" key={`${message}-${index}`}>{message}</div>
                ))}
              </div>
            </PanelSectionRow>
          </div>
        )}

        {actionMessage && page !== "activity" && (
          <PanelSectionRow>
            <div className="codexRemoteMessage codexRemoteMessageDim">{actionMessage}</div>
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
