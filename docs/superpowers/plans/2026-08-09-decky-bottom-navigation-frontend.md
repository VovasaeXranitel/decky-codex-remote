# Decky Bottom Navigation Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Codex Remote frontend view dropdown with the approved bottom-navigation UX while keeping backend behavior unchanged.

**Architecture:** Keep the implementation in `src/index.tsx` for this frontend pass, matching the existing single-file Decky plugin pattern. Reuse current callable backend APIs, current state types, and current transcript/chat components; only reorganize view state, layout, and CSS. The bottom nav becomes the only page navigation surface and stays visible across `Remote`, `Chats`, `Auth`, `Setup`, and `Log`.

**Tech Stack:** React 19, TypeScript, `@decky/api`, `@decky/ui`, CSS-in-JS string in `src/index.tsx`, existing Python backend untouched.

## Global Constraints

- Frontend only for this pass; do not modify `main.py` or `codex_app_client.py`.
- Use Decky-native components where practical: `PanelSection`, `PanelSectionRow`, `TextField`, `ToggleField`, and `Focusable`.
- Use compact custom controls only where native Decky controls are too tall for the Quick Access panel.
- Keep button spacing at least 6px.
- Do not use large bright buttons.
- Do not use negative letter spacing.
- Keep bottom navigation visible on every page.
- Preserve existing backend callables and persisted settings shape.
- Do not expose or log the App Server token.

---

## File Structure

- Modify `src/index.tsx`: all React layout, view state, bottom nav, compact controls, and CSS.
- Modify `package.json`: bump patch version after frontend changes.
- Modify `CHANGELOG.md`: document bottom navigation frontend release.
- Modify `RELEASE_NOTES.md`: prepare release notes for the frontend release.
- Do not modify backend files in this plan.

---

### Task 1: Replace View Dropdown With Bottom Navigation Shell

**Files:**
- Modify: `src/index.tsx`

**Interfaces:**
- Consumes: existing `PageId = "remote" | "chats" | "auth" | "settings" | "activity"`.
- Produces: `BottomNav` component with props `{ page: PageId; setPage: (page: PageId) => void; items: NavItem[] }`.

- [ ] **Step 1: Add navigation item type and labels**

In `src/index.tsx`, near `type PageId`, add:

```tsx
type NavItem = {
  id: PageId;
  label: string;
};

const navItems: NavItem[] = [
  { id: "remote", label: "Remote" },
  { id: "chats", label: "Chats" },
  { id: "auth", label: "Auth" },
  { id: "settings", label: "Setup" },
  { id: "activity", label: "Log" },
];
```

- [ ] **Step 2: Add `BottomNav` component**

Add below `CodexButton`:

```tsx
type BottomNavProps = {
  page: PageId;
  setPage: (page: PageId) => void;
  items: NavItem[];
};

const BottomNav: FC<BottomNavProps> = ({ page, setPage, items }) => (
  <Focusable className="codexRemoteBottomNav" flow-children="row" tabIndex={0}>
    {items.map((item) => {
      const active = page === item.id;
      const activate = () => setPage(item.id);
      return (
        <Focusable
          key={item.id}
          className={`codexRemoteBottomNavItem${active ? " codexRemoteBottomNavItemActive" : ""}`}
          focusClassName="codexRemoteBottomNavItemFocus"
          onActivate={activate}
          onClick={activate}
          onOKButton={activate}
          role="button"
          tabIndex={0}
        >
          {item.label}
        </Focusable>
      );
    })}
  </Focusable>
);
```

- [ ] **Step 3: Remove DropdownItem view selector**

Remove `DropdownItem` from the `@decky/ui` import and remove the `PanelSectionRow` that renders:

```tsx
<DropdownItem
  label="View"
  menuLabel="Codex Remote view"
  rgOptions={pageOptions}
  selectedOption={page}
  onChange={(option) => setPage(option.data as PageId)}
/>
```

Also remove `pageOptions` and `currentPageTitle`.

- [ ] **Step 4: Use a stable PanelSection title**

Change:

```tsx
<PanelSection title={currentPageTitle}>
```

to:

```tsx
<PanelSection title="Codex Remote">
```

- [ ] **Step 5: Render bottom nav after page content**

At the end of the `PanelSection`, before the action message fallback or immediately before `</PanelSection>`, render:

```tsx
<PanelSectionRow>
  <BottomNav page={page} setPage={setPage} items={navItems} />
</PanelSectionRow>
```

