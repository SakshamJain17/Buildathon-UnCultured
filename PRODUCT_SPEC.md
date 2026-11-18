# Alluré: product spec

**One line:** a personal AI stylist you swipe through. It learns your taste, your colours and your idols, dresses you for the weather, shows you in the outfit, finds the best price, and buys it for you when the sale goes live.

## 1. Onboarding: learn the user
- User uploads **3–5 photos** of outfits they think are their best.
- AI extracts: **aesthetic**, **how they dress**, **taste**, **what they like to wear**, **overall dressing sense**.
- AI also extracts **skin tone + undertone**, then builds a **personal colour palette** and a "go easy on" list.
- Optional: user names **style icons** (e.g. Billie Eilish) and how they want to dress.

## 2. Recommendations: the swipe deck
- Deck is ranked by style match + colour match + icon match; each card says *why* it suits the user.

| Gesture | Meaning | What the AI does |
|---|---|---|
| Swipe right | Like | Shows **similar items and outfit options**; boosts those styles |
| Swipe left | Dislike | **Never shows it again**; lowers similar styles |
| Swipe down | Save | Adds it to the saved collection for later |

## 3. Style icons ("dress like…")
- AI asks: "Who do you look up to?" → maps the icon to a style profile (colours, silhouettes, tags).
- Suggests outfits **inspired by the icon but adjusted to the user's own palette and skin tone**.

## 4. Weather-aware daily outfit
- Reads today's weather for the user's location.
- Rain → waterproof jacket + closed shoes. Cold → sweatshirt + jeans + boots. Sunny → sunglasses + light layers.
- Gives a complete outfit (top, bottom, shoes, bag, accessories) with a one-line reason.

## 5. Try-on
- Tap any piece → AI shows the user **wearing it**, using their own photo.
- Colour-theory notes shown alongside ("flatters your warm undertone").

## 6. Buy: best deal and complete the look
- Tap an item → **best price**, **best quality**, **best value** across stores, plus delivery time.
- Recommends **shoes, bag, accessories** that pair with it.

## 7. Wallet and sale auto-buy
- User adds money to an in-app **wallet**, saves the items they want, and sets a target (e.g. "Black Friday").
- When the sale goes live, the app **buys the saved items automatically** and ships to the user's address.

---

## Status right now (4:05 PM; submission 6:30 PM)

| # | Feature | Status |
|---|---|---|
| 1 | Photo upload → aesthetic, taste, skin tone, palette | **Built.** The deeper "AI reads your taste" needs the Claude API key; without it the app uses colour-based fallbacks |
| 2 | Swipe deck, 3 gestures, learns from swipes | **Built.** Dislikes only last until refresh |
| 2b | Right swipe → similar-items strip | **Partly.** The deck re-ranks, but there is no explicit "more like this" strip |
| 3 | Style icons | **Not built** |
| 4 | Weather outfit | **Not built** |
| 5 | Try-on | **Built.** Real AI try-on needs a Gemini key; otherwise a drag-on preview |
| 6 | Best deal + complete the look | **Built.** Prices and ratings are made up |
| 7 | Wallet + sale auto-buy | **Not built** |
| – | Catalog | **58 real H&M products** in `products/`, plus a few drawn items |

## What to do with the remaining time

**Build now (cheap, and big for the demo):**
1. **Weather outfit.** Free weather service, no key needed. About 30 minutes.
2. **Style icons.** A picker of ~8 icons, each mapped to a style profile (Billie Eilish → oversized, black, streetwear). About 30 minutes.
3. **Save dislikes** across refreshes, and a **"more like this"** strip after a right swipe. About 20 minutes.

**Build as a simulation only:**
4. **Wallet + auto-buy.** A wallet screen with a fake balance, a "Black Friday drop" button that "buys" the saved items, and an order confirmation. No real payments in a 4-hour hackathon. Label it "simulated" in the demo and describe it as the roadmap: payments, address and a retailer-checkout integration.

**Do not build:** real payments, accounts, a real sale monitor.

**Pitch order:** onboarding → swipe → icon → weather → try-on → deal → wallet. That's the full story, and the 4 unbuilt pieces fit in about 90 minutes.
