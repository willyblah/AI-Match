# V2 QA 检查清单

## 1. 项目分析

- [ ] 是否读取了 `package.json` 确认技术栈
- [ ] 是否读取了主入口、主页面、路由
- [ ] 是否读取了业务状态类型、Hook、store
- [ ] 是否读取了核心 Action 函数
- [ ] 是否读取了 UI 主题/设计文档
- [ ] 是否形成了应用业务摘要
- [ ] 是否只有在无法推断时才询问用户

## 2. 角色来源确认

- [ ] 是否在图片生成前询问了角色来源
- [ ] 是否区分了参考图 / 文字描述 / Skill 推荐方案
- [ ] 是否获得了用户明确确认
- [ ] 是否避免了未经确认默认使用机械小助手等角色

## 3. 制作确认单

- [ ] 是否在生成素材前输出确认单
- [ ] 确认单是否包含：应用类型、角色来源、视觉状态、生命周期、自动气泡、点击气泡、双击 reaction、主动气泡、拖拽、临时事件、安全操作
- [ ] 是否等待用户确认后再继续执行
- [ ] 是否没有“输出确认单后立即继续执行”

## 4. 视觉生成

- [ ] 是否先生成/确认 canonical base
- [ ] 是否基于 canonical base 生成所有 Sprite Sheet
- [ ] 是否每个状态独立生成，失败时只重试该状态
- [ ] 是否生成了 4 个状态（默认）或 4–6 个状态（自定义）
- [ ] 是否在 Prompt 中传入 Application Visual System 与应用画风参考
- [ ] 是否没有用 SVG/CSS 圆点/图标/占位角色替代正式宠物

## 5. 素材标准化与几何规范

- [ ] 是否使用 `process_sprites.py` 处理
- [ ] 是否通过 `--config` 传入配置，而非硬编码
- [ ] 是否通过 `--output-dir` 指定输出目录
- [ ] **Alpha-first**：是否先检查源图透明通道，有有效 alpha 时直接保留、跳过 RGB 抠背景
- [ ] **背景模式**：是否显式使用 `bg_mode`（preserve-alpha/chroma/auto），auto 时是否暂停报告而非默认抠除
- [ ] **羽化方向**：是否为 0→255（背景边缘低透明 → 主体高透明）
- [ ] **canonical body scale**：是否以 canonical/idle neutral 为参考对整个状态统一缩放，保持基线与中心

## 5.5 素材完整性 QA（Asset Integrity）

- [ ] 是否运行 `geometry_qa.py` 并查看 blocker
- [ ] 是否比较了处理前(源)与处理后(输出)的：有效 alpha 面积、主体高度、主体宽度、主要连通区域
- [ ] 是否检查了头部/耳朵/身体内部的 alpha 覆盖率
- [ ] 主体面积或高度灾难性减少(≥50%)是否被判 blocker
- [ ] 是否检查：黑色角色未被抠除、白色角色未被抠除、内部无棋盘格透明洞、无黑色线稿、无白色贴纸外壳、无异常边缘膨胀
- [ ] **是否没有仅凭剩余部分几何一致就判定通过**
- [ ] 是否生成了 `pet-sprites.json` 并记录了真实 frameWidth/frameHeight/frameCount/fps/loop
- [ ] 是否包含 `canonical` 字段
- [ ] 是否所有状态单帧 canvas 一致
- [ ] 是否使用共享 scale 而非按帧 fit-to-frame
- [ ] 是否使用 bottom-center anchor
- [ ] 输出图片是否透明背景

## 6. 几何 QA 与可视化

- [ ] 是否运行 `geometry_qa.py` 生成几何报告
- [ ] 是否生成 `contact-sheet.png`
- [ ] 是否生成 `motion-preview.png`
- [ ] 是否检查相邻帧 size popping
- [ ] 是否检查跨状态 baseline jump
- [ ] 是否检查 center shift
- [ ] 是否检查空帧/裁切/边缘越界

## 7. 代码接入

- [ ] 是否复制了通用 Core 模板（SpriteAnimator、PetWidget、usePetPosition、usePetBehavior）
- [ ] 是否没有因为业务类型修改通用 Core 模板
- [ ] 是否编写了应用专属 `pet-config.ts`
- [ ] 是否在主页面挂载了 `<PetWidget />`
- [ ] 是否绑定了安全操作函数
- [ ] 是否运行 lint/type-check
- [ ] 是否运行构建

## 8. 类型正确性

- [ ] `PetAppConfig<TAppStatus>` 是否正确传入业务类型
- [ ] `PetWidget<TAppStatus>` 是否正确传入业务类型
- [ ] 是否没有因业务类型导致 TypeScript 报错
- [ ] Core 模板是否保持业务无关

## 9. 状态与生命周期

- [ ] 是否定义了 `stateMeta` 明确每个视觉状态的生命周期
- [ ] `idle` / `working` 是否为 `persistent`
- [ ] `success` / `remind` 是否为 `transient`
- [ ] `success` 触发后是否自动恢复当前 Base State
- [ ] 如果事件结束时业务状态已变为 `working`，宠物是否恢复为 `working` 而非 `idle`

## 10. 重复事件与优先级

- [ ] 同一个任务完成事件是否可以连续触发多次
- [ ] 喝水记录是否可以连续触发多次
- [ ] 提醒弹窗是否可以多次触发
- [ ] 冷却期内是否不会重复触发
- [ ] 冷却期结束后是否可以再次触发
- [ ] 是否配置了不同 transient 事件的优先级
- [ ] 高优先级事件是否可以覆盖低优先级事件
- [ ] 多个事件同时满足条件时，是否只显示最高优先级事件

## 10.5 Transient 生命周期与 Event Identity 去重（Bugfix）

