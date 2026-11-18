# Test ALLURE on your iPhone

The native app requires iOS 26 or newer. A development signing team must be configured by the owner in Xcode.

1. Connect the unlocked iPhone to your Mac by cable, and trust the Mac if prompted.
2. Open ios/Allure.xcodeproj.
3. In Xcode Settings > Apple Accounts, sign in with your Apple Account. Select the Allure target > Signing & Capabilities, enable automatic signing and choose your Personal Team. If the bundle identifier is unavailable, choose a unique reverse-domain identifier.
4. Enable Settings > Privacy & Security > Developer Mode on the iPhone and follow the restart prompt.
5. Choose the actual iPhone as Xcode’s run destination, and press Command-R.
6. In the app welcome screen, expand Prototype connection. Use the active public HTTPS demo host as the server URL, without /app or /api/v1. The Mac localhost default works for the simulator, not a physical phone.
7. Enter a name or try the sample walkthrough. Test right/left/down swipes, Saved, the stylist bot and a manual city forecast. Grant photo/location permissions only when choosing those features.

Keep the development Mac, backend, Ollama, Node proxy and tunnel running. The public tunnel address may change when restarted. The Mac DMG does not install on iPhone. TestFlight distribution has not been configured.

Apple setup: https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device
