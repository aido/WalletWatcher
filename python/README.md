<p align="center"> <img src="../assets/icons/wallet.svg" alt="Wallet Watcher" width="15%" height="15%"></p>

# Python Wallet Watcher

[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python application that periodically checks a Bitcoin wallet's balance and sends real-time notifications via Firebase Cloud Messaging (FCM) when the balance changes. Designed for continuous background operation, it integrates with systemd for reliable service management.

## Features

* **Real-time Bitcoin Wallet Monitoring:** Periodically checks the balance of a specified Bitcoin wallet.
* **FCM Notifications:** Sends instant notifications to your mobile device via Firebase Cloud Messaging (FCM) whenever the wallet balance changes.
* **Systemd Integration:** Designed to run as a systemd service for reliable background operation.
* **Heartbeat Notifications:** Sends a daily heartbeat notification to confirm the watcher is running.
* **Error Handling:** Robust error handling and logging for reliable operation.
* **PID Management:** Manages its own PID file for proper process control.
* **Included Systemd Service File:** A ready-to-use systemd service file is provided in the `systemd/` directory.

## Prerequisites

* Python 3.8 or higher
* A Firebase project with FCM enabled
* A Bitcoin wallet address
* Configuration files for FCM credentials and Bitcoin wallet details

## Obtaining `service-account-key.json`

To enable FCM notifications, you'll need a service account key file from your Firebase project:

1.  **Go to the Firebase Console:** Navigate to your Firebase project at [https://console.firebase.google.com/](https://console.firebase.google.com/).
2.  **Select Your Project:** Choose the project you want to use.
3.  **Project Settings:** Click the gear icon in the top left corner and select "Project settings".
4.  **Service Accounts Tab:** Go to the "Service accounts" tab.
5.  **Generate New Private Key:** Click the "Generate new private key" button.
6.  **Download the Key:** A `service-account-key.json` file will be downloaded to your computer.
7.  **Place the Key:** Move this file to the same directory as your `walletwatcher.conf` file, or adjust the path in your configuration accordingly.

## Installation

1.  Clone the repository:

    ```bash
    git clone git@github.com:aido/WalletWatcher.git
    cd WalletWatcher/python
    ```

2.  Create a virtual environment (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Build the package:

    ```bash
    python3 -m build
    ```

4.  Install the package:

    ```bash
    pip install dist/python-walletwatcher-0.0.1-py3-none-any.whl # or the .tar.gz
    ```

5.  Configure the application:

    * Create `walletwatcher.conf` in the `/etc/walletwatcher` directory with your FCM and Bitcoin wallet details.
    * Place the `service-account-key.json` file in the same directory, or adjust the path in your configuration.

## Systemd Service Installation

1.  Copy the provided service file to `/etc/systemd/system/`:

    ```bash
    sudo cp systemd/wallet-watcher.service /etc/systemd/system/
    ```

2.  Edit the service file:

    ```bash
    sudo nano /etc/systemd/system/wallet-watcher.service
    ```

    * Replace `/path/to/your/venv/` with the actual path to your project directory.
    * Replace `/path/to/your/venv/bin/walletwatcher` with the correct path to the walletwatcher executable inside of the correct virtual environment.
    * Replace `your_user` and `your_group` with the appropriate user and group that will run the service.

3.  Reload systemd:

    ```bash
    sudo systemctl daemon-reload
    ```

4.  Enable the service to start on boot:

    ```bash
    sudo systemctl enable wallet-watcher.service
    ```

5.  Start the service:

    ```bash
    sudo systemctl start wallet-watcher.service
    ```

6.  Check the service status:

    ```bash
    sudo systemctl status wallet-watcher.service
    ```

## Usage

1.  Run the `walletwatcher` command:

    ```bash
    walletwatcher
    ```

2.  (Optional) If using systemd, start the service as described above.

## Configuration

* **`walletwatcher.conf`:** This file contains your FCM credentials and Bitcoin wallet address.
* **Systemd Service:** The `systemd/wallet-watcher.service` file is provided for easy systemd integration.

## Dependencies

* aiohttp
* cysystemd
* google-auth-oauthlib

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## Licence

This project is licensed under the MIT Licence - see the [LICENCE](LICENSE) file for details.
