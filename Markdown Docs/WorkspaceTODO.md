# @Workspace Review & TODO List

## MAM Mission State Model (2026-04-09)

- Preserve privacy-first behavior: pilot PII stays local to the user's device (no server-side profile storage).
- Reframe mission status into storage/reuse intent, not mission lifecycle wording.
- Proposed model:
   - `Mission Only` (current `Draft`): use values for the current mission flow only.
   - `Workspace Reuse` (current `Active`): persist values for Drone_SOP local reuse (browser localStorage).
   - `Private Local Copy` (candidate replacement for `Closed`): user-managed local file copy for long-term/private control.
- UI follow-up: rename `Mission State` label to something like `Profile Usage Mode`.
- Behavioral follow-up:
   - `Mission Only`: auto-clear or avoid carrying forward selected fields after mission close/reset.
   - `Workspace Reuse`: keep current localStorage behavior for convenience.
   - `Private Local Copy`: add explicit import/export/save-as flow to user-selected local file.
- Data policy follow-up: add a short inline notice near profile controls confirming all profile data is local-only unless the user explicitly exports.
- MAM follow-up: evaluate whether Mission Automation settings should have the same 3-mode policy or remain independently persisted.




@workspace review my DRONE SOP project and suggest improvements to structure, accessibility and code quality



**Findings (by severity)**

1. **High: summary data source mismatch breaks checklist summary/export consistency**
   Index flow now stores selected SOPs in droneSOPProgress.selectedSOPs, but summary rendering in app.js reads selectedSections, which can be empty/stale, causing missing checklist blocks and incomplete CSV/PDF content.
   - [assets/js/app.js:66](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/app.js:244](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
2. **High: duplicate page logic (inline scripts + shared app.js) creates conflicting behavior**
   summary.html and flight-log.html both load assets/js/app.js and also run page-specific inline DOMContentLoaded logic touching the same DOM/localStorage, which risks double handlers and inconsistent UI state.
   - [summary.html:50](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [summary.html:52](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [flight-log.html:103](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [flight-log.html:118](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/app.js:74](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/app.js:212](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
3. **Medium: potential runtime crash when section metadata is missing**
   Summary rendering dereferences section.title without a null guard; if IDs drift, page render/export will throw.
   - [assets/js/app.js:250](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/app.js:292](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
4. **Medium: implicit global dependency (toDMS) in shared JS**
   Shared app.js geolocation handler calls toDMS though it is not defined there; behavior depends on page-local scripts and can fail if reused elsewhere.
   - [assets/js/app.js:375](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [flight-log.html:106](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
5. **Medium (Accessibility): section pages missing viewport meta on most pages**
   12/13 section templates lack <meta name="viewport">, reducing mobile readability/usability.
   - Example template: [sections/1_0_Micro_Pre-Flight.html:5](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
6. **Medium (Accessibility): visually-hidden labels are referenced but class is not defined**
   Form labels rely on .visually-hidden, but no CSS rule exists, so intended SR-only behavior is not implemented consistently.
   - [flight-log.html:58](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/css/style.css](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
7. **Low: CSS quality issues and dead/placeholder code**
   Duplicate selector blocks and an invalid placeholder rule indicate stylesheet drift.
   - [assets/css/style.css:3](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/css/style.css:145](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/css/style.css:305](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
8. **Low (Structure): repository has active code mixed with backups/legacy copies**
   Multiple app variants and backup CSS files increase confusion and regression risk.
   - [assets/js/app.js](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/new_revert_app.js](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/bu_app.js](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
   - [assets/js/app - Copy.js](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)
9. **Low (Content quality): placeholder link shipped in production tools list**
   - [tools.html:112](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)

1. **Low (Consistency): section template title typo/mismatch**

- [sections/1_0_Micro_Pre-Flight.html:5](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/Ron Treleaven/.vscode/extensions/openai.chatgpt-0.4.79-win32-x64/webview/)

**Open questions / assumptions**

- I assumed assets/js/app.js is the canonical script and backup variants are non-production.
- I assumed droneSOPProgress is the intended state model replacing selectedSections.

**Suggested improvements**

1. Consolidate to one state model (droneSOPProgress) and remove selectedSections reads/writes.
2. Move all page logic into modular JS files (no inline handlers), with one DOMContentLoaded entry per page.
3. Add shared accessibility baseline: .visually-hidden, focus-visible styles, semantic button controls instead of href="#" onclick.
4. Normalize section templates (viewport meta + consistent title conventions) using one source template.
5. Reorganize repo into src/, generated/, archive/, and keep backups out of active runtime paths.

No files were changed in this review.