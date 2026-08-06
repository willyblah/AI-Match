---
name: generate-vn-portrait
description: "Generate visual-novel portrait prompts first, then use the bundled GPT-Image-2 image generation reference to create raw images from those finalized portrait prompts, and postprocess the result: one character per image, default 3:4 portrait canvas, half-body/bust framing, transparent-ready flat chroma-key background, narrative-game character expression and pose direction. Use when Codex needs 人物立绘, visual-novel portraits, dating-sim character portraits, dialogue UI standees, or story-game character art. Use generate2dsprite for gameplay sprites, animation frames, sprite sheets, props, projectiles, and frame/grid extraction; use generate2dmap for backgrounds, locations, maps, stages, tilemaps, and scene art."
---

# Generate VN Portrait

Use this skill for visual-novel character portraits, not gameplay sprites or maps. Use `$generate2dsprite` for sprite sheets, animation frames, props, projectiles, and transparent gameplay assets. Use `$generate2dmap` for backgrounds, maps, location art, stages, and scene images.

Default output: **one character, one image, 3:4 vertical canvas, half-body/bust framing, flat chroma-key background**.

## Hard Requirements

- Generate one character per image by default.
- Use a vertical `3:4` canvas/aspect ratio by default.
- Use half-body/bust framing by default: head to chest or head to waist. No legs, no feet, no full-body pose unless the user explicitly asks.
- Use one expression and one pose by default. Do not generate multiple actions, frames, poses, expressions, or a character sheet unless the user explicitly asks.
- Use a perfectly flat solid `#FF00FF` magenta background by default for background removal.
- If the subject is dominated by magenta, pink, purple, or fuchsia, use a perfectly flat solid `#00FF00` green background instead and pass that key color to postprocessing.
- The chroma-key color must fill the entire canvas. No scenic background, campus background, room background, floor, cast shadow, gradient, texture, haze, lighting variation, UI, border, labels, text, or watermark.
- Do not use words like `sprite`, `sprite quality`, `sprite sheet`, `frame`, `grid`, `full body`, `standing full body`, `clear background`, or `simple gradient` in the final image prompt unless the user explicitly requests that behavior.

## Workflow

1. Inspect the request or narrative script.
   - Extract the story genre, period, region, tone, character role, age range, personality, emotional state, outfit, and any attached/reference image role.
   - If the request asks for several characters, produce one prompt and one output image per character.
   - If details are sparse, infer only practical portrait details that fit the genre.
2. Choose style, expression, and pose.
   - Read `references/style-and-acting.md` for genre-specific style, palette, expression, and gesture cues when the story type matters.
   - Match attached references when provided: line weight, face rendering, proportions, palette, and rendering style.
3. Write the final image prompt.
   - Use the prompt contract below.
   - Normalize user wording into portrait production language. For example, replace full-body or standing language with half-body/bust portrait language unless explicitly requested.
4. Generate raw art from the finalized VN portrait prompt.
   - Only start this stage after completing steps 1-3 and producing the final portrait prompt.
   - Read `references/guide.md` to load the bundled image generation workflow, authentication, and API requirements for this generation stage.
   - Use the `createImage` / 文生图 API described there with the final VN portrait prompt as input. For endpoint-level details, read `references/image-generations-api.md`.
   - Do not call an external image generation skill; the capability is bundled as local references.
   - Create exactly one image for each requested portrait.
   - Save the raw output to `assets/portraits/raw/<portrait-id>-raw.png` and save the prompt to `assets/portraits/raw/<portrait-id>.prompt.txt`. 
   - Inspect the raw result before postprocessing. If the background is not a clean full-canvas flat key color, regenerate with stricter background wording.
5. Postprocess the background.
   - Run `scripts/process_vn_portrait_sheet.py` with `--rows 1 --cols 1`.
   - Use `--key-color "#FF00FF"` by default, or `--key-color "#00FF00"` only when the prompt intentionally used green because the subject was magenta/purple.
   - Keep the default soft matte, despill, `--edge-contract 1`, and `--edge-feather 0.25` edge cleanup unless the subject is unusually thin-lined or the matte visibly erodes details.