- [ ] **Step 6: Run build**

Run: `pnpm run build`

Expected: build succeeds and `dist/index.js` is regenerated.

---

### Task 2: Add Bottom Navigation CSS and Height Budget

**Files:**
- Modify: `src/index.tsx`

**Interfaces:**
- Consumes: `BottomNav` class names from Task 1.
- Produces: stable bottom nav layout that does not resize between pages.

- [ ] **Step 1: Add bottom nav CSS**

In the `styles` string, add:

```css
.codexRemoteBottomNav {
  background: #0e1218;
  border-top: 1px solid #272d36;
  display: grid;
  gap: 4px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin-top: 4px;
  min-width: 0;
  padding: 8px 0 0;
}

.codexRemoteBottomNavItem {
  align-items: center;
  background: #151a22;
  border: 1px solid #303844;
  border-radius: 4px;
  color: #aeb4bf;
  display: flex;
  font-size: 9px;
  font-weight: 650;
  height: 32px;
  justify-content: center;
  letter-spacing: 0;
  min-width: 0;
  overflow: hidden;
  padding: 0 3px;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.codexRemoteBottomNavItemActive {
  background: #1d232d;
  border-color: #566174;
  color: #f0f2f5;
}

.codexRemoteBottomNavItemFocus,
.codexRemoteBottomNavItem:focus {
  border-color: #8d98a8;
  box-shadow: inset 0 0 0 1px #8d98a8;
  color: #f5f6f8;
}
```

- [ ] **Step 2: Tighten vertical spacing**

Update existing CSS values:

```css
.codexRemoteHeader {
  padding: 0 0 4px;
}

.codexRemotePage {
  gap: 6px;
}

.codexRemoteComposer {
  gap: 7px;
  padding-top: 7px;
}
```

- [ ] **Step 3: Increase Remote transcript budget carefully**

Set:

```css
.codexRemoteScrollFrame {
  max-height: 210px;
  min-height: 170px;
}

.codexRemoteScrollInner {
  max-height: 210px;
  min-height: 170px;
}
```

The bottom nav replaces the dropdown row, so the transcript can recover some height while primary controls remain visible.

- [ ] **Step 4: Run build**

Run: `pnpm run build`

Expected: build succeeds.

---

### Task 3: Make Remote View Match Approved B Content Priority

**Files:**
- Modify: `src/index.tsx`

**Interfaces:**
- Consumes: existing `state`, `transcript`, `quickActions`, `runAction`, `runSelectThread`.
- Produces: Remote page where current chat/status, transcript, approvals, quick actions, composer, and bottom nav are all reachable.

- [ ] **Step 1: Simplify Remote top card**

Replace the Remote chat `PanelSectionRow` body with:

```tsx
<div className="codexRemoteSection">
  <div className="codexRemoteSectionHeader">
    <div>
      <div className="codexRemoteEyebrow">Current chat</div>
      <div className="codexRemoteThread">{state.thread}</div>
    </div>
    <CodexButton compact variant="quiet" onClick={() => setPage("chats")}>Chats</CodexButton>
  </div>
  <div className="codexRemoteTask">{state.task}</div>
</div>
```

- [ ] **Step 2: Keep approvals above transcript**

Ensure the approval block remains between the current chat card and transcript. Keep existing `Approve` and `Deny` actions:

```tsx
<CodexButton compact variant="primary" onClick={() => runAction("approve")}>Approve</CodexButton>
<CodexButton compact variant="danger" onClick={() => runAction("deny")}>Deny</CodexButton>
```

- [ ] **Step 3: Keep composer compact**

Keep the existing compact `<input className="codexRemoteInput" />` and do not revert to Decky `TextField` for the Remote composer.

- [ ] **Step 4: Run build**

Run: `pnpm run build`

Expected: build succeeds.

---

### Task 4: Tune Secondary Views for Bottom Navigation

**Files:**
- Modify: `src/index.tsx`

**Interfaces:**
- Consumes: existing `visibleThreads`, `settings`, `accountInfo`, `login`, `connectionMessage`, `accountMessage`, `state.messages`.
- Produces: Chats/Auth/Setup/Log pages that work with the persistent bottom nav.

- [ ] **Step 1: Remove redundant section titles inside secondary views**

Inside `Chats`, `Auth`, `Setup`, and `Log`, avoid repeating page titles like `Connection` unless they label a row group. Keep labels short:

