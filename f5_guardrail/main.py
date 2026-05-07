import logging

from dify_plugin import Plugin, DifyPluginEnv
from utils.logging_control import is_plugin_log_enabled

if is_plugin_log_enabled():
    logging.basicConfig(level=logging.INFO)
else:
    logging.disable(logging.CRITICAL)

plugin = Plugin(DifyPluginEnv())

if __name__ == "__main__":
    plugin.run()
