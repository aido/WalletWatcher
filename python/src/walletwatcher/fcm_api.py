import os
import asyncio
import aiohttp
import logging
import google.auth.transport.requests
from google.oauth2 import service_account
from configparser import NoSectionError, NoOptionError
from walletwatcher.config import get as config_get

logger = logging.getLogger(__name__)
logger.propagate = True


class FCMAPIInitError(RuntimeError):
    """Custom exception for FCM API initialization errors."""
    pass

class FCMAPIValueError(ValueError):
    """Custom exception for FCM API related ValueErrors."""
    pass

class FCMAPI:
    def __init__(self):
        """
        Initialises the FCM API with required parameters.
        Raises FCMAPIInitError if configuration settings are missing.
        """
        try:
            self.api_url = config_get("fcm", "api_url")
            self.api_operation = config_get("fcm", "api_operation")
            self.project_id = config_get("fcm", "project_id")
            self.channel_id = config_get("fcm", "channel_id")
            self.token_key = config_get("fcm", "token_key")
            self.credentials = None

            # Check if all required variables are set
            if not all([self.api_url, self.api_operation, self.project_id, self.channel_id, self.token_key]):
                raise FCMAPIInitError("Required FCM API configuration settings are missing.")

        except FCMAPIInitError as re:
            logging.error(f"FCMAPI initialization failed: {re}")
            raise  # Re-raise the exception

        except NoSectionError as e:
            logging.error(f"FCMAPI initialization failed, configuration section missing: {e}")
            raise FCMAPIValueError (f"FCMAPI configuration section missing: {e}")

        except NoOptionError as e:
            logging.error(f"FCMAPI initialization failed, configuration option missing: {e}")
            raise FCMAPIValueError (f"FCMAPI configuration option missing: {e}")

        except Exception as e:
            logging.error(f"Unexpected error during FCMAPI initialization: {e}")
            raise FCMAPIInitError(f"Unexpected error during FCMAPI initialization: {e}")

    async def _get_access_token(self):
        if self.credentials is None:
            paths = [
                "/run/credentials/wallet-watcher.service/service-account-key.json",
                "/etc/walletwatcher/service-account-key.json",
            ]

            for path in paths:
                if os.path.exists(path):
                    try:
                        self.credentials = service_account.Credentials.from_service_account_file(
                            path,
                            scopes=['https://www.googleapis.com/auth/firebase.messaging']
                        )
                        logging.info(f"Loaded credentials {path}")
                        break

                    except FileNotFoundError:
                        logging.error(f"Credential file not found at {path}")

                    except json.JSONDecodeError:
                        logging.error(f"Credential file at {path} is not valid JSON")

                    except Exception as e:
                        logging.error(f"Error loading credentials from {path}: {e}")

            if self.credentials is None:
                raise Exception("Could not load credentials from any path.")

        if self.credentials.token is None or self.credentials.expired:
            request = google.auth.transport.requests.Request()
            self.credentials.refresh(request)
            if self.credentials.token is None:
                logging.error("Failed to refresh FCM API token")
                raise RuntimeError("Failed to refresh FCM API token")
            logging.info("Refreshed FCM API token")

        logging.debug(f"FCM API token: {self.credentials.token}")

    async def _make_rpc_request(self, notification):
        """
        Makes an RPC request to the FCM API.
        """
        await self._get_access_token()

        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.credentials.token}"
        }

        payload = {
            "message": {
                "token": self.token_key,
                "android": {
                    "priority": "HIGH",
                    "notification": notification
                }
            }
        }

        rpc_url = f"{self.api_url}/{self.project_id}/{self.api_operation}"

        async with aiohttp.ClientSession() as session:
            for attempt in range(8):
                try:
                    async with session.post(rpc_url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()

                        if isinstance(result, dict) and "name" in result and isinstance(result["name"], str):
                            logging.debug(f"Response from FCM RPC server: {result}")
                            return result["name"]
                        else:
                            logging.error(f"Error: Unexpected response from FCM RPC server {rpc_url}: {result}")
                            raise FCMAPIValueError(f"Unexpected response from FCM: {result}")

                except aiohttp.ClientConnectionError as e:
                    logging.error(f"FCM RPC connection failed (attempt {attempt+1}/3): {e}")
                    await asyncio.sleep(2 ** attempt)

                except aiohttp.ClientResponseError as e:
                    logging.error(f"FCM RPC response error (attempt {attempt+1}/3): {e}")

                except aiohttp.ClientError as e:
                    logging.error(f"FCM RPC request failed (attempt {attempt+1}/3): {e}")
                    await asyncio.sleep(2 ** attempt)

                except asyncio.TimeoutError as e:
                    logging.error(f"FCM RPC encountered a timeout error")
                    await asyncio.sleep(2 ** attempt)

                except Exception as e:
                    logging.error(f"FCM RPC encountered an unexpected error: {e}")
                    await asyncio.sleep(2 ** attempt)

            logging.error(f"FCM RPC request to {rpc_url} failed after multiple retries.")
            raise FCMAPIValueError("FCM RPC request failed after multiple retries.")

    async def send_notification(self,
                                title = "",
                                body = "",
                                icon = "ic_eye",
                                color = "#CCCCCC",
                                notification_priority = "PRIORITY_MAX",
                                default_sound = True,
                                default_vibrate_timings = False,
                                vibrate_timings = ["0s", "0.1s", "0.2s", "0.3s"],
                                visibility = "PUBLIC"
                                ):
        """
        Sends a notification via FCM.
        """
        notification = { "title": title,
                         "body": body,
                         "icon": icon,
                         "color": color,
                         "notification_priority": notification_priority,
                         "default_sound": default_sound,
                         "default_vibrate_timings": default_vibrate_timings,
                         "vibrate_timings": vibrate_timings,
                         "visibility": visibility
                       }

        try:
            notification["channel_id"] = self.channel_id
            logging.debug(f"Sending FCM notification: {notification}")
            name = await self._make_rpc_request(notification)

            if name:
                try:
                    notification_id = name.split("/")[-1]
                    logging.info(f"FCM successfully sent notification with id {notification_id}")

                except IndexError:
                    logging.error(f"Error parsing notification id from {name}")
                    raise FCMAPIValueError(f"Unexpected name format: {name}")

            else:
                raise FCMAPIValueError("FCM notification send failed: No name returned.")

        except (FCMAPIValueError, RuntimeError) as e:
            logging.error(f"Error sending FCM notification: {e}")
            raise e

        except Exception as e:
            logging.error(f"Unexpected error sending FCM notification: {e}")
