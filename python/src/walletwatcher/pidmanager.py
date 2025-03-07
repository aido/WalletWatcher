import fcntl
import logging
import os
import fcntl
import logging
import os
from cysystemd.daemon import notify, Notification

logger = logging.getLogger(__name__)
logger.propagate = True

class PidManager:
    def __init__(self, pid_file):
        self.pid_file = pid_file
        if "NOTIFY_SOCKET" in os.environ:
            notify(Notification.MAINPID, os.getpid())
            logging.debug("Systemd notification sent.")
        else:
            logging.debug("Systemd notify socket not found.")

    def write(self):
        try:
            with open(self.pid_file, 'w') as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                f.write(str(os.getpid()))
            logging.debug(f"PID written to {self.pid_file}")

        except BlockingIOError as e:
            logging.error(f"PID file is locked: {e}")
            raise BlockingIOError(f"PID file is locked: {e}")

        except IOError as e:
            logging.error(f"Error writing PID file: {e}")
            raise IOError(f"Error writing PID file: {e}")

    def remove(self):
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                logging.debug(f"PID file {self.pid_file} removed.")

        except FileNotFoundError as e:
            logging.error(f"PID file not found: {e}")
            raise FileNotFoundError(f"PID file not found: {e}")

        except PermissionError as e:
            logging.error(f"Permission error removing PID file: {e}")
            raise PermissionError(f"Permission error removing PID file: {e}")

        except Exception as e:
            logging.error(f"Error removing PID file: {e}")
            raise RuntimeError(f"Error removing PID file: {e}")

    def __enter__(self):
        self.write()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()
