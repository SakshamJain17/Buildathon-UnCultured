# ALLURÉ for iPhone

Native SwiftUI prototype for iOS 26+, with no third-party app dependencies. Developed using the installed Xcode 27.2 SDK, built for iOS Simulator 27.2; an actual iOS 26 runtime was not installed, so iOS 26 execution has not been verified.

## Open it without learning Xcode

1. Start the backend (instructions in repository README) on port 8766; leave that terminal running.
2. Open `ios/Allure.xcodeproj` in Xcode.
3. Choose **Allure** as the scheme and an installed iPhone simulator in the destination menu.
4. Press **Command + R**. The app opens in the simulated iPhone.
5. Enter a name and tap **Meet your stylist**. Simulator backend URL is http://127.0.0.1:8766.
6. Choose a city in Today; try the swipe feed, add a wardrobe photo, and ask the stylist.

On the development Mac Xcode uses Device Hub; the standalone Simulator.app is not present. A simulator device can also be booted with `xcrun simctl boot <device-id>` and inspected in Device Hub. Desktop automation requires the relevant computer-use permission; command-line install/launch/screenshot does not verify mouse interactions.

## App screens

- Discover weather button: actual weather and an explained outfit, with manual city and opt-in location.
- Discover: swipe/accessible buttons, persistent left-swipe dismissal, saved items and provider-dependent live search.
- Wardrobe: selected-photo upload with user-entered labels, authenticated thumbnails, deletion and basic owned-item outfits.
- Persistent Allure bot: local Ollama/Gemini answers, real preference/feedback actions, tool trace and feature navigation. Available from the bottom accessory and product details.
- Saved: persisted saved pieces.
- You: progress counts and collapsed controls for explicit style, user-selected celebrity/creator inspiration tags, five-reference photo analysis, hairstyle ideas, optional colour exploration and profile deletion.
- Fitting room: two explicit photo selections, consent, provider submission and polling. FASHN key needed; no dummy generated output.

No automatic access to the entire photo library. Photo picker loads only chosen items. Location is one-shot when requested; there is no background tracking or push-notification scheduling.

## Build from terminal

From repo root:

```bash
xcodebuild -project ios/Allure.xcodeproj -scheme Allure \
  -sdk iphonesimulator -configuration Debug -derivedDataPath ios/.build \
  CODE_SIGNING_ALLOWED=NO build
```

Project file is tracked. Regenerate it with `python3 ios/scripts/create_project.py` only after adding/removing Swift source files. Build output and screenshots are ignored.

The Debug-only `--allure-sample` launch argument adds labelled sample wardrobe/interactions to the existing session once. First-time users can choose “Try the sample walkthrough.” Neither automatically requests location access.

## Verify Swift API decoding against the backend

```bash
swiftc ios/Allure/Models.swift ios/Allure/API.swift ios/scripts/VerifyAPI.swift -o ios/.build/verify-api
ios/.build/verify-api
```

This creates and deletes an isolated test session, checks native request/response decoding, a durable dislike, live city lookup and weather. It is not a UI interaction test.

## Real iPhone

Use a reachable HTTPS backend for deployment. For local development, run the backend on an appropriate LAN interface and enter the Mac's local address in Prototype connection; this exposes the development server to that network, so use only a trusted local network. The current plist permits local networking, not arbitrary insecure internet endpoints. Device installation needs your own Apple development signing team in Xcode; no signing account was configured automatically.

## Known limitations

Backend must remain running. Tokens are Keychain-backed prototype sessions, not recoverable production accounts. An expired/deleted session requires reconnection and a new profile; dislike persistence is profile-scoped. Celebrity follows use the tags chosen by the user, not actual celebrity recommendations. Hair advice uses entered length/texture/goal, not face or photo analysis. Daily styling now considers private wardrobe labels along with shared catalogue references; full compatibility remains an initial heuristic. Vision, live shopping and try-on require the appropriate configured providers. No TestFlight or App Store deployment has been performed.
