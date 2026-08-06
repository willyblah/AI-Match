# 国内秒哒应用规格

## 页面

1. 文章输入：粘贴正文、Markdown或上传支持的文档。
2. AI分析：展示主旨、认知转折、建议配图点和不建议配图段落。
3. 分镜表：可编辑、排序、启停；包含主题、插入位置、核心意思、构图、动作、元素、标注和提示词。
4. 风格与角色：默认文章观察员、自定义参考图或明确选择来源预设。
5. 生成队列：逐图显示待处理、提交中、生成中、成功、失败和超时；成功项不重复提交。
6. 结果画廊：真实图片预览、用途、版本、下载、局部编辑和重新生成。
7. 导出：分镜JSON/CSV、提示词包和图片ZIP，必须产生真实下载。

## 技术

- 分析：加载 `wenxin-text-generation`。
- 生图/编辑：加载 `image-generation-super`，参考图走编辑能力。
- 单次项目可用前端状态；需要云端历史时使用Supabase表 `projects`、`article_sources`、`style_profiles`、`character_profiles`、`illustration_shots`、`generation_tasks`、`image_versions`。
- 异步任务只有终态成功、图片可预览、已持久化且下载可用时才算完成。显示真实402、429、解析和超时错误。
