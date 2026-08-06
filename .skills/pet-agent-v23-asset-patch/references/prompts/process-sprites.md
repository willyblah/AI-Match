# 素材处理提示词/说明

## 用途

将生成的 1×N 横向 Sprite Sheet 处理为统一尺寸、透明背景的 Sprite 资源，并生成 `pet-sprites.json`。

## 处理流程

1. 读取 `tasks/<state>-spritesheet.png`。
2. 自动采样背景色，去除纯色背景，保留透明通道。
3. 羽化边缘，减少白边。
4. 按内容列自动切帧，识别帧数。
5. 统一画布尺寸，保持角色底部基线一致。
6. 输出透明 PNG 到 `public/images/pet/<state>.png`。
7. 汇总所有状态，生成 `public/images/pet/pet-sprites.json`。

## 输入

- `tasks/<state>-spritesheet.png`（一个或多个）

## 输出

- `public/images/pet/<state>.png`
- `public/images/pet/pet-sprites.json`

## 配置说明

- 画布尺寸应基于所有状态中的最大内容区域，不强制固定。
- `frameWidth` 应等于 `总宽度 / 帧数`。
- `frameHeight` 应等于画布高度。
- `fps` 和 `loop` 根据状态语义手动配置（示例值非默认推荐）。
- 资源配置文件统一命名为 `pet-sprites.json`（不要写成 `pet.json`）。

## 失败处理

- 如果帧数识别失败，检查源图是否等宽或提示词是否清晰。
- 如果背景去除不净，可调整采样阈值或重新生成源图。