6. QA the final asset.
   - Confirm alpha channel exists and corners are transparent.
   - Confirm the portrait is half-body/bust, not full-body.
   - Confirm there is only one character and no multi-frame sheet.
   - Confirm the final crop works in dialogue UI and no key-color fringe remains.
   - Before using the generated portrait in app or game code, import the processed transparent portrait asset explicitly at the top of the file. Do not reference the raw file path or assume the bundler will discover the asset automatically.
   - When placing the portrait in a Phaser game scene, set the display scale so the portrait occupies roughly 50–60% of the canvas height, leaving room for the dialogue box at the bottom. Calculate the scale as `targetHeight / portrait.height` where `targetHeight = cameraHeight * 0.55`. Do not use the portrait's native pixel size as the display size.

## Final Image Prompt Contract

The final image prompt should follow this structure. Do not send a loose user request directly to image generation.

```text
Use case: illustration-story
Asset type: visual novel character portrait / 人物立绘
Primary request: <one-sentence character role and story genre>
Subject: exactly one character, <age range>, <role>, <personality>, <outfit/accessories>
Expression and pose: <one expression>, <one subtle upper-body gesture or posture>
Style/medium: <genre-specific VN illustration style>, clean readable face, consistent linework, polished but not over-rendered
Composition/framing: vertical 3:4 canvas, half-body/bust portrait, head to chest or head to waist, no legs, no feet, no full-body view, character fills most of the canvas height, centered, generous padding around hair and shoulders
Background: perfectly flat solid <#FF00FF or #00FF00> chroma-key background filling the entire canvas
Constraints: one character only, one pose only, one expression only, no scenic background, no gradient, no floor, no shadow, no text, no watermark, no UI, no border
Avoid: sprite, sprite sheet, animation frames, action poses, full-body pose, legs, feet, multiple characters, multiple expressions, character sheet, clear background, simple gradient
```

## Genre And Acting

Use character acting words, not action-animation words. Prefer small, portrait-friendly acting:

- gaze direction, guarded smile, tired eyes, shy glance, confident half-smile, nervous hand near collar, notebook held to chest, one hand on backpack strap, folded arms, relaxed shoulders, clenched jaw, restrained grief.
- For youthful romance, keep the pose simple and readable.
- For mystery or historical drama, use more restrained expressions and period-specific clothing details.
- For stylized comedy, allow brighter expression and simpler shapes.

## Postprocessing

For one portrait:

```bash
python3 skills/generate-vn-portrait/scripts/process_vn_portrait_sheet.py \
  --input assets/portraits/raw/<portrait-id>-raw.png \
  --output-dir assets/portraits/<character-id> \
  --rows 1 \
  --cols 1 \
  --labels <portrait-id> \
  --key-color "#FF00FF" \
  --edge-contract 1 \
  --edge-feather 0.25 \
  --trim \
  --padding 24
```

If the subject required green key because of magenta/purple-dominant design:

```bash
python3 skills/generate-vn-portrait/scripts/process_vn_portrait_sheet.py \
  --input assets/portraits/raw/<portrait-id>-raw.png \
  --output-dir assets/portraits/<character-id> \
  --rows 1 \
  --cols 1 \
  --labels <portrait-id> \
  --key-color "#00FF00" \
  --edge-contract 1 \
  --edge-feather 0.25 \
  --trim \
  --padding 24
```

Do not use `--auto-key border` as the normal path. It is only for debugging or salvage, because it can hide a failed generation with the wrong background.

If a visible magenta/green fringe remains, retry postprocessing with `--edge-contract 2`. If the edge becomes too bitten or hair/linework erodes, return to `--edge-contract 1` and reduce feathering with `--edge-feather 0`.

## Output Layout

Prefer:

```text
assets/portraits/
  raw/
    <portrait-id>-raw.png
    <portrait-id>.prompt.txt
  <character-id>/
    <portrait-id>.png
    sheet-alpha.png
    manifest.json
```

For narrative scripts, use `assets.portraits` ids as stable filenames.
