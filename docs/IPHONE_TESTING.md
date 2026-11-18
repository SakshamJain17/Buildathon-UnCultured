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

## No cable: use the hosted web app with the real AI stylist

Open https://allure-sakshamjain17s-projects.vercel.app/app in Safari. Choose Explore with a reference profile for labelled sample wardrobe data. Open Try the live demo for a four-step interactive guide, or tap Ask Allure to do it. Suggested prompt: "Read my wardrobe and build an outfit from what I own." Try-on generation is unavailable; local text/vision AI, wardrobe tools, weather and shopping use the configured backend. Add the web app to the Home Screen from Safari's Share menu for a standalone window. This is a web app shortcut, not the native Swift app.

The frontend and logo are hosted on Vercel. API requests proxy to the active Cloudflare tunnel, so keep the development Mac, FastAPI, Ollama, Node proxy and tunnel running. If the tunnel changes, rebuild the static package with web/build_static.py --backend NEW_HTTPS_ORIGIN and redeploy. No provider keys belong in the static package.

On new physical-device installs, the native app now defaults to the Vercel server URL. An existing install may retain its previous Prototype connection value; update it there if needed.
