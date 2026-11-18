#!/bin/zsh
set -eu
# Pass a working website URL; the launcher does not bundle a backend or model weights.
cd "$(dirname "$0")/.."
ALLURE_WEBSITE_URL="${1:-http://localhost:8790}"
mkdir -p macos/.build/ALLURE.app/Contents/MacOS backend/runtime/assets/downloads
swiftc -parse-as-library -target arm64-apple-macos14.0 macos/AllureDesktop.swift -o macos/.build/ALLURE.app/Contents/MacOS/ALLURE
ALLURE_WEBSITE_URL="$ALLURE_WEBSITE_URL" python3 - <<'PY'
import plistlib,os
from pathlib import Path
info={'CFBundleName':'ALLURE','CFBundleDisplayName':'ALLURÉ','CFBundleIdentifier':'app.allure.desktop.prototype','CFBundleExecutable':'ALLURE','CFBundlePackageType':'APPL','CFBundleVersion':'1','CFBundleShortVersionString':'0.2','LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,'AllureWebsiteURL':os.environ['ALLURE_WEBSITE_URL'],'NSAppTransportSecurity':{'NSAllowsLocalNetworking':True},'NSLocationWhenInUseUsageDescription':'Optional location for local weather styling.'}
Path('macos/.build/ALLURE.app/Contents/Info.plist').write_bytes(plistlib.dumps(info))
PY
codesign --force --deep --sign - macos/.build/ALLURE.app
mkdir -p macos/.build/package
# Reversible packaging copy; no application files outside this repo are modified.
ditto macos/.build/ALLURE.app macos/.build/package/ALLURE.app
ln -sfn /Applications macos/.build/package/Applications
hdiutil create -volname ALLURE -srcfolder macos/.build/package -ov -format UDZO backend/runtime/assets/downloads/ALLURE-Prototype.dmg
