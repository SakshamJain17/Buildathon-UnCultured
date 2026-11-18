# Alluré demo video: about 2 minutes

Record the screen with your voice. Only show things that work right now. Do **not** open Stylist chat, Hair ideas or Try-on: they need keys or a model and will say "not available".

## Set up (3 minutes, once)
1. Backend running on port 8766 (the team's FastAPI, with `seed_hm_catalogue.py` run so the H&M photos and prices appear).
2. Web server running: `node server.js`, then open **http://localhost:3000** (or the port it prints; during this session it is 3001).
3. Chrome: close other tabs, turn on Do Not Disturb, zoom 100%.
4. For the app part, make the window phone-shaped: right-click → Inspect → device toolbar → iPhone 14 Pro, then close the inspector.
5. Have 3 outfit photos on the Desktop, ready to pick (any clear outfit photos of one person).
6. Do a full dry run once. **Every new browser tab is a fresh user**, so each take starts clean.

## Record
Press **Cmd+Shift+5** → **Record Selected Portion** → Options → **Microphone** → Record. Do the whole thing in one take. Stop from the menu bar. Do two takes; keep the better one.

## Script (say it as you do it)

| Time | On screen | Say |
|---|---|---|
| 0:00 | Landing page hero, slowly scroll | "Choosing what to wear is broken: endless scrolling, colours that don't suit you, and clothes you return. This is Alluré, a personal AI stylist you swipe through." |
| 0:14 | Scroll past the five "how it works" animations | "You show us outfits you love, it learns your taste, you swipe, you see real prices, and it dresses you for the day." |
| 0:24 | Colour guide: click Warm, then Cool | "It suggests a starting palette from your undertone. A guide, never a rule." |
| 0:34 | Click **Open app**, type a name, Continue | "Getting started takes a name. No password, and you can delete everything any time." |
| 0:42 | Pick 2–3 photos, click **Read my colours** | "You add one to five outfits you love. Here it reads the main colours in them, right on this device; with a vision model it reads the clothes too. Photos are never stored." |
| 0:56 | Profile screen, then **Start swiping** (tab: Discover) | "Now it's built around you." |
| 1:02 | Swipe: right, left, then down (use the arrows if dragging is awkward) | "Right to like, left to pass, down to save. A piece you pass on never comes back, and every card says why it was picked." |
| 1:18 | Tap a card: price, then Complete the look | "Real listed prices, and the pieces that finish the outfit with the total. Where we don't know a price, we say so." |
| 1:32 | Today tab → type a city → pick it | "It reads today's weather for your city and builds an outfit that makes sense for it. Location is opt-in and never stored." |
| 1:46 | You → Style inspirations → add one (e.g. Hailey Bieber) → Discover | "Tell it who you dress like and your feed shifts toward that style." |
| 1:56 | Saved tab | "And everything you saved is waiting here." |
| 2:02 | Back to the landing page closing line | "Alluré: find your kind of style. We earn when you buy, and brands see fewer returns." |

## If something fails mid-take
Stop, reload, start a new take. Don't try to fix it live. If the backend isn't connected, the app shows an "Offline demo" badge, so check it is **"Backend connected"** before you record.

## Be honest if asked
- Photo analysis, try-on, live price comparison and the stylist chat run when the backend has those providers configured; they need keys.
- Wallet auto-buy, sale alerts and wardrobe auto-tagging are the roadmap, not built.
- Prices in the demo are H&M's listed prices on the day we collected them; the backend never invents prices.