```tsx
<div className="codexRemoteEyebrow">Current</div>
<div className="codexRemoteEyebrow">Server</div>
<div className="codexRemoteEyebrow">Status</div>
```

- [ ] **Step 2: Keep Chats selection returning to Remote**

Verify `runSelectThread` includes:

```tsx
setPage("remote");
```

- [ ] **Step 3: Keep Auth token-gated**

Verify `Check`, `Login`, `Refresh` in Auth use:

```tsx
disabled={!hasEndpoint || !hasSecureToken}
```

- [ ] **Step 4: Keep Setup actions in two-column grid**

Verify Setup action row remains:

```tsx
<div className="codexRemoteActionGrid">
  <CodexButton compact variant="primary" onClick={runScanLan}>Scan</CodexButton>
  <CodexButton compact variant="primary" onClick={runConnect} disabled={!hasEndpoint || !hasSecureToken}>Link</CodexButton>
  <CodexButton compact variant="quiet" onClick={runConnectionTest}>Check</CodexButton>
  <CodexButton compact variant="quiet" onClick={runDisconnect}>Disconnect</CodexButton>
</div>
```

- [ ] **Step 5: Run build**

Run: `pnpm run build`

Expected: build succeeds.

---

### Task 5: Version, Docs, Package, And Deck Validation

**Files:**
- Modify: `package.json`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Test: Steam Deck install path `/home/deck/homebrew/plugins/CodexRemote`

**Interfaces:**
- Consumes: packaged `build/CodexRemote.zip`.
- Produces: installable frontend release package.

- [ ] **Step 1: Bump package version**

Change `package.json`:

```json
"version": "0.1.29"
```

- [ ] **Step 2: Add changelog entry**

Add to the top of `CHANGELOG.md`:

```markdown
## 0.1.29 - 2026-08-09

Implement approved bottom navigation frontend.

- Replace the view dropdown with persistent bottom navigation.
- Keep Remote focused on current chat, approvals, transcript, quick actions, and composer.
- Preserve Chats, Auth, Setup, and Log as separate compact pages.
- Keep backend behavior unchanged.
```

- [ ] **Step 3: Update release notes**

Set `RELEASE_NOTES.md` heading to:

```markdown
# Codex Remote v0.1.29
```

Use this highlight list:

```markdown
- Replaces the view dropdown with persistent bottom navigation.
- Keeps Remote as the primary control surface.
- Preserves compact Chats, Auth, Setup, and Log pages.
- Leaves backend behavior unchanged for this frontend-only release.
```

- [ ] **Step 4: Build package**

Run: `pnpm run package`

Expected: `build/CodexRemote.zip` exists and `build/CodexRemote/package.json` reports `0.1.29`.

- [ ] **Step 5: Install on Steam Deck**

Use the existing SSH key and install package to `/home/deck/homebrew/plugins/CodexRemote`. Do not print secrets or tokens in logs.

- [ ] **Step 6: Verify Decky service**

Run on Deck:

```bash
systemctl is-active plugin_loader.service
jq -r .version /home/deck/homebrew/plugins/CodexRemote/package.json
PYTHONPYCACHEPREFIX=/tmp/codexremote-pyc python -m py_compile /home/deck/homebrew/plugins/CodexRemote/main.py /home/deck/homebrew/plugins/CodexRemote/codex_app_client.py
```

Expected:

```text
active
0.1.29
```

Python compile exits with code `0`.

- [ ] **Step 7: Check Decky logs**

Run:

```bash
journalctl -u plugin_loader.service -n 160 --no-pager | grep -i -E 'codex remote|codexremote|traceback|exception|error' || true
```

Expected: no Codex Remote traceback or frontend/backend load error.

- [ ] **Step 8: Commit frontend release**

```bash
git add src/index.tsx package.json CHANGELOG.md RELEASE_NOTES.md
git commit -m "Implement bottom navigation frontend"
```

---

## Self-Review

Spec coverage:

- Bottom navigation replaces dropdown: Task 1 and Task 2.
- Remote content priority: Task 3.
- Chats/Auth/Setup/Log retained as separate pages: Task 4.
- Frontend-only constraint: Global Constraints and Task 5 backend exclusion.
- Deck validation: Task 5.

Completion scan:

- No unfinished steps are present.

Type consistency:

- `PageId`, `NavItem`, and `BottomNavProps` are defined before use.
- `setPage("remote")` uses an existing `PageId` value.
- Existing backend callables and state types are reused unchanged.
