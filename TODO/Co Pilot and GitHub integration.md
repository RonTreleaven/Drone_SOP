# Co Pilot and GitHub integration

Use this simple control model:

1. Define mode at the start of each prompt: Plan only, Plan plus one action, or Full execute.
2. Require an effort estimate first: small, medium, large.
3. Set a hard budget per turn: max tool calls and max file edits.
4. Use a run keyword: only execute when you say run now.
5. Use a stop keyword: pause immediately when you say hold.
6. Prefer one objective per prompt, not bundled requests.
7. Ask for decision points before expensive work: scan codebase, run tests, or regenerate large files.
8. End every run with a short receipt: what changed, what was skipped, and what remains.

Important reassurance: Copilot chat does not ask for your credit card mid-session. Billing and limits are managed at the account or org level in GitHub settings, not inside this conversation.

If you want, I can follow this exact operating contract from now on and keep every response in that format.



============================

## Practical usage guidance:

1. Use subagents for targeted research or codebase scanning when you want less main-thread noise.
2. Ask for quick, medium, or thorough scope to control token usage.
3. Prefer one clear objective per subagent run.
4. Require a short result format: findings, risks, next step.
5. Use your own gate phrase like run now before any subagent/tool execution.







# plan first

Mode: plan first
Budget: small
Tools: do not use unless I say "run now"
Edits: do not make unless I say "edit now"
Format: direct answer first, then <=10 bullets, then wait
Task: ...








## **Settings To Review**
These are the VS Code/Copilot areas most worth checking for control and cost awareness:

1. `Copilot Chat` model selection
2. `Agent` vs `Ask` style behavior
3. Tool permissions for terminal, edits, web, notebooks
4. Context sources: open files, selection, workspace, terminal
5. Session/history behavior
6. Custom instructions and workspace instructions
7. Extensions and whether they add extra AI features
8. Settings Sync categories so both machines behave consistently

**Two-Machine Rule**
For your setup, keep this split:

1. VS Code `User` settings for personal editor behavior
2. Workspace settings and repo files for project behavior
3. Sync enabled on both machines only after you’re happy with the current machine’s setup

**Best Next Review**
If you’re looking through settings now, the most useful order is:

1. `Profiles`
2. `Settings Sync`
3. `Copilot`
4. `Copilot Chat`
5. `Extensions`

If you want, next I can do a no-tools walkthrough of the specific `User` vs `Workspace` settings you should care about most for Copilot and agent control.