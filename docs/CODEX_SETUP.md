# Reproduce this setup with Codex

This guide connects **your own WhatsApp account** to local Codex and ChatGPT. You do not need the original author's machine, tunnel ID, API key, or plugin. The repository supplies code, not an account or a running cloud service.

## Give Codex this prompt

```text
Read README.md and docs/CODEX_SETUP.md in this repository. Help me connect my own WhatsApp account to both local Codex and ChatGPT using the code here.

Inspect my operating system and existing setup first. Use an isolated checkout if needed. Keep the Go bridge on loopback. Preserve any existing MCP configuration, WhatsApp sessions, and unrelated processes. Use the locked Python dependencies and check that my Go compiler supports go.mod.

Run the synthetic MCP regression tests and build the bridge before claiming that setup works. Guide me through WhatsApp QR pairing and the OpenAI account steps that require my interaction. Never ask me to paste API keys into the conversation. Use bin/connect-chatgpt.py with my own tunnel ID and private terminal input.

Register the local stdio server, retain approval for write tools, and configure a private ChatGPT tunnel. Validate authentication as well as process health; a running process alone is not success. Refresh ChatGPT's tool metadata after schema changes. Test a small read-only query and distinguish successful tool discovery from successful tool execution.

Do not send messages or files unless I explicitly authorize the recipient and exact content. Do not delete databases to solve a routine error. End with confirmed working parts, remaining blockers, and exact operating commands for my machine. Never commit databases, keys, attachments, or logs.
```

## Before installation

Use a trusted computer that can remain awake. The tested environment is macOS on Apple Silicon. Go's SQLite dependency needs CGO and a C compiler. Python requires 3.11 or newer; `uv sync --locked` reproduces the committed environment. Install prerequisites from their official sources. This project does not automatically install system dependencies.

