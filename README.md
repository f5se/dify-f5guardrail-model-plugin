# F5 Guardrail (Dify model provider plugin)

This plugin exposes **F5 Guardrail (CalypsoAI)** as a model provider inside Dify.
Every request that Dify sends to this provider is forwarded through the Guardrail
`prompts` API. Guardrail's scanners run on the prompt and the LLM response, then
the plugin maps the result back to Dify's `LLMResult` shape so the Dify UI works
unchanged.

## What you get

- One predefined model named `F5 Guardrail (routed)` whose underlying LLM is
  decided by the **Provider** and/or **Project** configured at the Dify
  provider-credentials level.
- Two ways to surface a blocked outcome to the Dify UI:
  - `message` (default): return an assistant message containing the configurable
    blocked-text template.
  - `error`: raise an invocation error so the Dify chat shows an error banner.
- Two guardrail check scopes:
  - `full-conversation` (default): send the full Dify conversation context
    (multi-turn) to Guardrail.
  - `latest-user-message`: only send the latest user message in the current
    conversation to Guardrail.
- Defensive request handling: file uploads are rejected with a clear error,
  streaming is downgraded to a single-chunk response.

## Limitations

- **No streaming.** F5 Guardrail's `prompts.send` API is synchronous. The plugin
  always calls Guardrail in blocking mode and emits a single chunk if Dify asks
  for a stream.
- **No file uploads.** Image / document / audio / video content is rejected with
  `InvokeBadRequestError` to avoid silently dropping data.

## Provider credentials

| Field | Required | Description |
|-------|----------|-------------|
| `calypsoai_url` | yes | Base URL of your F5 AI Security tenant, e.g. `https://www.us1.calypsoai.app`. |
| `calypsoai_token` | yes | Token issued by F5 AI Security. Stored as a secret. |
| `calypsoai_provider` | optional | Provider name **or** ID configured in F5 Guardrail. Forwarded as `provider=` to the SDK if set. |
| `calypsoai_project` | optional | Project ID or friendly ID. Forwarded as `project=` to the SDK if set. |
| `message_check_scope` | yes (default `full-conversation`) | `full-conversation` or `latest-user-message`. Controls whether Guardrail checks full history or only the latest user message. |
| `blocked_response_mode` | yes (default `message`) | `message` or `error`. Determines how blocked prompts are returned to Dify. |
| `blocked_message_template` | optional | Format string with `{reason}` placeholder used in `message` mode. |
| `request_timeout_seconds` | optional | Reserved for future use. |

> **Routing rule** — when both `calypsoai_provider` and `calypsoai_project`
> are filled, both values are passed to the Guardrail SDK in the same call.
> The Guardrail backend decides the final route.

> **Scope rule** — when `message_check_scope=latest-user-message`, only the
> newest `user` message is sent to Guardrail. If no user message exists in the
> prompt list, the plugin returns a clear bad-request error.

## Local development

This repository is set up to be developed inside a `conda` environment.

```bash
conda create -n dify-f5-guardrail python=3.12 -y
conda activate dify-f5-guardrail
pip install -r f5_guardrail/requirements.txt
```


### Run unit tests

```bash
cd f5_guardrail
python -m pytest tests
```

The tests stub out the Guardrail SDK so they run offline.

### Debug against a Dify instance

```bash
cd f5_guardrail
cp .env.example .env
# fill REMOTE_INSTALL_HOST / REMOTE_INSTALL_KEY from Dify > Plugins > Debug
# set PLUGIN_LOG_ENABLED=true only when you want runtime logs
python -m main
```

## Packaging

```bash
dify plugin package f5_guardrail
```

The resulting `*.difypkg` can be installed directly into a Dify instance.
