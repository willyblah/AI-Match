# 应用集成与产品验收

## 用户流程

1. 上传人物参考图；
2. 上传动作参考视频；
3. 可选填写提示词或选择参考主体；
4. 选择人物朝向、声音和清晰度；
5. 提交后展示排队/生成状态和可继续查询的任务记录；
6. 成功后播放、下载并保存持久化副本；
7. 失败时展示可理解原因，保留输入以便修正后重试。

创建接口返回 `task_id` 仅代表提交成功。应用必须继续自动轮询；只有查询状态为 `succeeded`、取得视频 URL 并渲染播放器和下载入口后，才可以向用户显示“生成成功”。完整代码见 `app-complete-workflow.md`。

## 前端校验

- 图片格式、大小、像素和宽高比；
- 视频格式、大小、像素、时长；
- `image` 朝向最大 10 秒，`video` 朝向最大 30 秒；
- 使用主体时锁定 `video` 朝向；
- Prompt 字符数；
- 提交中禁用重复点击。

## 服务端职责

- 从环境读取 `INTEGRATIONS_API_KEY`，通过 `X-Gateway-Authorization` 调用飞轮生成的 API Plugin Endpoint；
- 重复执行全部关键校验；
- 生成唯一 `external_task_id`；
- 调用创建/查询接口；
- 保存任务状态、请求 ID、外部 ID和安全错误信息；
- 成功后流式转存视频，避免把大媒体载入内存或模型上下文；
- 使用 `task.id + output.id` 保证转存幂等。

## 验收清单

- Given 合法图片和 3–10 秒视频，When 朝向为 `image`，Then 创建成功并保存任务 ID；
- Given 超过 10 秒的视频，When 朝向为 `image`，Then 前端和服务端均阻止提交；
- Given 使用参考主体，When 朝向不是 `video`，Then 自动锁定或返回字段级错误；
- Given 重复点击，Then 只产生一个创建请求；
- Given Callback 丢失，Then 轮询仍能推进到终态；
- Given 查询返回多个任务，Then 按目标 ID 精确选择；
- Given 任务失败，Then 展示 `message` 且不自动重建；
- Given 视频生成成功但转存失败，Then 重试转存而不是重新生成；
- Given 成功输出，Then 持久化 URL 可播放和下载；
- Given 创建接口只返回任务 ID，Then 页面显示“已提交/生成中”并自动轮询，不显示“生成成功”；
- Given 查询达到 `succeeded`，Then 页面显示带 controls 的视频预览、“下载视频”按钮和可恢复的结果记录；
- Given 页面刷新时任务仍为非终态，Then 自动恢复轮询；Given 已完成，Then 恢复视频预览与下载；
- Given 任何日志和前端响应，Then 不含 API Key 或 Authorization。