Clone and run the first three steps in [README.md](../README.md#start-here). The QR pairing is performed by you on your phone. A successful pairing is separate from successful history synchronization.

If port 8080 is occupied, identify its owner first. Do not terminate an unrelated process. Keep the bridge and Python client's port settings consistent if you intentionally change them.

## Connect ChatGPT through a private tunnel

The following is the path verified during this project's September 2026 setup. Product labels and eligibility may change; consult the [current connection instructions](https://developers.openai.com/plugins/deploy/connect-chatgpt) and [Secure MCP Tunnel documentation](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

### 1. Install the official tunnel client

Download the archive for your operating system and CPU from [OpenAI's tunnel-client releases](https://github.com/openai/tunnel-client/releases/latest). Compare its SHA-256 checksum with the release's `SHA256SUMS.txt` before running it. Extract the release contents together into `bin/tunnel-runtime/`, or install `tunnel-client` on your PATH. Do not commit the downloaded files.

On macOS, when using the repository directory:

```bash
chmod +x bin/tunnel-runtime/tunnel-client bin/tunnel-runtime/cloudflared
bin/tunnel-runtime/tunnel-client help quickstart
```

The helper prefers `bin/tunnel-runtime/tunnel-client` and otherwise searches PATH. Use the CLI help shipped with your installed version if its flags differ. The verified version was 0.0.14.

### 2. Create your tunnel

Open [Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels). Create a tunnel named **Personal WhatsApp** and associate it with your own Platform organization and the ChatGPT workspace where you will use it. Copy its `tunnel_...` ID.

Tunnel management, tunnel use, and ChatGPT developer mode have separate access controls. The operator creating a tunnel needs Tunnels Read + Manage; the runtime principal needs Read + Use. If access is unavailable, resolve it with the organization/workspace owner instead of making the bridge public.

### 3. Create a dedicated runtime key

In [Platform API keys](https://platform.openai.com/settings/organization/api-keys), create a dedicated key under your own project. Choose **Restricted** permissions and enable **Tunnels Read + Use**. Choose an expiration appropriate for your use; after expiration you must replace the key. Do not use an organization admin key for the background runtime.

Copy the secret only when it is displayed. Enter it in the helper's hidden terminal prompt, not in Codex, ChatGPT, a shell argument, or a committed file.

### 4. Start the managed runtime

From the repository root, substitute your own tunnel ID:

```bash
uv run --project whatsapp-mcp-server --locked python bin/connect-chatgpt.py --tunnel-id tunnel_YOUR_ID
```

The helper derives paths from its own location, rejects obvious duplicated or masked keys, saves the runtime key outside the repository with owner-only permissions, and starts a managed runtime called `whatsapp`. It supports the macOS/POSIX layout documented here; it is not a Windows installer. Use one `whatsapp` alias per host unless you adapt the helper for multiple accounts.

It stores the key at `~/.config/tunnel-client/whatsapp-secrets/runtime-key`. This is a restricted local file, not an encrypted keychain. It does not print the key. The managed runtime is independent of the terminal that launched the helper; automatic restart after reboot is not established by this script.

### 5. Verify the connection

```bash
bin/tunnel-runtime/tunnel-client runtimes status whatsapp
```

Check **process running, healthy, ready, and no remote authentication error**. During this build, a runtime could report local readiness while OpenAI rejected its key, so local readiness alone is insufficient. If startup is still in progress, check status again after it settles.

A failed setup can leave a process running. Stop it before changing credentials or retrying:

```bash
bin/tunnel-runtime/tunnel-client runtimes stop whatsapp
```

Rerun the helper with your tunnel ID to supply a corrected key. Keep the bridge running too.

### 6. Add the connection in ChatGPT

In ChatGPT, enable **Settings → Security and login → Developer mode**, if available to your account. Then open [Plugins](https://chatgpt.com/plugins), choose **Create app**, and configure:

| Field | Value |
| --- | --- |
| Name | Personal WhatsApp |
| Description | Search my WhatsApp chats; send only when explicitly requested |
| Connection | Tunnel |
| Tunnel | Your Personal WhatsApp tunnel |
| Authentication | No Auth |

Here, **No Auth** means that this stdio MCP server does not implement an additional OAuth flow. The tunnel itself still authenticates through OpenAI and its organization/workspace access controls. Never interpret this as permission to expose the unauthenticated REST bridge publicly.

Review and acknowledge the custom-server notice, then create the connection. Add an optional PNG icon during creation if desired; the UI observed during this setup did not offer icon editing afterward. Verify that ChatGPT lists all 12 actions, labels retrieval tools as reads, and recognizes sending as writes. Keep the plugin's approval policy at **Allow low-risk** or stricter rather than allowing all actions.

### 7. Test the actual tools

Start a new conversation with Personal WhatsApp selected:

> List my three most recent WhatsApp chats. Do not send anything.

Then test a bounded date query with an explicit timezone. Successful tool discovery does not prove valid tool results. For a daily brief, request pagination, deduplication, and a coverage statement. Do not infer that an empty result means no activity until the bridge's synchronization and date filter have been checked.

The ChatGPT connection is account/workspace scoped. Availability in a particular mobile app surface should be checked on that device; this repository's validation did not include a separate mobile UI test.

## Keep it running

- Keep the host awake and online. Sleep interrupts the bridge/tunnel workflow.
- `bash bin/start-bridge.sh` runs the bridge in the foreground. For startup at login, ask Codex to generate a LaunchAgent using your absolute repository path, a private log directory, and your installed Go executable. Pair interactively before enabling a background service. Tildes are not expanded in LaunchAgent path values.
- Use `tunnel-client runtimes connect` through the helper for managed tunnel startup; use `runtimes status` to verify it and `runtimes stop whatsapp` to stop it.
- After changing Python code, restart the tunnel runtime. After changing schemas or tool descriptions, also click **Refresh** in the ChatGPT plugin settings and start a new conversation.
- Local Codex's MCP connection has its own restart control. Restarting the tunnel does not automatically reload an existing local Codex process.

## Troubleshooting lessons from this build

| Symptom | Check and fix |
| --- | --- |
| “Malformed results” | Check actual return values against output schemas. Message text is a string; contact/chat results are typed records; missing results can be null. SQLite `0/1` values must become JSON booleans where declared. Run the regression test. |
| Empty metadata-only chat list | Earlier code selected message columns without joining the message table. The included fix returns null metadata and surfaces database errors instead of hiding them as empty activity. |
| MCP protocol parsing failures | Never print diagnostics to stdio's stdout. Keep them on stderr. |
| FastMCP import breaks after upgrading | Keep `mcp>=1.12,<2` and the lockfile. MCP 2.x changes the API; upgrading it needs a deliberate migration. |
| Runtime runs but OpenAI rejects it | Check the remote error, key validity, and permissions. Paste the key exactly once. Never post it for debugging. |
| Tunnel not listed in ChatGPT | Check its workspace association and the account's tunnel-use permission. |
| Port check returns HTTP 404 | `/` is not a health endpoint in this bridge. A 404 is not a WhatsApp authentication check. Verify MCP execution and synchronization. |
| Missing or stale history | Check bridge connectivity and WhatsApp linked-device state. Back up before any deliberate re-pairing; do not delete databases as the first troubleshooting step. |
| Downloaded file cannot be opened in ChatGPT | The returned path belongs to the host Mac. File upload/transfer or transcription needs a separate explicitly authorized workflow. |

## What to report when setup is finished

Codex should report separately: bridge pairing/connectivity; synthetic tests; local MCP registration and execution; tunnel remote authentication; ChatGPT tool discovery; actual read execution; and anything not tested, including sending and mobile UI behavior. Do not claim complete history coverage from one successful page of messages.
