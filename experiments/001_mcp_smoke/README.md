# 001 · Official MCP live smoke

日期：2026-09-22。机器：macOS 26.6.2 / arm64。Blender：5.2.2 LTS。

**Live smoke：PASS。** [完整结构化证据](result.json)记录了真实对象、相机投影边界、灯光、材质和本机成果 SHA-256。

| 检查 | 实际结果 |
|---|---|
| 官方 MCP server / add-on | v1.0.3，固定官方提交与 release ZIP 校验和 |
| Codex 配置 | 项目级配置，`codex mcp get blender` 成功 |
| Codex live inspection | App Server `mcpServerStatus/list` 返回 26 个官方工具 |
| Scene read | 原始 GUI 场景 Cube / Camera / Light |
| Scene write | `execute_blender_code` 创建 18 个对象，5 种材质 |
| Lighting / Camera | Key、Fill、Rim 三盏灯，正交产品相机 |
| Geometry | 圆角主体、前面板、金色旋钮、通风孔、文字、展示台、地面 |
| Render | `execute_blender_code` → `bpy.ops.render.render`，Cycles CPU / 64 samples / 降噪 |
| PNG | 1920×1080，完整解码、像素方差和色彩丰富度通过 |
| Blend | 保存后用独立 Blender 进程重新打开并校验 datablocks |
| Visual check | 预览、最终 PNG、官方 MCP 窗口截图均实际打开检查 |
| Manual gate | 无；启动遮罩也已自动关闭 |

完整本机成果：

- `renders/mcp_smoke_v0_1.png`
- `blender/scenes/mcp_smoke_v0_1.blend`

为遵守本轮“不上传本机文件”的边界，二进制成果与截图仅保留本机；公开 PR 包含新编写的代码、文档和脱敏证据，不上传上述文件。

执行路径始终经过 Codex 内置 MCP client 和官方 server/add-on。独立 CLI 仅用于安装和**保存后的校验**，没有替代场景创建或渲染的 MCP 链路。

预览最初等待 Metal 内核编译；采样确认后停止该实验实例，用 CPU 重建并成功出图。没有把失败的 GPU 尝试记为成功。本轮无需重启 Codex；当前任务使用官方 App Server 工具调用 API，新任务可直接载入项目 MCP。普通桌面工具目录的动态更新没有验证。
