import logging

from dify_plugin import ModelProvider
from dify_plugin.entities.model import ModelType
from dify_plugin.errors.model import CredentialsValidateFailedError
from utils.logging_control import is_plugin_log_enabled

logger = logging.getLogger(__name__)


class F5GuardrailProvider(ModelProvider):
    """F5 Guardrail (CalypsoAI) model provider.

    Credentials are configured at the provider level. The model layer reuses
    them to authenticate against F5 Guardrail prompts API. Both ``provider``
    and ``project`` (when provided) are forwarded together to the Guardrail
    SDK so the F5 backend can decide the final routing.
    """

    def validate_provider_credentials(self, credentials: dict) -> None:
        try:
            self._validate_required(credentials)
            model_instance = self.get_model_instance(ModelType.LLM)
            model_instance.validate_credentials(
                model="f5-guardrail", credentials=credentials
            )
        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            if is_plugin_log_enabled():
                logger.exception("F5 Guardrail credentials validate failed")
            raise CredentialsValidateFailedError(str(ex))

    @staticmethod
    def _validate_required(credentials: dict) -> None:
        url = (credentials or {}).get("calypsoai_url", "").strip()
        token = (credentials or {}).get("calypsoai_token", "").strip()
        if not url:
            raise CredentialsValidateFailedError(
                "F5 Guardrail Base URL is required."
            )
        if not (url.startswith("http://") or url.startswith("https://")):
            raise CredentialsValidateFailedError(
                "F5 Guardrail Base URL must start with http:// or https://."
            )
        if not token:
            raise CredentialsValidateFailedError(
                "F5 Guardrail Token is required."
            )
