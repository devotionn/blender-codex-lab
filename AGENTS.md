# Blender Codex Lab

- This public repository integrates the **official Blender Lab MCP**, not the similarly named PyPI/community project. Read `docs/implementation.md` before changing the integration.
- Keep scene creation and render execution on the live MCP route. Use `scripts/codex_mcp.py` if tools added during this task are not exposed directly in the desktop tool catalog. This invokes Codex's MCP client, not a replacement Blender server.
- Read the scene before writing. Reset only the default empty-startup scene or `MCP_SMOKE_SCENE_V0_1`; never clear unrelated user work.
- Work only with this repository and its outputs. Do not inspect unrelated projects, browser data, credentials, SSH keys, or other personal files. Never upload local private files.
- Keep `.local/`, `.venv/`, generated `.blend`, full renders, logs, cache, backups, machine-specific configuration, and credentials out of Git. Use repository-relative paths in committed evidence.
- Official bridge is loopback-only. It executes arbitrary Python and is not a security sandbox. Do not expose it to a network.
- Preserve existing Codex and Blender settings. This project uses its own Blender profile and `.codex/config.toml`.
- Validate live datablocks, reopen the saved `.blend`, validate PNG pixels/dimensions, and visually inspect the output. An exit code alone is not a pass.
- After rendering, run `.venv/bin/python -m unittest discover -s tests -v`. Keep verification evidence accurate; do not carry over a visual PASS after changing the render without inspecting it again.
- Do not merge the current product-video PR.
