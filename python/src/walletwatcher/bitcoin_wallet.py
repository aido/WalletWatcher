import asyncio
import aiohttp
import base64
import logging
from enum import Enum, auto
from configparser import NoSectionError, NoOptionError
from walletwatcher.config import get as config_get

logger = logging.getLogger(__name__)

class BitcoinWalletInitError(RuntimeError):
    """Custom exception for Bitcoin wallet initialization errors."""
    pass

class BitcoinWalletValueError(ValueError):
    """Custom exception for BitcoinWallet related ValueErrors."""
    pass

class BitcoinWalletStatus(Enum):
    INITIALISING = auto()
    SCANNING = auto()
    OK = auto()
    RPC_FAILURE = auto()

class BitcoinWallet:
    def __init__(self):
        """
        Initialises the bitcoin wallet with required parameters.
        Raises BitcoinWalletInitError if configuration settings are missing.
        """
        try:
            self.rpc_user = config_get("bitcoin", "rpc_user")
            self.rpc_password = config_get("bitcoin", "rpc_password")
            self.rpc_host = config_get("bitcoin", "rpc_host")
            self.rpc_port = config_get("bitcoin", "rpc_port")
            self.wallet_name = config_get("bitcoin", "wallet_name")
            self.descriptor_range = config_get("bitcoin", "descriptor_range")
            self.rescan_timestamp = config_get("bitcoin", "rescan_timestamp")

            xpub = config_get("bitcoin", "xpub")
            address_type = config_get("bitcoin", "address_type")
            master_fingerprint = config_get("bitcoin", "master_fingerprint")
            derivation_path = config_get("bitcoin", "derivation_path")

            # Check if all required variables are set
            if not all([
                self.rpc_user, self.rpc_password, self.rpc_host, self.rpc_port,
                self.wallet_name, self.descriptor_range, self.rescan_timestamp,
                xpub, address_type, master_fingerprint, derivation_path
            ]):
                raise BitcoinWalletInitError("Required bitcoin wallet configuration settings are missing.")

            self.descriptor = f"{address_type}([{master_fingerprint}/{derivation_path}]{xpub}/0/*)"
            self.rpc_request_id = 1
            self.current_balance = self.previous_balance = 0
            self.status = BitcoinWalletStatus.INITIALISING

        except BitcoinWalletInitError as re:
            logging.error(f"BitcoinWallet initialization failed: {re}")
            raise  # Re-raise the exception

        except NoSectionError as e:
            logging.error(f"BitcoinWallet initialization failed, configuration section missing: {e}")
            raise BitcoinWalletValueError(f"BitcoinWallet configuration section missing: {e}")

        except NoOptionError as e:
            logging.error(f"BitcoinWallet initialization failed, configuration option missing: {e}")
            raise BitcoinWalletValueError(f"BitcoinWallet configuration option missing: {e}")

        except Exception as e:
            logging.error(f"Unexpected error during BitcoinWallet initialization: {e}")
            raise

    async def _make_rpc_request(self, method, params):
        """
        Makes an RPC request to the Bitcoin Core server.

        Args:
            method (str): The RPC method to call.
            params (list): A list of parameters for the RPC method.

        Returns:
            The result of the RPC call, or None if an error occurs.
        """
        request_id = self.rpc_request_id
        self.rpc_request_id += 1

        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(f"{self.rpc_user}:{self.rpc_password}".encode()).decode()
        }
        payload = {
            "jsonrpc": "1.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        rpc_url = f"http://{self.rpc_host}:{self.rpc_port}/wallet/{self.wallet_name}" if method in ["getbalance", "getwalletinfo", "importdescriptors"] else f"http://{self.rpc_host}:{self.rpc_port}"

        async with aiohttp.ClientSession() as session:
            num_attempts = 4
            for attempt in range(num_attempts):
                try:
                    async with session.post(rpc_url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()

                        if isinstance(result, dict) and "result" in result and "error" in result and result["error"] is None and "id" in result and result["id"] == request_id:
                            logging.debug(f"Response from bitcoin RPC server method {method}: {result}")
                            result_data = result["result"]

                            if "warnings" in result_data and isinstance(result_data["warnings"], list) and result_data["warnings"]:
                                warnings = result_data["warnings"]
                                for warning in warnings:
                                    logging.warning(f"Warning: {warning}")
                            return result_data
                        else:
                            logging.error(f"Error: Unexpected response from bitcoin RPC server method {method}: {result}")
                            return None

                except aiohttp.ClientConnectionError as e:
                    logging.error(f"Bitcoin RPC connection failed (attempt {attempt+1}/{num_attempts}): {e}")
                    await asyncio.sleep(2 ** attempt)

                except aiohttp.ClientResponseError as e:
                    logging.error(f"Bitcoin RPC response error (attempt {attempt+1}/{num_attempts}): {e}")
                    await asyncio.sleep(2 ** attempt)

                except aiohttp.ClientError as e:
                    logging.error(f"Bitcoin RPC request failed {attempt+1}/{num_attempts}): {e}")
                    await asyncio.sleep(2 ** attempt)

                except asyncio.TimeoutError as e: 
                    logging.error(f"Bitcoin RPC encountered a timeout error")
                    await asyncio.sleep(2 ** attempt)

                except Exception as e:
                    logging.error(f"Bitcoin RPC encountered an unexpected error: {e}")
                    await asyncio.sleep(2 ** attempt)

            logging.error(f"Bitcoin RPC request to {method} failed after multiple retries.")
            self.status = BitcoinWalletStatus.RPC_FAILURE
            return None

    async def _import_descriptor(self):
        """
        Imports the descriptor into the wallet to watch specific Bitcoin addresses.
        """
        try:
            logging.info("Importing bitcoin descriptor.")
            get_descriptorinfo_result = await self._make_rpc_request("getdescriptorinfo", [self.descriptor])

            if get_descriptorinfo_result is None:
                logging.error("Error getting bitcoin descriptor info: RPC request returned None")
                raise BitcoinWalletValueError("RPC request returned None")

            if "descriptor" in get_descriptorinfo_result:
                descriptor = get_descriptorinfo_result.get("descriptor")
                try:
                    descriptor_range = int(self.descriptor_range)
                    rescan_timestamp = int(self.rescan_timestamp)

                except BitcoinWalletValueError:
                    logging.error("descriptor_range or rescan_timestamp are not valid integers")
                    raise BitcoinWalletValueError("descriptor_range or rescan_timestamp are not valid integers")

                import_descriptors_result = await self._make_rpc_request("importdescriptors", [[{
                    "desc": descriptor,
                    "range": descriptor_range,
                    "timestamp": rescan_timestamp
                }]])

                if isinstance(import_descriptors_result, list) and all(result.get("success") == True for result in import_descriptors_result):
                    logging.info("Bitcoin descriptor successfully imported.")
                else:
                    logging.error(f"Error importing bitcoin descriptor: {import_descriptors_result}")
                    raise BitcoinWalletValueError(f"Error importing bitcoin descriptor: {import_descriptors_result}")
            else:
                logging.error(f"Error getting bitcoin descriptor info: {get_descriptorinfo_result}")
                raise BitcoinWalletValueError(f"Error getting bitcoin descriptor info: {get_descriptorinfo_result}")

        except BitcoinWalletValueError as ve:
            logging.error(f"Error importing bitcoin descriptor: {ve}")
            raise ve

        except Exception as e:
            logging.error(f"Error importing bitcoin descriptor: {e}")
            raise BitcoinWalletInitError(f"Unexpected error importing bitcoin descriptor: {e}")

    async def _create_wallet(self):
        """
        Creates a new descriptor-based wallet if it doesn't already exist.
        """
        disable_private_keys = True  # Disable private keys in the wallet
        blank = True  # Create a blank wallet
        passphrase = ""  # No passphrase
        avoid_reuse = False  # Allow address reuse
        descriptors = True  # Create a descriptor wallet
        load_on_startup = True  # Load the wallet on startup
        try:
            logging.info(f"Creating bitcoin wallet {self.wallet_name}.")
            create_wallet_result = await self._make_rpc_request(
                "createwallet",
                [
                    self.wallet_name,
                    disable_private_keys,
                    blank,
                    passphrase,
                    avoid_reuse,
                    descriptors,
                    load_on_startup,
                ],
            )

            if create_wallet_result is None:
                logging.error("Error creating bitcoin wallet: RPC request returned None")
                raise BitcoinWalletValueError("RPC request returned None")

            if create_wallet_result.get("name") == self.wallet_name:
                logging.info(f"Bitcoin wallet {self.wallet_name} created.")
            else:
                logging.error(f"Error creating bitcoin wallet: {create_wallet_result}")
                raise BitcoinWalletValueError(f"Error creating bitcoin wallet: {create_wallet_result}")

        except BitcoinWalletValueError as ve:
            logging.error(f"Error creating bitcoin wallet: {ve}")
            raise ve

        except Exception as e:
            logging.error(f"Error creating bitcoin wallet: {e}")
            raise BitcoinWalletInitError(f"Unexpected error creating bitcoin wallet: {e}")

    async def _load_wallet(self):
        """
        Loads an existing wallet into Bitcoin Core.
        """
        try:
            # Get list of currently loaded wallets
            wallets = await self._make_rpc_request("listwallets", [])

            # Load wallet if not already loaded
            if self.wallet_name not in wallets:
                logging.info(f"Loading bitcoin wallet {self.wallet_name}.")
                load_wallet_result = await self._make_rpc_request("loadwallet", [self.wallet_name])

                if load_wallet_result and load_wallet_result.get("name") == self.wallet_name:
                    logging.info(f"Bitcoin wallet {self.wallet_name} loaded.")
                else:
                    logging.error(f"Error loading bitcoin wallet: {load_wallet_result}")
            else:
                logging.info(f"Bitcoin wallet {self.wallet_name} already loaded.")

        except Exception as e:
            logging.error(f"Error loading bitcoin wallet: {e}")
            raise BitcoinWalletInitError(f"Unexpected error loading bitcoin wallet: {e}")

    async def initialise_wallet(self):
        """
        Checks if the wallet exists; if not, creates and loads it. Then imports descriptors.
        """
        try:
            logging.info(f"Initializing bitcoin wallet {self.wallet_name}.")
            list_walletdir_result = await self._make_rpc_request("listwalletdir", [])

            # Check if the wallet exists in the directory
            if "wallets" in list_walletdir_result and any(wallet["name"] == self.wallet_name for wallet in list_walletdir_result["wallets"]):
                await self._load_wallet()
            else:
                # Create and load wallet, then import descriptors
                await self._create_wallet()
                await self._load_wallet()
                asyncio.create_task(self._import_descriptor())  # Import descriptor asynchronously

        except Exception as re:
            logging.error(f"Error initializing bitcoin wallet: {re}")
            raise BitcoinWalletInitError(f"Error initializing bitcoin wallet: {re}")

    async def get_balance(self):
        """
        Retrieves the wallet's balance. If scanning is in progress, logs progress.

        Raises:
            BitcoinWalletValueError : If there is an error getting wallet info.
            Exception: If an unexpected error occurs.
        """
        try:
            wallet_info = await self._make_rpc_request("getwalletinfo", [])

            if not wallet_info:
                logging.error("Bitcoin wallet info is empty.")
                raise BitcoinWalletValueError("Bitcoin wallet info is empty.")

            if "scanning" in wallet_info and wallet_info["scanning"]:
                scanning_info = wallet_info["scanning"]
                if scanning_info and "progress" in scanning_info:
                    logging.warning(f"Bitcoin wallet is scanning: {scanning_info['progress']:.2%}")
                else:
                    logging.warning("Bitcoin wallet is scanning, but progress is unavailable.")
                self.current_balance = None
                self.status = BitcoinWalletStatus.SCANNING
                return None

            elif "balance" in wallet_info:
                self.previous_balance = self.current_balance
                self.current_balance = wallet_info["balance"]
                self.status = BitcoinWalletStatus.OK
                return self.current_balance

            logging.error("Bitcoin wallet info does not contain balance.")
            raise BitcoinWalletValueError("Bitcoin wallet info does not contain balance.")

        except BitcoinWalletValueError as ve:
            logging.error(f"Error getting bitcoin wallet balance: {ve}")
            raise ve

        except Exception as e:
            logging.error(f"Unexpected error getting bitcoin wallet balance: {e}")
