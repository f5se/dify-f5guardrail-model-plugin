# Privacy Policy

This plugin sends prompt content from Dify to the F5 Guardrail (CalypsoAI) service that the user has explicitly configured. No data is sent anywhere else by this plugin.

## Data sent to F5 Guardrail

- The plain text representation of the prompt messages produced by Dify (system / user / assistant / tool messages, after being concatenated to a single text input).
- The provider name and/or project ID configured by the user (used for routing).
- The authorization token configured by the user.

## Data NOT sent

- File uploads of any kind. The plugin rejects requests containing non-text content.
- Streaming control messages. Streaming requests are downgraded to a single non-streaming call before being sent to F5 Guardrail.

## Storage

This plugin does not persist prompts, responses, or credentials. Credentials are managed by the Dify plugin runtime.

## Logs

Scanner outcome metadata (scanner ID, outcome, scan direction) may be logged at INFO level to aid auditing. Prompt content and tokens are not logged.

For F5 Guardrail's own data handling, please refer to F5 AI Security documentation: https://docs.aisecurity.f5.com/
