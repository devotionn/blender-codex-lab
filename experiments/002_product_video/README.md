# 002 · Premium hotel towel product video

This experiment turns a natural-language commercial brief into a 7-second product shot through the official Blender MCP and a deterministic `bpy` generator.

The scene contains three procedurally modeled folded towels, separate raised hems, a folded top end, beveled/subdivided/displaced cloth geometry, a procedural fabric bump material, a matte pedestal, seamless warm-gray cyclorama and four large area lights. The physical product values in `product.json` are visual experiment inputs, not a product information system.

The camera itself is animated. It moves from `[6.2, -8.8, 4.8]` through `[5.5, -7.8, 4.2]` to `[4.5, -7.1, 3.7]`, while the lens changes from 54 mm to 60 mm. The world and product remain stationary.

## Pipeline

1. Codex uses the official MCP `execute_blender_code` tool to run `render_product_video.py` in the live GUI Blender.
2. The generator reads `product.json`, creates the scene, keys the camera and saves `product_towel_v0_1.blend`.
3. Three preview check frames are rendered and visually inspected. The first attempt exposed the cyclorama edge; Codex widened the backdrop and rendered the checks again.
4. Preview and final PNG sequences are rendered through MCP in bounded chunks.
5. `encode_product_video.py` checks that all 168 frames exist and encodes H.264 MP4 with FFmpeg.
6. Tests reopen the `.blend`, inspect Blender data and use `ffprobe` to validate both videos.

Generated binaries remain local and Git-ignored. The committed `result.json` contains relative paths, hashes, timing and the inspection result.
