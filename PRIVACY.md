# Privacy Policy

This plugin is designed with privacy-by-default principles. It only processes
the minimum data required to deliver Guardrail scanning and routed model
responses through the user-configured F5 Guardrail service.

## 1. Data Processing Scope

The plugin may process the following categories of data at runtime:

- User-provided prompt content and conversation context required for inference.
- Provider routing parameters configured by the user (for example provider/project).
- Authentication credentials provided by the user in Dify plugin settings.
- Guardrail decision metadata (for example outcome, scanner direction, scanner ID).

The plugin does not collect additional personal profile attributes by design.

## 2. Purpose Limitation

Processed data is used only for:

- Sending requests to the configured F5 Guardrail endpoint.
- Receiving and transforming Guardrail results into Dify-compatible responses.
- Operational troubleshooting and security auditing (limited metadata only).

No processed data is used for advertising, profiling, or unrelated analytics.

## 3. Data Minimization

- The plugin only sends data necessary to complete each model invocation.
- Optional routing fields are transmitted only when configured.
- Logging is disabled by default and can be explicitly enabled by operators.
- When logging is enabled, prompt body content is not intentionally recorded.

## 4. Storage and Retention

- The plugin does not intentionally persist prompts, completions, or credentials
  to local plugin storage.
- Credentials are managed by Dify's plugin runtime secret handling.
- Runtime data exists in memory for request processing and is discarded afterward.

## 5. Third-Party Transfer

This plugin transmits inference data to the F5 Guardrail service configured by
the user. Data handling by F5 Guardrail is governed by F5 policies and terms.

Reference: https://docs.aisecurity.f5.com/

## 6. Security Controls

- Transport uses HTTPS endpoints configured by the user.
- Credentials are treated as secrets and are not meant to be exposed in logs.
- Error handling avoids returning raw secret values in user-facing messages.

## 7. User and Operator Responsibilities

Plugin operators are responsible for:

- Using appropriate legal basis and user notice for processing data.
- Configuring compliant retention/access controls in their Dify environment.
- Enabling logs only when required for troubleshooting and disabling afterward.

## 8. Contact and Updates

If privacy-related behavior changes in future versions, this file will be
updated accordingly in the plugin package.
