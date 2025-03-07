import os
import configparser
import logging

logger = logging.getLogger(__name__)
logger.propagate = True

class Config:
    def __init__(self):
        self._config = None

    def _load_config(self):
        paths = [
            "/run/credentials/wallet-watcher.service/walletwatcher.conf",
            "/etc/walletwatcher/walletwatcher.conf",
        ]

        for path in paths:
            if os.path.exists(path):
                try:
                    self._config = configparser.ConfigParser()
                    self._config.read(path)
                    logging.info(f"Loaded configuration from {path}")
                    return

                except configparser.Error as e:
                    logging.error(f"Error reading configuration file {path}: {e}")

                except FileNotFoundError:
                    logging.error(f"Configuration file not found at {path}")

        logging.error("No valid configuration file found!")
        raise FileNotFoundError("No valid configuration file found!")

    def get(self, section, key):
        if self._config is None:
            self._load_config() #load the config here.
        return self._config.get(section, key)

_config_instance = Config()

def get(section, key):
    return _config_instance.get(section, key)
