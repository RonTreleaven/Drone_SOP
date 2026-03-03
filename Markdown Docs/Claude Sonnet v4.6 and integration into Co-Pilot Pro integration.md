# Claude Sonnet v4.6 and integration into Co-Pilot Pro integration



## MCP Documentation 

https://docs.github.com/en/copilot/concepts/context/mcp

Model Context Protocol (MCP) is a protocol that allows you to extend the capabilities of GitHub Copilot by integrating it with other systems.



## [Overview of Model Context Protocol (MCP)](https://docs.github.com/en/copilot/concepts/context/mcp#overview-of-model-context-protocol-mcp)

The Model Context Protocol (MCP) is an open standard that defines how applications share context with large language models (LLMs). MCP provides a standardized way to connect AI models to different data sources and tools, enabling them to work together more effectively.

You can use MCP to extend the capabilities of Copilot Chat by integrating it with a wide range of existing tools and services. For example, the GitHub MCP server allows you to use Copilot Chat in your IDE to perform tasks on GitHub. You can also use MCP to create new tools and services that work with Copilot Chat, allowing you to customize and enhance your experience.

For more information on MCP, see [the official MCP documentation](https://modelcontextprotocol.io/introduction). For information on currently available MCP servers, see [the MCP servers repository](https://github.com/modelcontextprotocol/servers/tree/main).

To learn how to configure and use MCP servers with Copilot Chat, see [Extending GitHub Copilot Chat with Model Context Protocol (MCP) servers](https://docs.github.com/en/copilot/how-tos/context/model-context-protocol/extending-copilot-chat-with-mcp).

Enterprises and organizations can choose to enable or disable use of MCP for members of their organization or enterprise with the **MCP servers in Copilot** policy. The policy is disabled by default. See [Managing policies and features for GitHub Copilot in your enterprise](https://docs.github.com/en/copilot/how-tos/administer/enterprises/managing-policies-and-features-for-copilot-in-your-enterprise) and [Managing policies and features for GitHub Copilot in your organization](https://docs.github.com/en/copilot/how-tos/administer-copilot/manage-for-organization/manage-policies). The MCP policy **only** applies to users who have a Copilot Business or Copilot Enterprise subscription from an organization or enterprise that configures the policy. Copilot Free, Copilot Pro, or Copilot Pro+ **do not** have their MCP access governed by this policy.

## [Availability](https://docs.github.com/en/copilot/concepts/context/mcp#availability)

There is currently broad support for local MCP servers in clients such as Visual Studio Code, JetBrains IDEs, XCode, and others.

Support for remote MCP servers is growing, with editors like Visual Studio Code, Visual Studio, JetBrains IDEs, Xcode, Eclipse, and Cursor providing this functionality with OAuth or PAT, and Windsurf supporting PAT only.

To find out if your preferred editor supports remote MCP servers, check the documentation for your specific editor.

## [About the GitHub MCP server](https://docs.github.com/en/copilot/concepts/context/mcp#about-the-github-mcp-server)

The GitHub MCP server is a Model Context Protocol (MCP) server provided and maintained by GitHub.

GitHub MCP server can be used to:

- Automate and streamline code-related tasks.
- Connect third-party tools (like Cursor, Windsurf, or future integrations) to leverage GitHub’s context and AI capabilities.
- Enable cloud-based workflows that work from any device, without local setup.
- Invoke GitHub tools, such as Copilot coding agent (requires GitHub Copilot subscription) and code scanning (requires GitHub Advanced Security subscription), to assist with code generation and security analysis.

To learn how to set up and use the GitHub MCP server, see [Using the GitHub MCP Server](https://docs.github.com/en/copilot/how-tos/context/model-context-protocol/using-the-github-mcp-server).

### [Remote access](https://docs.github.com/en/copilot/concepts/context/mcp#remote-access)

You can access the GitHub MCP server remotely through Copilot Chat in Visual Studio Code without any local setup. The remote server has access to additional toolsets only available in the remote GitHub MCP server. For a list of such tools, see [Additional toolsets](https://github.com/github/github-mcp-server?tab=readme-ov-file#additional-toolsets-in-remote-github-mcp-server) in the `github/github-mcp-server` repository.

The GitHub MCP server can also run locally in any MCP-compatible editor, if necessary.





# installing the VSC extension



Install it as the **Claude Code VS Code extension** (this is the “workspace” experience), then add MCP servers via CLI.

1. In VS Code, open Extensions (Ctrl+Shift+X), search **Claude Code**, install the official Anthropic extension.

2. Confirm VS Code is **1.98.0+**.

3. Open the Claude panel (spark icon), sign in, and pick Sonnet from the prompt / menu when needed (model switch is built in).

4. Add MCP servers from VS Code terminal:

   `claude mcp add --transport http github https://api.githubcopilot.com/mcp/ `

5. If prompted, run claude then /mcp to authenticate MCP tools.

6. Restart/reload VS Code if the spark panel or MCP tools don’t appear.

Notes:

- You do **not** install a separate “Sonnet library” extension.
- MCP server config is managed via Claude CLI/settings and then used in the extension.

Sources:

- https://code.claude.com/docs/en/ide-integrations
- https://docs.claude.com/en/docs/claude-code/ide-integrations



# Claude Code for VS Code

Unleash Claude’s raw power directly in your terminal. 
Search million-line codebases instantly. 
Turn hours-long workflows into a single command. 
Your tools. Your workflow. 
Your codebase, evolving at thought speed.

- **Powerful intelligence:** Use the latest Claude models using your Pro, Max, Team, or Enterprise subscription, or pay-as-you-go pricing
- **Works alongside you:** Claude autonomously explores your codebase, reads and writes code, and runs Terminal commands with your permission.
- **New, friendlier interface** that makes it easier than ever to get started
- **Integrated with the editor:** Claude knows about your current file and text selection, and proposes changes directly inside your editor window.
- **Powerful agentic features** like subagents, custom slash commands, and MCP are supported. (These features work in the VS Code extension, but some can only be configured using the command-line interface)

## New to Claude Code?

Visit [claude.com/claude-code](https://claude.com/claude-code) to get started with Claude Code.



![Welcome to Claude Code](https://file+.vscode-resource.vscode-cdn.net/c:/Users/Ron Treleaven/.vscode/extensions/anthropic.claude-code-2.1.63-win32-x64/resources/walkthrough/welcome.png)

**Claude Code helps you write, edit, and understand code right in VS Code.**

Claude can read your files, make edits, run terminal commands, and help you navigate complex codebases. It understands context and works alongside you like a knowledgeable teammate.

Prefer a terminal experience? Run **Claude Code: Open in Terminal** from the Command Palette, or enable it permanently in Settings.