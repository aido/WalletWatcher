import os
import logging
import requests
import json
from google.api_core import exceptions
import firebase_admin
from firebase_admin import credentials, auth, firestore, messaging, exceptions as firebase_exceptions
from configparser import NoSectionError, NoOptionError
from walletwatcher.config import get as config_get

logger = logging.getLogger(__name__)
logger.propagate = True

class FirebaseInitError(RuntimeError):
    """Custom exception for Firebase initialization errors."""
    pass

class FirebaseValueError(ValueError):
    """Custom exception for Firebase related ValueErrors."""
    pass

class Firebase:
    def __init__(self):
        """
        Initialises Firebase with required parameters.
        Raises FirebaseInitError if configuration settings are missing.
        """
        try:
            self.project_id = config_get("firebase", "project_id")
            self.channel_id = config_get("firebase", "channel_id")
            self.device_id = config_get("firebase", "device_id")
            self.collection = config_get("firebase", "collection")
            self.credentials = None
            self.service_account_email = None
            self.db = None
            self.fcm_token = None

            # Check if all required variables are set
            if not all([self.project_id, self.channel_id, self.device_id, self.collection]):
                raise FirebaseInitError("Required Firebase configuration settings are missing.")

            # Load credentials and initialize the app.
            self._get_credentials()
            if not firebase_admin._apps:
                firebase_admin.initialize_app(self.credentials)

            # Now initialize the client
            self.db = firestore.client()

        except FirebaseInitError as re:
            logging.error(f"Firebase initialization failed: {re}")
            raise  # Re-raise the exception

        except NoSectionError as e:
            logging.error(f"Firebase initialization failed, configuration section missing: {e}")
            raise FirebaseInitError(f"Firebase configuration section missing: {e}")

        except NoOptionError as e:
            logging.error(f"Firebase initialization failed, configuration option missing: {e}")
            raise FirebaseInitError(f"Firebase configuration option missing: {e}")

        except Exception as e:
            logging.error(f"Unexpected error during Firebase initialization: {e}")
            raise FirebaseInitError(f"Unexpected error during Firebase initialization: {e}")

    def _get_credentials(self):
        if self.credentials is None:
            paths = [
                "/run/credentials/wallet-watcher.service/service-account-key.json",
                "/etc/walletwatcher/service-account-key.json",
            ]

            for path in paths:
                if os.path.exists(path):
                    try:
                        self.credentials = credentials.Certificate(path)
                        logging.info(f"Loaded credentials {path}")

                        # Extract service_account_email
                        with open(path, 'r') as f:
                            creds = json.load(f)
                            self.service_account_email = creds.get('client_email')
                        logging.info(f"Service account email: {self.service_account_email}")

                        break

                    except FileNotFoundError:
                        logging.error(f"Credential file not found at {path}")

                    except json.JSONDecodeError:
                        logging.error(f"Credential file at {path} is not valid JSON")

                    except Exception as e:
                        logging.error(f"Error loading Firebase credentials from {path}: {e}")

            if self.credentials is None:
                raise Exception("Could not load Firebase credentials from any path.")

    async def _get_fcm_token(self):
        """Retrieves the FCM token from Firestore."""
        try:
            logging.info(f"Retrieving FCM token for device ID: {self.device_id} from collection: {self.collection}")
            doc = self.db.collection(self.collection).document(self.device_id).get()

            if doc.exists:
                token_data = doc.to_dict()
                if token_data and "token" in token_data:
                    self.fcm_token = token_data["token"]
                    logging.info(f"Successfully retrieved FCM token: {self.fcm_token}")
                else:
                    logging.error(f"FCM token field not found in document for device ID: {self.device_id}")
                    self.fcm_token = None  # Ensure that the fcm token is set to none.
            else:
                logging.error(f"No document found for device ID: {self.device_id} in collection: {self.collection}")
                self.fcm_token = None  # Ensure that the fcm token is set to none.

        except Exception as e:
            logging.error(f"Error retrieving FCM token for device ID: {self.device_id}: {e}")
            self.fcm_token = None  # Ensure that the fcm token is set to none.

        if self.fcm_token is None:
            logging.warning(f"FCM token retrieval failed for device ID: {self.device_id}")

    async def send_notification(self,
                                title="",
                                body="",
                                icon="ic_eye",
                                color="#CCCCCC",
                                priority="max",
                                default_sound=True,
                                default_vibrate_timings=False,
                                vibrate_timings_millis=[0, 100, 200, 300],
                                visibility="public"):
        """
        Sends a notification via FCM.
        """
        try:
            if not firebase_admin._apps:
                firebase_admin.initialize_app(self.credentials)

            # Now initialize the client
            self.db = firestore.client()

            await self._get_fcm_token()

            fcm_notification = {
                "title": title,
                "body": body,
                "icon": icon,
                "color": color,
                "priority": priority,
                "default_sound": default_sound,
                "default_vibrate_timings": default_vibrate_timings,
                "vibrate_timings_millis": vibrate_timings_millis,
                "visibility": visibility,
                "channel_id": self.channel_id
            }

            # Create a message
            message = messaging.Message(
                notification=messaging.Notification(),
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        **fcm_notification
                    )
                ),
                token=self.fcm_token
            )

            response = messaging.send(message)

            if isinstance(response, messaging.Message):
                logging.info(f"Successfully sent FCM message: {response.message_id}")
            elif isinstance(response, str) and response.startswith("projects/"): # check for string message id.
                logging.info(f"FCM message accepted: {response}") # log message id
            else:
                logging.error(f"FCM message send failed: {response}")
                raise FirebaseValueError(f"FCM message send failed: {response}")

        except exceptions.InvalidArgument as e:
            if "registration-token-not-registered" in str(e):
                logging.error(f"Invalid FCM token: {self.fcm_token}.")
            else:
                logging.error(f"FCM invalid argument error: {e}")
            raise FirebaseValueError("Invalid argument error")
        except exceptions.Unauthenticated as e:
            logging.error(f"FCM Unauthenticated error: {e}")
            raise FirebaseValueError("FCM Unauthenticated error")
        except requests.exceptions.RequestException as e:
            logging.error(f"FCM Network error: {e}")
            raise FirebaseValueError("FCM Network error")
        except firebase_exceptions.FirebaseError as e:
            logging.error(f"FCM error: {e}")
            raise FirebaseValueError("FirebaseError error")
        except ValueError as e:
            logging.error(f"FCM Value error: {e}")
            raise FirebaseValueError("FCM  Value error")
        except Exception as e:
            logging.error(f"An unexpected FCM  error occurred: {e}")
