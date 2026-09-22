# Future Cutflow contract

Status: interface sketch only. This repository does not connect to Cutflow in v0.1.

Cutflow may eventually send one shot request to a Blender generator:

```json
{
  "shot_type": "product_hero",
  "product": {
    "name": "Premium Hotel Bath Towel",
    "width_cm": 70,
    "length_cm": 140,
    "weight_g": 600,
    "color": "White"
  },
  "duration_seconds": 7,
  "aspect_ratio": "16:9",
  "style": "premium_hotel",
  "output": "clip.mp4"
}
```

The future boundary is deliberately small:

```text
Cutflow shot request
        ↓ validate / map into product config
Blender Generator
        ↓ deterministic scene + camera + render
clip.mp4 + result.json
        ↓
Cutflow Timeline
```

## Input contract

| Field | Type | Requirement |
|---|---|---|
| `shot_type` | string | v0 contract recognizes `product_hero` |
| `product` | object | Product display fields and generator parameters; never treated as executable code |
| `duration_seconds` | number | Positive and bounded by the generator policy |
| `aspect_ratio` | string | Named ratio such as `16:9`; mapped to explicit pixel dimensions |
| `style` | string | Allow-listed visual preset such as `premium_hotel` |
| `output` | string | Relative output filename under an approved render directory |

## Output contract

The generator should return the relative MP4 path plus machine-readable evidence: Blender and generator versions, frame range, FPS, resolution, render engine, elapsed time, checksums and validation state. Errors should be structured and must preserve any completed image sequence.

## Ownership boundary

- Cutflow chooses timeline intent, validates product data and consumes the clip.
- The Blender generator owns scene construction, camera motion, rendering and local artifact validation.
- MCP remains the interactive control and inspection channel for Codex. The deterministic generator remains the reproducible execution path.
- A later integration must sanitize paths, allow-list styles and shot types, cap duration/resolution, and never evaluate input as Python.
