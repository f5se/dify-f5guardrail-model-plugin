import os


def is_plugin_log_enabled() -> bool:
    value = os.getenv("PLUGIN_LOG_ENABLED", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}

