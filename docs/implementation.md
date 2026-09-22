# 实现与来源

核验日期：2026-09-22。

## 官方实现

- [Blender Lab MCP 页面](https://www.blender.org/lab/mcp-server/)要求 Blender 5.1+。
- [官方源码与发布](https://projects.blender.org/lab/blender_mcp/releases/tag/v1.0.3)：v1.0.3，发布于 2026-09-11，固定提交 `2cea8d566dde07fbac28a61d698909d69724e853`。
- 官方源码的 `mcp/pyproject.toml` 定义 Python 包 `blender-mcp`，入口 `blmcp:main`。本项目从已核验官方 Git checkout 安装，**不能以裸 `uvx blender-mcp` 替代**，同名公共包不代表同一个实现。
- Add-on 使用官方发布的 `mcp-1.0.3.zip`，SHA-256：`a7a9da816192502e5a0a202a396444e266b47d8fc4f74ad4698048bd43040707`。
- `addon/blender_mcp_addon/blender_manifest.toml`：扩展 ID `mcp`，版本 1.0.3，最低 Blender 5.1.0。
- `mcp/blmcp/__init__.py`：`python -m blmcp --transport stdio`；客户端负责启动服务进程。
- `mcp/blmcp/tools_helpers/connection.py`：本地 TCP，NUL 结尾的 JSON，默认 localhost:9876；变量为 `BLENDER_MCP_HOST` 和 `BLENDER_MCP_PORT`；socket 超时 300 秒。
- 插件的 `__init__.py`：默认自动启动；GUI 模式通过 Blender timer 执行 Python；必须开启 online access，即使只用 localhost。本项目仅给实验进程传入 `--online-mode`。
- Blender 的 `--command extension install-file --help` 实测支持 `--repo user_default --enable`。安装位置由 Blender 自己根据隔离 profile 决定，不手工猜测系统 Add-on 目录。

上游 Wiki Setup 在此次访问时返回 HTTP 403，因此安装参数通过可访问的官方源码、扩展 manifest 和本机官方 CLI help 交叉验证。

## 配置策略

[Codex 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp)支持受信任项目的 `.codex/config.toml`、stdio、启动和工具超时。本机该项目已被信任；本项目没有写入用户级配置。

配置审计复查确认原有 MCP 条目和本项目 trust 仍在。会话期间用户配置的文件长度从 4128 变为 4127 字节、哈希发生变化；本任务未发出任何用户配置写操作，变更来源未核实，因此不声称其字节级完全不变，也未回滚可能来自其他任务或应用的变化。

配置通过 `./scripts/blender-mcp` 调用隔离虚拟环境里的官方模块。脚本从自身位置计算仓库根目录。应在此项目目录打开 Codex；项目迁移后重新运行 setup，虚拟环境不可搬运。

Blender 偏好和扩展位于 `.local/blender-user`，使用本机 `blender --help` 明确列出的 `BLENDER_USER_RESOURCES`。普通双击 Blender 不会自动选择这个项目 profile；请使用项目启动器。

## 当前任务的真实调用路径

安装之后，桌面任务原有工具目录不会自动出现新的 Blender 工具名。本轮没有因此停止出图：本机 Codex CLI 0.155.0-alpha.9.2 提供 App Server 的 `mcpServerStatus/list` 和 `mcpServer/tool/call`。

`scripts/codex_mcp.py` 使用本机 `codex app-server generate-json-schema --experimental` 返回的真实协议。它启动一个本地 Codex App Server，创建临时执行上下文，然后由 **Codex 内置 MCP 客户端**启动官方 Blender 服务、列举工具和调用工具。没有启动额外 LLM、没有创建新的用户侧任务，也没有替换官方 MCP server。

执行顺序：`initialize` → `thread/start`（ephemeral）→ `mcpServerStatus/list` → `mcpServer/tool/call`。连接关闭时终止辅助进程；Blender GUI 继续运行。每次调用可在本轮完成，无需重启桌面应用。新开的普通 Codex 任务也可直接加载项目 MCP；已有任务若只想使用自动注入的工具名，可重新打开任务。

这部分 App Server API 标记为 experimental；升级 Codex 后如协议变化，需重新生成 schema 核对。`codex mcp get blender` 只能证明配置被读取；本实验另外实际验证了 26 个 live tools 和成功的场景读写。

## 输出和边界

脚本按场景、通用几何/摄影、渲染和验证分文件。保存的 `.blend` 采用相对 render path；完整二进制成果留在本机，不提交。实验报告保存对象、相机边界、灯光参数、材质、输出尺寸、文件哈希等可复核结果。截图仅获取 Blender 窗口，留在忽略目录。

安装依赖版本由 `requirements.lock` 固定；官方 server 源码和 Add-on 归 Blender Authors，以 GPL-3.0-or-later 发布，不复制进本仓库。
