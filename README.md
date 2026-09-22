# Blender Codex Lab

让 Codex 实际操作本机 Blender：从静态 MCP smoke test 走到参数化的 3D 产品广告短片。

本项目使用 **Blender Lab 官方 MCP v1.0.3**。本次环境为 Apple Silicon / Blender 5.2.2 LTS。静态验证见 [`experiments/001_mcp_smoke`](experiments/001_mcp_smoke)，产品视频见 [`experiments/002_product_video`](experiments/002_product_video)。完整渲染和可编辑 `.blend` 保留在本机。

## 它如何工作

```text
Codex
  ↓ Codex 内置 MCP Client（本轮通过 App Server 调用）
Blender Lab MCP Server（stdio 子进程）
  ↓ 本机 TCP 127.0.0.1:9876
Blender 官方 MCP Add-on
  ↓ Blender Python API / bpy
Scene → .blend → PNG Render
```

Blender 是实际建模和渲染的软件。MCP 是让 Codex 向正在运行的 Blender 发出操作的连接。Python 脚本保存了可复用的建模步骤，下一次不必依赖完全相同的聊天措辞。

## Product Video Pipeline

```text
Natural-language Brief
        ↓
      Codex
        ↓
   Blender MCP              interactive agent control
        ↓
Scene Iteration / Inspection
        ↓
Parameterized bpy Generator reproducible generation
        ↓
      Blender
        ↓
PNG Frames → H.264 MP4
```

MCP 负责实时读取、调整、渲染和检查当前 Blender 场景。生成器负责把已验证的方法固化为确定性代码。成功逻辑不只留在 prompt 中；产品参数、镜头时长和位置、分辨率、FPS 与输出路径都在 [`product.json`](experiments/002_product_video/product.json) 中。

当前 v0.1 针对白色折叠浴巾：几何使用 bevel、subdivision、细微 displacement、独立织边和折叠层次；材质使用高 roughness、sheen 和程序化 fabric bump；相机本身执行平滑 dolly-in 与小幅 orbit。没有使用付费或外部模型资产，也没有 cloth simulation。

Blender 启动并连接 MCP 后，完整可复现入口是：

```sh
.venv/bin/python scripts/run_product_video.py
```

该入口依次读取配置、通过 MCP 生成并保存场景、渲染检查帧、生成 preview、生成 final、编码并运行测试。只需要快速迭代时使用 `--preview-only`。底层 Blender 入口是 [`render_product_video.py`](blender/scripts/render_product_video.py)，支持 `build`、`checks`、`preview:first:last` 和 `final:first:last`，便于 Codex 针对一个镜头分段重做。

最终版本为 1920×1080、24 fps、168 帧、7 秒。PNG 序列先落盘，再编码 MP4，因此编码失败不会丢掉已渲染帧。未来 Cutflow 边界见 [`docs/CUTFLOW_INTEGRATION.md`](docs/CUTFLOW_INTEGRATION.md)。

## 以后重新开机怎样开始

1. 在 Codex 打开这个仓库，启动 `./scripts/start-blender`。它会打开使用项目专用设置的 Blender；等待窗口打开。此时插件自动开启。不要同时启动两个占用 9876 的实验 Blender。
2. 保持 Blender 运行。MCP Server 由 Codex 按 `.codex/config.toml` 自动启动，无需单独开一个服务终端。
3. 让 Codex “检查 Blender MCP 连接”。可用 `codex mcp get blender` 查配置，再用 `.venv/bin/python scripts/codex_mcp.py inspect` 确认 live tool 清单；只有后者以及成功读场景才说明链路可用。
4. 告诉 Codex：“运行 MCP_SMOKE_SCENE_V0_1，检查并保存最终渲染。”它应先读取当前场景，再按下面的复现流程操作。不要在存有其他工作的 Blender 场景里运行 reset。

本机本轮已安装完成。只有新机器或依赖目录被删除时，才需 `python3 scripts/setup.py`。需要已安装的 Blender 5.1+、uv、git 和 Codex CLI。新机器还需让 Codex 信任该项目。启动器支持 `BLENDER_EXECUTABLE` 覆盖 Blender 可执行文件位置。

## 可复现运行

Blender 打开后，从仓库根目录执行；也可以直接让 Codex 执行：

```sh
.venv/bin/python scripts/codex_mcp.py execute --file blender/scripts/inspect_scene.py
.venv/bin/python scripts/codex_mcp.py execute --file blender/scripts/smoke_scene.py
.venv/bin/python scripts/codex_mcp.py execute --file blender/scripts/render_scene.py
.venv/bin/python scripts/codex_mcp.py execute --file blender/scripts/verify_scene.py
.venv/bin/python -m unittest discover -s tests -v
```

- 可编辑场景：`blender/scenes/mcp_smoke_v0_1.blend`
- 最终图片：`renders/mcp_smoke_v0_1.png`，1920×1080，Cycles CPU，64 samples，降噪
- 可选小预览：将 render 脚本换成 `preview_scene.py`，写入 `.local/preview.png`；之后仍须运行正式 render。
- 在 Blender 中按 F12 可再次渲染已保存场景；脚本渲染完成后也可直接打开 PNG。

## 本次遇到的问题

- **首次 Metal 渲染长时间等待内核编译**：进程采样确认停在 Metal compiler / Cycles wait，未产生预览。本次重启的仅是新建实验实例，随后改为 CPU；v0.1 明确固定 CPU，Metal 加速留待后续单独验证。
- **官方 Wiki 返回 403**：使用官方 Git 源码、release manifest 和 Blender CLI help 验证安装，不切换第三方 fork。
- **当前桌面任务没有新增工具名**：使用已验证的 Codex App Server MCP tool-call 接口完成当前任务；不是手写 TCP 绕过 MCP。此接口仍属 experimental，见[实现说明](docs/implementation.md)。
- **普通 Blender 看不到项目插件**：项目 profile 被有意隔离；用 `scripts/start-blender` 启动。
- **连接被拒绝**：先确认项目 Blender 正在运行，且监听本机 9876。插件需要 `--online-mode`，启动器已配置。关闭该实验 Blender 就会停止 bridge。

## 安全与仓库内容

官方 MCP 可以执行任意 Python；隔离 profile 只是隔离偏好和扩展，**不是 OS 沙箱**。本实验只操作指定场景与仓库输出；bridge 仅监听 loopback，不公开到网络。项目不用外部付费素材。

`.local/`、`.venv/`、完整 render、`.blend`、日志和备份均忽略；用户 Codex 配置不入库。没有为了安装而改动 `~/.codex/config.toml` 或日常 Blender profile。[官方来源与安装细节](docs/implementation.md)。
