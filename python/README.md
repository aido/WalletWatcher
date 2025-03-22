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

## Setting Up a Firebase Project

1.  **Go to the Firebase Console:** Navigate to [https://console.firebase.google.com/](https://console.firebase.google.com/).
2.  **Create a New Project:** Click "Add project".
3.  **Enter Project Details:**
    * Enter a project name.
    * Accept the Firebase terms.
    * Click "Continue".
4.  **Configure Google Analytics (Optional):**
    * You can enable Google Analytics for your project if you want to track usage.
    * If not, you can disable it and click "Create project".
5.  **Wait for Project Creation:** Firebase will create your project. This might take a few moments.
6.  **Enable Cloud Messaging (FCM):**
    * Once your project is created, click "Continue".
    * In the Firebase console, go to "Project settings" (gear icon in the top left).
    * Go to the "Cloud Messaging" tab.
    * Note the "Server key" (you might need this for some configurations, though the service account is preferred).
7.  **Enable Firestore (if needed):**
    * The Android application stores FCM tokens in Firestore, go to "Firestore Database" in the Firebase console.
    * Click "Create database".
    * Choose "Start in production mode" or "Start in test mode" based on your needs.
    * Select a location for your Firestore database.
    * Click "Enable".

## Obtaining `service-account-key.json`

To enable FCM notifications, you'll need a service account key file from your Google Cloud project:

1.  **Go to the Google Cloud Console:** Navigate to your Google Cloud project at [https://console.cloud.google.com/](https://console.cloud.google.com/).
2.  **Select Your Project:** Choose the project you want to use.
3.  **Service Accounts:** Navigate to "IAM & Admin" > "Service Accounts".
4.  **Create Service Account:** Click "+ CREATE SERVICE ACCOUNT".
5.  **Grant Access:** Give the service account the "Firebase Admin SDK Administrator Service Agent" role, or create a custom role (see below).
6.  **Create Key:** Under the "Keys" tab, click "ADD KEY" > "Create new key".
7.  **Download JSON:** Select "JSON" as the key type and click "CREATE". A `service-account-key.json` file will be downloaded.
8.  **Place the Key:** Move this file to `/etc/walletwatcher/`, or adjust the path in your configuration accordingly.

## Least Privilege Access

To read the FCM tokens stored in Firestore by the mobile device the Python service account needs the "Firebase Admin SDK Administrator Service Agent" role. But for more fine-grained, least privilege access, create a custom role in the Google Cloud Console:

1.  **Go to IAM & Admin > Roles:** [https://console.cloud.google.com/iam-admin/roles](https://console.cloud.google.com/iam-admin/roles)
2.  **Create Role:** Click "+ CREATE ROLE".
3.  **Give it a name:** e.g. "Python Script".
4.  **Add Permissions:** Add the following permissions:
    * `cloudmessaging.messages.create`
    * `datastore.entities.get`
5.  **Save Role:** Click "CREATE".
6.  When creating the service account, assign this custom role instead of "Firebase Admin SDK Administrator Service Agent".

With these permissions, the Python script will only have the necessary access to read FCM tokens from Firestore and send notifications, nothing more.

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

3.  Build the package:

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

* aiohttp>=3.11.0
* cysystemd>=2.0.1
* firebase-admin>=6.7.0

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## Licence

This project is licensed under the MIT Licence - see the [LICENCE](LICENSE) file for details.
