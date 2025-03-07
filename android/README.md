<p align="center"> <img src="../assets/icons/wallet.svg" alt="Wallet Watcher" width="15%" height="15%"></p>

# WalletWatcher Android Application

[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

WalletWatcher is an Android application designed to enable cold wallet balance notifications. Upon installation and device reboot, WalletWatcher retrieves and displays your device's FCM token as a notification. This token is then used to configure a companion application, running on your Bitcoin Core node, which will send notifications about balance changes.

## Features

**FCM Notifications:** Stay informed about your cryptocurrency wallet activity with real-time push notifications. Get alerts for changes in the balance of a cold wallet, or other significant events.
* **FCM Token Display:** When the device is rebooted after the app is installed, the app receives an FCM token. This token is then displayed as a notification.
* **Secure FCM Token Storage:** Your Firebase Cloud Messaging (FCM) tokens are stored securely on your device using Android's SharedPreferences, ensuring that your notification preferences are protected
* **FCM Token Viewing via ADB:** The stored FCM token can be viewed using Android Debug Bridge (ADB).
* **Companion Application Integration:** The FCM token is used in the configuration of the Python companion application running on a Bitcoin Core node, enabling push notifications from the node to this Android app. See the [Python README](../python/README.md) for detailed instructions.


## Technologies Used

* **Kotlin:** The app is built using Kotlin, a modern, concise, and safe programming language that is fully supported by Google for Android development.
* **Android SDK:** The foundation of the app is the Android Software Development Kit, providing the necessary tools and libraries for building native Android applications.
* **Firebase Cloud Messaging (FCM):** We use Firebase Cloud Messaging to receive and handle notifications.
* **FCM Token Persistence:** The received FCM token is stored securely using Android's SharedPreferences, allowing it to persist across app sessions and device reboots.
* **Gradle:** Gradle is the build system used to manage dependencies, compile the code, and package the app for distribution.

## Firebase Setup

This app uses Firebase Cloud Messaging (FCM) to receive FCM tokens. Here's how to set up a Firebase project and enable FCM:

1.  **Create a Firebase Project:**
    * Go to the [Firebase console](https://console.firebase.google.com/).
    * Click "Add project."
    * Follow the on-screen instructions to create a new project.
2.  **Add an Android App:**
    * In your Firebase project, click the Android icon to add an Android app.
    * Enter your app's package name (e.g., `aido.walletwatcher`).
    * Register the app and download the `google-services.json` file.
3.  **Enable Cloud Messaging:**
    * In your Firebase project, go to "Cloud Messaging" under the "Engage" section.
    * Make sure the Cloud Messaging API is enabled.
4.  **Place `google-services.json`:**
    * Move the downloaded `google-services.json` file into the `app/` directory of your Android project.

## Getting Started

These instructions will get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Android Studio installed.
* Android SDK set up.
* A Firebase project set up with FCM enabled (see "Firebase Setup" above).
* A `google-services.json` file downloaded from your Firebase project and placed in the `app/` directory.

### Building and Running

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/aido/WalletWatcher.git](https://github.com/aido/WalletWatcher.git)
    ```
2.  **Open in Android Studio:** Open the project in Android Studio.
3.  **Sync Gradle:** Sync the project with Gradle files.
4.  **Build:** Build the project (Build > Make Project).
5.  **Run:** Run the app on an emulator or a physical device.
6.  **Reboot Device:** After installing the app on the device or emulator, reboot it to trigger the FCM token generation.
7.  **View Notification:** After reboot, a notification will display the FCM token.
8.  **View Token via ADB:**
    * Connect your device or emulator.
    * Open a terminal.
    * Run:
        ```bash
        adb shell
        run-as aido.walletwatcher
        cat shared_prefs/FCM_PREFS.xml
        ```

## Security

* **FCM Token Storage:** FCM tokens are stored securely using SharedPreferences locally on your device. This ensures that your notification preferences are protected.
* **`google-services.json`:** The `google-services.json` file is excluded from version control and should be kept private. This file contains sensitive information about your Firebase project.

## Contributing

We welcome contributions! Please feel free to submit pull requests or open issues to discuss potential changes.

## Licence

This project is licensed under the MIT Licence - see the [LICENCE](LICENSE) file for details.
