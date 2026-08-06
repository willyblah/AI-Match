# 状态 Sprite Sheet 生成提示词模板

## 用途

基于 canonical base pet 生成某个动画状态的 1×N 横向 Sprite Sheet。

## 输入变量

- `{{state_name}}`：状态名称，如 idle / working / success / remind
- `{{frame_count}}`：帧数
- `{{frame_description}}`：每帧动作描述
- `{{base_pet_path}}`：canonical base pet 图片路径（唯一身份参考）
- `{{app_visual_system}}`：目标应用的 Application Visual System
- `{{app_style_reference}}`：应用截图或现有插画路径（用于 visual style，可选）
- `{{total_width}}`：建议总宽度，如 `{{frame_width * frame_count}}`
- `{{frame_height}}`：建议高度

## 提示词

```text
Generate a 1×{{frame_count}} horizontal sprite sheet of the SAME character from the canonical reference image.

Character: use the EXACT same pet/character from {{base_pet_path}} (this is the identity reference).

The character must look like it NATURALLY belongs to the target application's existing illustration system — same color palette, stroke style, shadow/gradient usage, and shape language — NOT a generic mascot, sticker, 3D toy, or photo asset.

Application Visual System to match:
{{app_visual_system}}

{{#if app_style_reference}}
Visual style reference (use ONLY for art style — do NOT copy its text, UI controls, or full scenes):
{{app_style_reference}}
{{/if}}

State: {{state_name}}

Frame descriptions (from left to right):
{{frame_description}}

Layout requirements:
- Exactly {{frame_count}} equal-width cells arranged horizontally, left to right.
- Each cell must show the full character centered at the same scale.
- The character baseline and body position must be aligned across all frames.
- No overall position shift; motion amplitude must be subtle and consistent with the state.
- Leave clean, uniform light off-white space between cells and around the character.
- Image size: approximately {{total_width}}×{{frame_height}} pixels.
- Transparent/alpha background is acceptable if generated, but a uniform light background is also fine for post-processing.

Silhouette preservation (V2.1):
- Keep the SAME signature silhouette and body proportions as the canonical reference.
- Preserve the relative length/width, ratio to head/body, fixed position, and visual weight of signature features (long ears, hat, hairstyle, tail, wings, horns, fixed costume, headwear, etc.).
- Do NOT change head size, head-to-body ratio, or let ears/hat/hair/tail proportions drift across frames.

Props (V2.1):
- Props (book, pen, computer, file, etc.) are secondary. Lock the character's canonical scale FIRST, then accommodate props.
- Never shrink the character body to fit a prop. If a prop is too large, shrink or simplify the prop instead.
- Do NOT add large tables, chairs, or background scenes unless explicitly requested.

Quality requirements:
- No text, no numbers, no titles, no borders, no grid lines, no watermarks.
- Consistent fur/skin color, markings, facial features, and expression style.
- Soft natural lighting, high detail, suitable for seamless animation.

Output: a single PNG file named {{state_name}}-spritesheet.png.
```

## 输出文件

- `tasks/{{state_name}}-spritesheet.png`

## 备注

- `{{frame_description}}` 应逐帧描述，每帧独立成段。
- 动作幅度应适合该状态语义：idle 要小，success 可以夸张，remind 要引起注意。
- 确保同一状态内角色不发生整体位置偏移。
