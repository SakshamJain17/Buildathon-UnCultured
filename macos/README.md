# ALLURÉ Mac demo launcher

This Apple-silicon macOS 14+ application opens the connected ALLURÉ website in a WebKit window. It is not the native iPhone app and does not include backend/model weights.

Build a development DMG:

```bash
macos/build_dmg.sh https://YOUR-ACTUAL-DEMO-URL
```

Output: backend/runtime/assets/downloads/ALLURE-Prototype.dmg. The landing footer exposes the file when it exists. The launcher requires the selected website/backend host to stay online. It uses an ad-hoc development signature, not Developer ID notarization; it is not a production distribution build. The browser demo is the easiest way for judges to try the product.
