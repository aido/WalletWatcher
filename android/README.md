<p align="center"> <img src="../assets/icons/wallet.svg" alt="Wallet Watcher" width="15%" height="15%"></p>

# WalletWatcher Android Application

[![Licence: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

WalletWatcher is an Android application designed to enable cold wallet balance notifications. Upon installation and device reboot, WalletWatcher retrieves and displays your device's FCM token as a notification. This token is then used to configure a companion application, running on your Bitcoin Core node, which will send notifications about balance changes.

## Features

* **FCM Notifications:** Stay informed about your cryptocurrency wallet activity with real-time push notifications. Get alerts for changes in the balance of a cold wallet, or other significant events.
* **FCM Token Display:** When the device is rebooted after the app is installed, the app receives an FCM token. This token is then displayed as a notification.
* **Secure FCM Token Storage:** Your Firebase Cloud Messaging (FCM) tokens are stored securely in Cloud Firestore, ensuring that your notification preferences are protected.
* **Companion Application Integration:** The FCM token is used in the configuration of the Python companion application running on a Bitcoin Core node, enabling push notifications from the node to this Android app. See the [Python README](../python/README.md) for detailed instructions.

## Technologies Used

* **Kotlin:** The app is built using Kotlin, a modern, concise, and safe programming language that is fully supported by Google for Android development.
* **Android SDK:** The foundation of the app is the Android Software Development Kit, providing the necessary tools and libraries for building native Android applications.
* **Firebase Cloud Messaging (FCM):** We use Firebase Cloud Messaging to receive and handle notifications.
* **Cloud Firestore:** The received FCM token is stored securely in Cloud Firestore, allowing it to persist across app sessions and device reboots.
* **Gradle:** Gradle is the build system used to manage dependencies, compile the code, and package the app for distribution.

## Firebase Setup

This app uses Firebase Cloud Messaging (FCM) and Cloud Firestore. Here's how to set up a Firebase project and enable FCM and Firestore:

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
4.  **Enable Firestore:**
    * In your Firebase project, go to "Firestore Database" under the "Build" section.
    * Click "Create database."
    * Choose "Start in production mode" or "Start in test mode" based on your needs.
    * Select a location for your Firestore database.
    * Click "Enable."
5.  **Place `google-services.json`:**
    * Move the downloaded `google-services.json` file into the `app/` directory of your Android project.
6.  **Enable Anonymous Authentication in Firebase Console:**
    * Open your Firebase project in the Firebase console.
    * In the left-hand menu, click on "Authentication."
    * Select the "Sign-in method" tab.
    * Find the "Anonymous" sign-in provider.
    * Toggle the switch to enable it.
    * Make sure to save your changes.

## Google Cloud Setup

1.  **Grant Service Account Token Creator Role:**
    * To allow the Android application to create FCM tokens, you need to grant the "Service Account Token Creator" role.
    * Go to the [Google Cloud Console](https://console.cloud.google.com/).
    * Navigate to "IAM & Admin" > "IAM".
    * Locate the service account associated with your Firebase project.
    * Click the pencil icon to edit permissions.
    * Click "ADD ANOTHER ROLE".
    * Search for and select "Service Account Token Creator".
    * Click "Save".
2.  **Firestore Security Rules:**
    * The default Firestore rules are restrictive. To allow the Android app to write FCM tokens, update the rules:
        ```rules
        rules_version = '2';
        service cloud.firestore {
            match /databases/{database}/documents {
                match /fcm_tokens/{deviceId} {
                    // Deny delete and read
                    allow delete, read: if false;
                    // Allow only Wallet Watcher app to write tokens
                    allow create, update: if request.auth != null
                                        && request.auth.token.aud == "YOUR_PROJECT_ID"
                                        && request.resource.data.timestamp is timestamp
                                        && request.resource.data.token is string;
                }
                match /{document=**} {
                    allow read, write: if false;
                }
            }
        }
        ```
    * Replace `YOUR_PROJECT_ID` with your actual Firebase project ID.
    * These rules allow only authenticated requests from your app to write tokens, ensuring security.

## Getting Started

These instructions will get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Android Studio installed.
* Android SDK set up.
* A Firebase project set up with FCM and Firestore enabled (see "Firebase Setup" above).
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

## Security

* **Firestore Storage:** FCM tokens are stored securely in Cloud Firestore.
* **`google-services.json`:** The `google-services.json` file is excluded from version control and should be kept private. This file contains sensitive information about your Firebase project.
* **Firestore Security Rules:** The provided Firestore rules ensure that only your application can write FCM tokens.

## Battery Optimization Warning

Android's battery optimization features can sometimes interfere with the proper functioning of this app as a background service. If you experience issues such as:

* Service unexpectedly stopping
* App icon disappearing
* Inconsistent background operation

It's likely that battery optimization is affecting the app.

**Recommended Action:**

To ensure the app runs reliably, please exclude it from battery optimization:

1.  Go to your device's **Settings**.
2.  Navigate to **Apps**.
3.  Find and select "Wallet Watcher".
4.  Tap on **Battery**.
5.  Choose **Battery optimization**.
6.  Select **All apps** from the dropdown menu (if available).
7.  Find "Wallet Watcher" in the list.
8.  Select **Don't optimize**.

> [!NOTE]
> The exact steps might vary slightly depending on your Android version and device manufacturer.

## Contributing

We welcome contributions! Please feel free to submit pull requests or open issues to discuss potential changes.

## Licence

This project is licensed under the MIT Licence - see the [LICENCE](LICENSE) file for details.
