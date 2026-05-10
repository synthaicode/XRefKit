# Security Policy

## Secret Handling

XRefKit must not contain API keys, access tokens, passwords, private certificates, or `.env` files.

Users should never paste provider API keys into:

- prompts
- issues
- pull requests
- Skill definitions
- knowledge files
- work logs
- agent startup files

## AI Agent Safety

XRefKit is designed to be used with AI agents, but AI agent execution is outside the repository trust boundary.

Before running Claude Code, Codex, GitHub Copilot, or any other agent in this repository, users should review:

- agent startup files
- project-level settings
- hooks
- MCP/tool definitions
- shell commands
- network-related configuration

## Network Behavior

XRefKit should document any component that performs outbound network access.

If a command, Skill, or tool requires network access, it must state:

- what endpoint is contacted
- what data is sent
- whether secrets are required
- how the user can disable or inspect the behavior

## Reporting

If you find a possible credential leak, malicious configuration, unsafe agent instruction, or secret-handling issue, please report it as a security issue.
