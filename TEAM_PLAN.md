# Action plan: submission at 6:30 PM

Start the app: `cd ~/Desktop/yc && node server.js`, then open http://localhost:3000

**Do this first (3:35):** find out exactly what the submission needs (a link? a demo video? slides? a GitHub repo?) and write it here: ______________________

---

## Teammate B: real products (no coding needed)

**3:35–4:45: collect 30 products**

1. Open Myntra, Zara, H&M, Ajio or a similar store in Chrome.
2. Find a product. Choose ones that have a **plain white or light-grey background** photo.
3. Right-click the product photo → **Save Image As…**
4. Name the file exactly like this, using **two underscores** between the parts:

   ```
   Product Name__type__price__Brand.jpg
   ```

   Examples:
   ```
   Terracotta Linen Shirt__shirt__1799__Zara.jpg
   Black Cargo Pants__trousers__2499__Snitch.jpg
   White Sneakers__shoes__3999__Adidas.jpg
   ```

5. Save it into the folder **Desktop → yc → products**.

**`type` must be one of these words exactly (lowercase):**
`tee` `shirt` `hoodie` `jacket` `dress` `kurta` `trousers` `skirt` `shoes` `bag` `watch` `cap` `sunglasses`

**Get this mix (30 total):**
- 12 tops (tee, shirt, hoodie, jacket, kurta)
- 6 bottoms (trousers, skirt)
- 4 dresses
- 4 shoes
- 4 accessories (bag, watch, sunglasses, cap)

**Pick many different colours:** earthy (rust, camel, olive), cool (navy, emerald, burgundy), bright (cobalt, mustard), and neutral (white, black, beige). The app matches colours to skin tone, so it needs variety.

**Every 10 products:** tell Aditya, who refreshes the app to check they show up. The colour is read from the photo automatically.

**4:45–5:15:** take 5 full-length outfit photos of one teammate (plain wall behind, good light, face and arms visible). These are for the live demo.

---

## Teammate A: pitch

**3:35–5:00: deck of 6 slides**
1. **Problem:** shopping for clothes means endless scrolling, colours that don't suit you, and lots of returns.
2. **Solution:** swipe for clothes. The AI learns your style **and your skin tone**, so every colour suggested flatters you.
3. **Demo:** screenshots, as a backup in case the live demo fails.
4. **How it works:** 5 photos → style + skin tone + undertone → personal palette → swipe deck that learns → best price + full outfit → try-on.
5. **Business model:** affiliate commission (5–15%) on every purchase, brand-sponsored cards, premium try-ons.
6. **Market and ask:** India's online fashion market, and what you'd build next (live store prices, a bigger catalog).

**5:00–5:30:** record a 90-second screen video of the demo, as a backup and for the submission.

---

## Aditya (you): tech + demo

- **3:35–4:00:** get API keys if the organisers give credits: Anthropic (console.anthropic.com) and Gemini (aistudio.google.com). Start the app with keys:
  `ANTHROPIC_API_KEY=... GEMINI_API_KEY=... node server.js`
  No keys? That's fine. The app works without them, so skip this and don't waste time on it.
- **4:00–5:15:** refresh the app as products arrive. If a product doesn't show up, its file name is wrong (check the `type` word and the `__`).
- **5:15–5:45:** run the full demo with the real outfit photos. Check that the skin tone is right; use the adjust buttons if it isn't.
- **5:45: FEATURE FREEZE.** No more changes.

---

## Everyone

- **5:45–6:15:** rehearse the demo and pitch twice with a timer.
- **6:15:** submit. Don't wait for 6:29.

## The 90-second demo
1. "Shopping for clothes is broken: wrong colours, endless scrolling, returns." (10s)
2. Upload 5 photos → "It worked out my style, my skin tone and undertone, and built my personal colour palette." (20s)
3. Swipe 3–4 cards: right, left, down. "Every card says why it suits *my* skin, and it learns from every swipe." (15s)
4. Tap a card → "Best price across stores, and the whole outfit picked for me." (20s)
5. "Try it on me." (15s)
6. "We earn commission on every sale. Brands get fewer returns; shoppers stop guessing." (10s)

**If a judge asks:** prices are simulated today; in production they come from affiliate APIs.
