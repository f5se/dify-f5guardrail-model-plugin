# F5 Guardrail（Dify 模型供应商插件）

本插件把 **F5 Guardrail（CalypsoAI）** 接入 Dify，作为一个模型供应商。Dify
向该供应商发起的每一次请求，都会被插件转换为 F5 Guardrail `prompts` 接口
调用；Guardrail 会在请求和响应两个方向运行扫描器，插件再把结果按 Dify 的
`LLMResult` 结构返回，确保 Dify 前端无需任何改动即可显示。

## 主要能力

- 提供一个名为 `F5 Guardrail (安全模型代理)` 的预定义模型，背后真正调用的 LLM
  由你在供应商凭据中配置的 **Provider** / **Project** 决定。
- 阻断结果返回给 Dify 有两种方式：
  - `message`（默认）：把阻断说明作为 assistant 消息返回，前端可正常显示。
  - `error`：抛出标准调用错误，Dify 前端展示错误。
- 支持两种 Guardrail 检查范围：
  - `full-conversation`（默认）：把 Dify 当前多轮会话上下文整体送检。
  - `latest-user-message`：仅把当前对话中最新一条用户消息送检。
- 输入校验严格：上传文件直接返回 `InvokeBadRequestError`；流式请求被降级为
  单次非流式调用，再以单 chunk 形式返回。

## 已知限制

- **不支持流式**：F5 Guardrail `prompts.send` 是同步接口。插件始终以非流式
  方式调用 Guardrail；如果 Dify 请求流式，会在内部完成一次完整调用后，把
  结果作为单个 `LLMResultChunk` 返回。
- **不支持文件上传**：image / document / audio / video 内容会被拒绝，避免
  数据被静默丢弃。

## 供应商凭据字段

| 字段 | 是否必填 | 说明 |
|------|----------|------|
| `calypsoai_url` | 是 | F5 AI Security 实例地址，例如 `https://www.us1.calypsoai.app`。 |
| `calypsoai_token` | 是 | F5 AI Security 中生成的 token，作为 secret 存储。 |
| `calypsoai_provider` | 可选 | F5 Guardrail 中配置的 provider 名称或 ID。如填写则作为 `provider=` 透传给 SDK。 |
| `calypsoai_project` | 可选 | project ID 或 friendly ID。如填写则作为 `project=` 透传给 SDK。 |
| `message_check_scope` | 是（默认 `full-conversation`） | `full-conversation` 或 `latest-user-message`。控制 Guardrail 检查完整历史还是仅最新用户消息。 |
| `blocked_response_mode` | 是（默认 `message`） | `message` 或 `error`，决定阻断时如何返回 Dify。 |
| `blocked_message_template` | 可选 | 包含 `{reason}` 占位符的字符串模板，用于 `message` 模式下的阻断文案。 |
| `request_timeout_seconds` | 可选 | 预留字段。 |

> **路由策略**：当 `calypsoai_provider` 和 `calypsoai_project` 同时填写时，
> 两者都会被一并传给 Guardrail SDK，由 Guardrail 服务端决定最终的路由。

> **检查范围策略**：当 `message_check_scope=latest-user-message` 时，插件只会
> 将最新 `user` 消息发送到 Guardrail；若当前消息列表中没有 user 消息，会返回
> 明确的 bad-request 错误。

## 本地开发

推荐使用 `conda` 环境：

```bash
conda create -n dify-f5-guardrail python=3.12 -y
conda activate dify-f5-guardrail
pip install -r f5_guardrail/requirements.txt
```

> `calypsoai` 由 F5 发布，可能位于私有源或以 wheel 包形式提供。请在环境
> 创建完成后手工安装。

### 运行单元测试

```bash
cd f5_guardrail
python -m pytest tests
```

测试用 mock 替换了真实 SDK，可离线运行。

### 与 Dify 联调

```bash
cd f5_guardrail
cp .env.example .env
# 在 Dify 控制台 > 插件 > 调试 中获取 REMOTE_INSTALL_HOST / REMOTE_INSTALL_KEY
# 仅在需要排查问题时设置 PLUGIN_LOG_ENABLED=true 打开运行日志
python -m main
```

## 打包发布

```bash
dify plugin package f5_guardrail
```

打包出的 `*.difypkg` 文件可直接上传安装到 Dify。
