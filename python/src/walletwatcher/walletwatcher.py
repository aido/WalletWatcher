import os
import asyncio
import atexit
import signal
import logging
from cysystemd.daemon import notify, Notification
from walletwatcher.pidmanager import PidManager
from walletwatcher.firebase import Firebase, FirebaseInitError, FirebaseValueError
from walletwatcher.bitcoin_wallet import BitcoinWallet, BitcoinWalletValueError, BitcoinWalletInitError, BitcoinWalletStatus

class WalletWatcher:
    def __init__(self):
        """
        Initialises the WalletWatcher with required parameters from a config file or systemd credential file.
        """
        self.is_watching = False # Flag to control the loop
        self.is_systemd = "NOTIFY_SOCKET" in os.environ

    def stop(self, signum, frame):
        """Handles termination signals gracefully."""
        logging.info("Received termination signal.")
        self.is_watching = False  # Set flag to stop loop
        if self.is_systemd:
            notify(Notification.STOPPING)

    async def cleanup(self):
        """Clean up and cancel all ongoing tasks."""
        logging.info("Cleaning up tasks.")
        tasks = {task for task in asyncio.all_tasks() if task is not asyncio.current_task()}

        for task in tasks:
            task.cancel()  # Cancel all outstanding tasks

        await asyncio.gather(*tasks, return_exceptions=True)  # Gather results to ensure clean cancellation

async def async_main():
    """
    Main function to initialise the watcher and periodically check the balance.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    pid = PidManager("/run/walletwatcher.pid")

    # Write PID at startup
    pid.write()
    atexit.register(pid.remove) # Ensure PID file is removed on exit

    # Initialise the WalletWatcher instance
    watcher = WalletWatcher()

    # Register signal handlers
    signal.signal(signal.SIGTERM, watcher.stop)
    signal.signal(signal.SIGINT, watcher.stop)

    # Notify systemd service is starting (Ready)
    if watcher.is_systemd:
        notify(Notification.READY)

    async def heartbeat_task(firebase, bitcoin):
        while watcher.is_watching:
            try:
                if bitcoin.status == BitcoinWalletStatus.INITIALISING:
                    notificationBody = "Initialising"
                    notificationColor =  "#FFA500"
                elif bitcoin.status == BitcoinWalletStatus.SCANNING:
                    notificationBody = "Scanning"
                    notificationColor =  "#FFA500"
                elif bitcoin.status == BitcoinWalletStatus.RPC_FAILURE:
                    notificationBody = "RPC Failure"
                    notificationColor =  "#FF0000"
                elif bitcoin.status == BitcoinWalletStatus.OK:
                    notificationBody = "Watching"
                    notificationColor =  "#00FF00"

                await firebase.send_notification(title = "Status",
                                                body = notificationBody,
                                                icon = "ic_heartbeat",
                                                color = notificationColor,
                                                priority = "default")

            except Exception as e:
                logging.error(f"Heartbeat notification failed: {e}")

            try:
                await asyncio.sleep(86400)  # Sleep for 24 hours

            except asyncio.CancelledError:
                break

        await firebase.send_notification(title = "Status",
                                        body = "Not watching",
                                        icon = "ic_heartbeat",
                                        color = "#FF0000",
                                        priority = "default")

    try:
        # Initialise the Firebase instance
        firebase = Firebase()

        # Initialise the BitcoinWallet instance
        bitcoin = BitcoinWallet()
        await bitcoin.initialise_wallet()

        # If initialise_wallet() succeeds, set is_watching to True
        watcher.is_watching = True

        # Start heartbeat task
        heartbeat_task_instance = asyncio.create_task(heartbeat_task(firebase, bitcoin))

        while watcher.is_watching:
            try:
                await bitcoin.get_balance()
                if bitcoin.current_balance is not None:
                    logging.debug(f"Current bitcoin balance: {bitcoin.current_balance:.8f}")
                    if bitcoin.current_balance != bitcoin.previous_balance:
                        logging.warning(f"Bitcoin balance has changed from {bitcoin.previous_balance:.8f} to {bitcoin.current_balance:.8f}")
                        if bitcoin.current_balance > bitcoin.previous_balance:
                            notificationBody = "Bitcoin balance has increased"
                            notificationColor = "#00FF00"
                        else:
                            notificationBody = "Bitcoin balance has decreased"
                            notificationColor = "#FF0000"

                        await firebase.send_notification(title="Balance Alert",
                                                        body=notificationBody,
                                                        icon = "ic_bitcoin",
                                                        color=notificationColor,
                                                        priority="max")
                if watcher.is_systemd:
                    notify(Notification.WATCHDOG)

                try:
                    await asyncio.sleep(60)  # Sleep for 60 seconds
                except asyncio.CancelledError:
                    break

            except (BitcoinWalletValueError, FirebaseValueError) as ve:
                logging.error(f"Configuration error during loop: {ve}")
                # Continue the while loop
                continue

    except (FirebaseInitError) as re:
        logging.exception(f"Firebase initialisation error: {re}")
        return 1

    except (BitcoinWalletInitError) as re:
        logging.exception(f"Bitcoin wallet initialisation error: {re}")
        await firebase.send_notification(title = "Status",
                                        body = "Bitcoin wallet failed to initialise.\nWatcher has stopped",
                                        icon = "ic_bitcoin",
                                        color = "#FF0000",
                                        priority = "default")
        return 1

    except Exception as e:
        logging.exception(f"Unexpected error occurred: {e}")
        return 1

    else:
        await firebase.send_notification(title = "Status",
                                        body = "Watcher has stopped",
                                        icon = "ic_eye",
                                        color = "#FF0000",
                                        priority = "default")
        logging.info("WalletWatcher stopped.")
        return 0 

    finally:
        await watcher.cleanup()
        logging.info("Shutting down gracefully...")

def main(): #create a non async main, that calls the async main.
    """
    Main entry point for the script.
    """
    return asyncio.run(async_main())

if __name__ == "__main__":
    exit(main())  # Run the script asynchronously and exit.
