# ChatGPT web connection

Use this route only for requested connection/setup/testing. Read `docs/ISOLATED-LAB-WEB-CONNECTION.md` from the selected verified source bundle. A personal Codex skill does not install an account plugin or grant tunnel permissions.

Reuse the official OpenAI Secure MCP Tunnel client with the separate `web_mcp.py` facade. `prepare_web_connection.py` stages it privately without changing running guest source, starting a VM or opening an internet connection. The default is read-only. Local policy can enable selected guest actions only with a dedicated guest. It never exposes VM start/stop or host input. Do not take over another chat's guest or sessions.

Check the account's actual Platform tunnel/workspace association, runtime-key access and personal ChatGPT plugin. Keep credentials out of chat/source bundles. Sign-in, account access and connection activation are separate from local acceptance. The reference local test passed with the real vendor Windows client; the real web account test is pending.

Prefer structured files/process results, browser DOM/ARIA and native AT-SPI data. Inspect, act, read back. Every web action needs a unique request_key; duplicate identical requests return recorded outcomes without rerunning. OUTCOME_UNKNOWN/timeouts require observation before any retry. No permanent autonomous/hang-free or universal app-control claim follows from a finite test.

For another computer, carry the verified source packet and accept its local guest first. Generate a new local plan/identity and configure the selected tunnel; do not import another machine's API keys/cookies. Refresh the actual ChatGPT plugin tool catalog and verify real replies before calling it connected.