- [ ] success occurrence A 是否只触发一次
- [ ] success `durationMs` 结束后，是否不会因旧 timestamp 仍存在而再次触发
- [ ] 新的 occurrence B 出现后，是否可以再次正确触发
- [ ] failed 同一个 request/error identity 是否不会循环重复
- [ ] `repeatable: true` 的 transient 是否能响应真正的新事件
- [ ] transient 结束后是否恢复**当前最新** Base State
- [ ] Base State 在 transient 期间发生变化时，结束后是否恢复变化后的新状态
- [ ] boolean 条件持续为 `true` 时，是否不会周期性重触发
- [ ] `false → true` 的新 edge 是否可以再次触发
- [ ] 是否优先使用 event occurrence / timestamp / requestId 作为 identity，而非仅依赖持续 boolean condition

## 11. 通用轻交互（V2 新增）

- [ ] 单击宠物是否正常打开/关闭气泡
- [ ] 双击宠物是否触发 reaction
- [ ] 拖拽是否不误触点击
- [ ] 连续点击是否有节流
- [ ] 长时间 idle 主动气泡是否不会频繁出现
- [ ] 页面切换后宠物位置是否保持
- [ ] 用户输入时是否不触发主动气泡
- [ ] reaction 是否不改变主应用业务状态

## 12. 拖拽与边界

- [ ] 宠物是否可拖拽
- [ ] 拖拽时是否不会触发点击气泡
- [ ] 拖拽后位置是否记忆到 localStorage
- [ ] 刷新页面后位置是否保持
- [ ] 是否使用真实 DOM 尺寸计算边界，而非固定 128px
- [ ] 移动端/不同尺寸宠物是否不越界
- [ ] 窗口 resize 后是否重新校准边界

## 13. 气泡

- [ ] 点击宠物是否打开气泡
- [ ] 点击外部是否关闭点击气泡
- [ ] 状态变化时是否触发自动气泡
- [ ] 自动气泡是否自动关闭
- [ ] 气泡按钮是否只绑定安全操作
- [ ] 不同状态下气泡文案是否不同
- [ ] 是否同时最多显示一个气泡

## 14. 跨状态几何一致性（V2 新增）

- [ ] 同一个宠物所有状态单帧尺寸是否一致
- [ ] 所有状态是否使用共享 scale
- [ ] baseline 是否基本一致
- [ ] cross-state 切换是否无明显跳动
- [ ] success 起始/结束是否与 canonical anchor 兼容
- [ ] 不同 frameCount 状态是否仍使用相同单帧 canvas
- [ ] 某一状态几何 QA 失败时是否只修复该状态
- [ ] 是否出现角色主体被裁切
- [ ] 是否出现角色为了容纳动作而明显缩小
- [ ] 是否出现后处理造成的跨帧抖动

## 14.5 Character Identity QA（V2.1 新增）

- [ ] contact sheet 是否包含统一参考辅助（相同 canvas / baseline / center line / canonical reference）
- [ ] 是否逐一比较各状态的脸型、头身比、标志性配饰、发型/耳朵/帽子、服装、配色、尾巴/突出结构、整体 silhouette
- [ ] 标志性轮廓（耳朵/帽子/发型/尾巴/翅膀/角等）是否跨状态保持比例与位置
- [ ] 头身比是否跨状态一致
- [ ] 头饰/耳朵/发型比例是否无漂移
- [ ] 道具是否未导致角色本体缩小（道具过大时是否优先缩小道具）
- [ ] 是否无默认大桌子/大椅子/大背景场景（除非用户明确要求）
- [ ] 同一角色在不同状态是否看起来是同一版本
- [ ] 即使 bbox 通过，人眼是否无可明显察觉的 identity drift
- [ ] identity drift 的状态是否判定失败并只重新生成该状态

## 15. 失败与降级

- [ ] canonical base 失败时是否停止接入并报告，不用 SVG/CSS/占位角色
- [ ] 单个 Sprite 失败时是否只重试该状态，不影响主应用
- [ ] 是否没有用未经 QA 的静态占位图冒充状态
- [ ] Sprite 处理失败时是否不自动切 SVG/CSS 宠物
- [ ] 运行时资源加载失败时是否隐藏宠物（Error Boundary 隔离）
- [ ] 找不到安全操作时是否降级为只读状态宠物
- [ ] 几何 QA 失败时是否只修复失败状态

## 16. Application Visual Integration QA（V2.2 新增）

- [ ] 是否在实际应用页面预览中检查（非仅看独立 Sprite）
- [ ] 宠物是否与应用现有插画/人物属于同一视觉系统
- [ ] 色彩、饱和度、描边、阴影、渐变、材质是否一致
- [ ] 宠物是否不像外部贴纸、通用吉祥物、3D 模型或照片素材
- [ ] 桌面端与移动端尺寸、位置、视觉重量是否协调
- [ ] 移动端小尺寸下是否仍清楚可辨
- [ ] 是否不遮挡输入框、主要按钮、导航、关键内容
- [ ] 状态动画节奏是否与应用协调
- [ ] 气泡和双击反馈是否不破坏整体风格
- [ ] 是否无越界、裁切或视觉冲突

## 17. 不做的范围

- [ ] 没有实现多宠物
- [ ] 没有实现自主行走
- [ ] 没有实现声音/语音反馈
- [ ] 没有实现复杂 AI 对话

## 18. 跨应用复用验证

- [ ] 同一个 Core 模板是否同时适用于番茄钟、Personal Workspace、AI Workspace
- [ ] 是否没有为番茄钟修改 Core 模板
- [ ] 是否没有为当前应用修改 Core 模板
- [ ] 差异是否仅存在于 `pet-config.ts` 和主页面挂载
