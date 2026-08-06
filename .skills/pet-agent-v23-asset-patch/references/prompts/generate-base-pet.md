# 角色基准生成提示词模板

## 用途

生成统一的 canonical base pet，作为后续所有动画状态的唯一视觉参考。

## 输入变量

- `{{character_description}}`：用户对角色的文字描述
- `{{reference_images}}`：用户提供的参考图路径（如有，用于 identity）
- `{{app_visual_system}}`：目标应用的 Application Visual System（色彩/描边/阴影/形状语言等）
- `{{app_style_reference}}`：应用截图或现有插画路径（用于 visual style，可选）

## 提示词

```text
Generate a single high-resolution full-body character image of the following pet/character:

{{character_description}}

This character must look like it NATURALLY belongs to the target application's existing illustration system — as if drawn by the same designer using the same visual language — NOT a generic cartoon mascot, sticker, 3D toy, or photo asset pasted onto the page.

Application Visual System to match:
{{app_visual_system}}

{{#if app_style_reference}}
Visual style reference (use ONLY for art style, color, stroke, shading language — do NOT copy its text, UI controls, or full scenes):
{{app_style_reference}}
{{/if}}

Requirements:
- The character should be in a clear, natural, stable pose (sitting or standing front-facing).
- Match the application's color palette, saturation, stroke style, shadow/gradient usage, shape language, and simplification level.
- Background: clean, uniform light off-white color, easy to remove later.
- Lighting: soft, even, natural.
- No text, no numbers, no watermarks, no borders, no grid lines.
- The character should be centered in the frame with comfortable padding around it.
- Full body visible, proportions natural, identity clear.

Output: a single PNG image with clean edges, suitable for use as a canonical reference for subsequent animation states.
```

## 输出文件

- `tasks/canonical-base-pet.png`
- 或 `public/images/pet/canonical-base-pet.png`

## 备注

- 如果用户有参考图，应在生成时通过 image-reference 参数传入（用于 identity）。
- 应用画风参考（截图/插画）单独传入，仅用于 visual style。
- canonical base 是内部生产与 QA 基准，**生成后无需再次向用户确认**即可继续后续状态生成。
