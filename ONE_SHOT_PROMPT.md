# One-shot prompt: rebuild Alluré (website + app + backend wiring) exactly

Paste everything below the line into a coding agent (Claude Code or similar) in an empty folder.

---

You are a coding agent. Create the exact project described below, run it, and confirm it works. Do not redesign, rename or "improve" anything: reproduce every file below byte for byte. The brand is **Alluré** (with the é); the tagline is "Find your kind of style."

## What Alluré is
A personal AI stylist, "Tinder for clothes", in two parts:
1. **Website** (`/`): a minimal + editorial landing page (warm off-white, black Playfair Display serif headlines, Inter body, big section numbers, thin black rules, square corners) with a hero whose words rise in, three floating product cards with parallax, a product marquee, five animated "how it works" graphics, an interactive colour guide (warm/cool/neutral undertone → palette), a feature grid, a live phone-framed demo of the app, and a closing call to action.
2. **App** (`/app`): a mobile-first app in the same style: splash, welcome (name → session), upload 1–5 outfit photos, bottom tab bar (Discover, Today, Stylist, Saved, You), swipe deck (right = like, left = dislike, down = save), bottom sheets for item detail and try-on, weather outfit, stylist chat, colour guide, style inspirations, wardrobe, hair ideas, delete-my-data.

## Architecture
- Zero dependencies: Node 18+ and plain HTML/CSS/JS. `server.js` serves `/` (landing.html), `/app` (app.html), `/products/<file>` (+ `/api/products`) and **reverse-proxies `/api/v1/*` to the team's FastAPI backend** (default `http://127.0.0.1:8766`, override with `BACKEND_URL`). Same origin, so no CORS setup and no keys in the browser.
- **The backend** is the team repo's `backend/` (FastAPI, Python 3.12+, SQLite): https://github.com/SakshamJain17/Buildathon-UnCultured (read `docs/BACKEND_BLUEPRINT.md` and `docs/API_CONTRACT.md`). Run it with `cd backend && pip install -r requirements.txt && uvicorn app.main:app --port 8766`.
- The app auto-detects the backend through `GET /api/v1/health`. If unreachable it runs an **offline demo** on sample data and says so.

## Backend facts the frontend must respect (do not fake any of these)
- Every response is `{success,data,error,request_id}`; sessions are name-only (`POST /sessions`) with a bearer token kept in `sessionStorage`; 401 means start a new session.
- Swipes are `like / dislike / save` with an `Idempotency-Key` header (same key on retries). Disliked items never return.
- Catalogue scores are relative rankings, not percentages; show the backend `reasons`. Demo fixtures have `is_demo:true` and null price/image: show a drawn colour placeholder and "Demo item · no price". Never invent prices.
- Weather is read by the backend (`/stylist/daily`); location is opt-in, rounded to 2 decimals, with city search (`/locations/search`) as the fallback. `occasion_applied:false` is shown.
- Colour guide is user-chosen undertone + consent (`/style/palette`). There is **no photo-based skin analysis**.
- Photo analysis (`/style/analyze`) needs a vision model (`health.providers.vision`). Try-on needs FASHN (`tryon`), live offers need SerpApi (`shopping`), the stylist chat needs Ollama/Gemini (`agent`). When off, the UI says so plainly and offers what it can.
- There is **no checkout or wallet** in the backend; those are listed as "Coming next", never shown as working.

## Upload rule: 1 to 5 photos (max 5)
The upload accepts one to five photos. With a vision model they go to `POST /style/analyze`. The original backend insists on exactly five images, so the frontend retries once with the photos repeated to fill five slots when it gets `IMAGE_COUNT`. `backend_accept_1_to_5_images.patch` (below) makes 1–5 native; apply it from the repo root with `git apply backend_accept_1_to_5_images.patch`. With no vision model, the app reads the main colours of the photos on the device (nothing uploaded) and saves them as colour preferences via `PUT /me/preferences`.

## Folder layout
```
server.js   landing.html   app.html   seed_hm_catalogue.py   backend_accept_1_to_5_images.patch
products/   (58 photos named Name__type__price__Brand.jpg)
```

## Step 1: `server.js`
~~~js
// Zero-dependency web server for Alluré's website and app.
//   /            marketing site (landing.html)
//   /app         the product (app.html)
//   /products/*  product photos (+ /api/products lists them)
//   /api/v1/*    reverse proxy to the team's FastAPI backend (same origin: no CORS setup, tokens never leave this machine)
// Run: node server.js        Backend: BACKEND_URL=http://127.0.0.1:8766 (default)
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const BACKEND = new URL(process.env.BACKEND_URL || 'http://127.0.0.1:8766');
const PRODUCTS = path.join(__dirname, 'products');

const send = (res, code, obj) => { res.writeHead(code, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(obj)); };
const page = (res, file) => { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); fs.createReadStream(path.join(__dirname, file)).pipe(res); };

function proxy(req, res) { // streams multipart uploads and binary responses (wardrobe images) untouched
  const upstream = http.request({ hostname: BACKEND.hostname, port: BACKEND.port, path: req.url, method: req.method, headers: { ...req.headers, host: BACKEND.host } }, (r) => {
    res.writeHead(r.statusCode, r.headers); r.pipe(res);
  });
  upstream.on('error', () => send(res, 502, { success: false, error: { code: 'BACKEND_UNREACHABLE', message: 'The Alluré backend is not reachable.' }, request_id: 'proxy' }));
  req.pipe(upstream);
}

http.createServer((req, res) => {
  try {
    const url = req.url.split('?')[0];
    if (req.url.startsWith('/api/v1/')) return proxy(req, res);
    if (req.method !== 'GET') return send(res, 405, { error: 'method not allowed' });
    if (url === '/api/products') {
      const files = fs.existsSync(PRODUCTS) ? fs.readdirSync(PRODUCTS).filter((f) => /\.(jpe?g|png|webp|avif)$/i.test(f)) : [];
      return send(res, 200, files);
    }
    if (url.startsWith('/products/')) {
      const file = path.join(PRODUCTS, path.basename(decodeURIComponent(url.slice(10)))); // basename blocks ../ escapes
      if (!fs.existsSync(file)) return send(res, 404, { error: 'not found' });
      const ext = path.extname(file).slice(1).toLowerCase();
      res.writeHead(200, { 'Content-Type': 'image/' + (ext === 'jpg' ? 'jpeg' : ext), 'Cache-Control': 'public, max-age=3600' });
      return fs.createReadStream(file).pipe(res);
    }
    if (url === '/app' || url === '/app.html') return page(res, 'app.html');
    if (url === '/' || url === '/index.html') return page(res, 'landing.html');
    send(res, 404, { error: 'not found' });
  } catch (e) {
    console.error(e);
    send(res, 500, { error: e.message });
  }
}).listen(PORT, () => console.log(`Alluré on http://localhost:${PORT}  (backend: ${BACKEND.origin})`));

~~~

## Step 2: `landing.html`
~~~html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alluré — your personal AI stylist</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
<style>
  :root { --bg:#f4f2ee; --ink:#111; --mute:#77736b; --line:#d9d6cf; --panel:#ebe8e2;
          --serif:"Playfair Display","Iowan Old Style",Georgia,serif; --sans:"Inter",-apple-system,system-ui,sans-serif; --pad:clamp(20px,5vw,72px); }
  * { box-sizing:border-box; margin:0; padding:0; }
  html { scroll-behavior:smooth; }
  body { background:var(--bg); color:var(--ink); font:16px/1.6 var(--sans); -webkit-font-smoothing:antialiased; overflow-x:hidden; }
  a { color:inherit; text-decoration:none; } img { display:block; }
  .progress { position:fixed; top:0; left:0; height:3px; background:var(--ink); width:0; z-index:100; }
  /* nav */
  nav { position:fixed; top:0; left:0; right:0; z-index:50; display:flex; align-items:center; justify-content:space-between; padding:18px var(--pad); transition:.3s; }
  nav.solid { background:#f4f2eee6; backdrop-filter:blur(10px); border-bottom:1px solid var(--line); padding-top:12px; padding-bottom:12px; }
  .logo { font:600 28px var(--serif); letter-spacing:-.02em; } .logo i { font-weight:400; }
  nav .links { display:flex; gap:32px; font:600 11px var(--sans); letter-spacing:.16em; text-transform:uppercase; }
  nav .links a { position:relative; } nav .links a::after { content:""; position:absolute; left:0; bottom:-4px; height:1px; width:0; background:var(--ink); transition:.3s; } nav .links a:hover::after { width:100%; }
  .btn { display:inline-block; font:600 12px var(--sans); letter-spacing:.14em; text-transform:uppercase; padding:17px 30px; background:var(--ink); color:#fff; border:1px solid var(--ink); transition:.25s; cursor:pointer; position:relative; overflow:hidden; }
  .btn:hover { transform:translateY(-3px); box-shadow:0 12px 0 -6px #0003; }
  .btn.ghost { background:transparent; color:var(--ink); } .btn.ghost:hover { background:var(--ink); color:#fff; }
  .btn.sm { padding:11px 18px; }
  /* reveal */
  .reveal { opacity:0; transform:translateY(40px); transition:opacity .9s cubic-bezier(.2,.7,.2,1), transform .9s cubic-bezier(.2,.7,.2,1); transition-delay:var(--d,0s); }
  .reveal.in { opacity:1; transform:none; }
  .kicker { font:700 12px var(--sans); letter-spacing:.18em; text-transform:uppercase; color:var(--mute); }
  .kicker b { font:600 56px/1 var(--serif); letter-spacing:-.03em; color:var(--ink); margin-right:14px; vertical-align:-8px; }
  h2.big { font:600 clamp(36px,6vw,84px)/1.02 var(--serif); letter-spacing:-.03em; margin-top:18px; max-width:15ch; } h2.big i { font-weight:400; }
  section { padding:clamp(70px,11vw,150px) var(--pad); position:relative; }
  hr.rule { border:0; border-top:1px solid var(--ink); margin:0 var(--pad); }
  /* hero */
  .hero { min-height:100vh; display:grid; grid-template-columns:1.15fr .85fr; gap:40px; align-items:center; padding-top:130px; overflow:hidden; }
  .hero h1 { font:600 clamp(48px,9vw,142px)/.94 var(--serif); letter-spacing:-.045em; }
  .hero h1 .w { display:inline-block; overflow:hidden; vertical-align:bottom; padding-bottom:.08em; } .hero h1 .w span { display:inline-block; transform:translateY(110%); animation:rise 1.1s cubic-bezier(.2,.8,.2,1) forwards; animation-delay:calc(.15s * var(--i)); }
  .hero h1 em { font-weight:400; }
  @keyframes rise { to { transform:none; } }
  .hero p.lead { max-width:44ch; margin:30px 0 36px; color:var(--mute); font-size:18px; opacity:0; animation:fadeup 1s .9s forwards; }
  .hero .cta { display:flex; gap:12px; flex-wrap:wrap; opacity:0; animation:fadeup 1s 1.1s forwards; }
  @keyframes fadeup { from { opacity:0; transform:translateY(20px);} to { opacity:1; transform:none; } }
  .stack { position:relative; height:min(66vh,560px); }
  .pcard { position:absolute; width:56%; aspect-ratio:3/4; background:var(--panel) center/cover; border:1px solid var(--ink); box-shadow:14px 14px 0 #0000000d; will-change:transform; }
  .pcard::after { content:attr(data-name); position:absolute; left:0; right:0; bottom:0; background:#fff; border-top:1px solid var(--ink); padding:8px 12px; font:600 15px var(--serif); }
  .pcard:nth-child(1) { left:0; top:6%; --r:-7deg; animation:float 7s ease-in-out infinite; }
  .pcard:nth-child(2) { right:0; top:0; --r:5deg; animation:float 8s -2s ease-in-out infinite; z-index:2; }
  .pcard:nth-child(3) { left:22%; bottom:0; --r:-2deg; animation:float 9s -4s ease-in-out infinite; z-index:3; }
  @keyframes float { 0%,100% { transform:translateY(0) rotate(var(--r)); } 50% { transform:translateY(-18px) rotate(calc(var(--r) * -.4)); } }
  .scrollcue { position:absolute; left:var(--pad); bottom:28px; font:700 10px var(--sans); letter-spacing:.2em; text-transform:uppercase; color:var(--mute); display:flex; gap:12px; align-items:center; }
  .scrollcue::after { content:""; width:1px; height:44px; background:var(--ink); transform-origin:top; animation:cue 2s ease-in-out infinite; }
  @keyframes cue { 0% { transform:scaleY(0);} 50% { transform:scaleY(1);} 100% { transform:scaleY(1); opacity:0; } }
  /* marquee */
  .marquee { border-block:1px solid var(--ink); overflow:hidden; padding:22px 0; background:var(--bg); }
  .marquee .track { display:flex; gap:56px; width:max-content; animation:slide 40s linear infinite; align-items:center; }
  .marquee:hover .track { animation-play-state:paused; }
  .marquee span { font:italic 400 clamp(28px,4vw,52px) var(--serif); white-space:nowrap; }
  .marquee img { height:88px; width:66px; object-fit:cover; border:1px solid var(--ink); }
  @keyframes slide { to { transform:translateX(-50%); } }
  /* steps */
  .steps { margin-top:70px; border-top:1px solid var(--ink); }
  .step { display:grid; grid-template-columns:90px 1fr 1fr; gap:32px; align-items:center; padding:48px 0; border-bottom:1px solid var(--line); }
  .step .n { font:600 54px/1 var(--serif); letter-spacing:-.03em; }
  .step h3 { font:600 clamp(26px,3vw,40px)/1.1 var(--serif); letter-spacing:-.02em; margin-bottom:10px; } .step p { color:var(--mute); max-width:40ch; }
  .viz { height:220px; background:var(--panel); border:1px solid var(--line); position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; }
  /* viz: photos */
  .v-slots { display:flex; gap:10px; } .v-slots i { width:46px; height:70px; border:1px solid var(--line); background:#fff; transform:scale(.6); opacity:0; }
  .in .v-slots i { animation:pop .5s cubic-bezier(.2,.9,.3,1.4) forwards; animation-delay:calc(.25s * var(--k)); } .in .v-slots i:nth-child(odd) { background:#cdbfa8; } .in .v-slots i:nth-child(even) { background:#9aa38c; }
  @keyframes pop { to { transform:none; opacity:1; } }
  /* viz: palette */
  .v-pal { display:flex; gap:8px; } .v-pal i { width:38px; height:96px; transform:scaleY(0); transform-origin:bottom; }
  .in .v-pal i { animation:grow .7s cubic-bezier(.2,.8,.2,1) forwards; animation-delay:calc(.12s * var(--k)); } @keyframes grow { to { transform:none; } }
  /* viz: swipe */
  .v-swipe .c { position:absolute; width:110px; height:150px; background:#fff center/cover; border:1px solid var(--ink); animation:swipe 5s ease-in-out infinite; }
  .v-swipe .t { position:absolute; top:22px; font:700 13px var(--sans); letter-spacing:.2em; padding:3px 10px; border:2px solid; opacity:0; background:#fffd; }
  .v-swipe .t.l { right:18%; color:#1e7a4c; animation:tl 5s infinite; } .v-swipe .t.r { left:18%; color:#b3261e; animation:tr 5s infinite; } /* LIKE shows on the right where the card exits */
  @keyframes swipe { 0%,8% { transform:none; } 28%,36% { transform:translateX(150px) rotate(18deg); opacity:0; } 37% { transform:translateX(0) scale(.9); opacity:0; } 46%,54% { transform:none; opacity:1; } 74%,82% { transform:translateX(-150px) rotate(-18deg); opacity:0; } 83% { transform:translateX(0) scale(.9); opacity:0; } 92%,100% { transform:none; opacity:1; } }
  @keyframes tl { 0%,12% { opacity:0; } 22%,30% { opacity:1; } 36%,100% { opacity:0; } } @keyframes tr { 0%,58% { opacity:0; } 68%,76% { opacity:1; } 82%,100% { opacity:0; } }
  /* viz: deals */
  .v-deals { width:78%; display:grid; gap:10px; } .v-deals div { height:18px; background:#d4cfc4; transform:scaleX(0); transform-origin:left; position:relative; }
  .in .v-deals div { animation:grow .9s cubic-bezier(.2,.8,.2,1) forwards; animation-delay:calc(.15s * var(--k)); } .v-deals div.best { background:var(--ink); }
  .v-deals div::after { content:attr(data-p); position:absolute; right:8px; top:0; font:600 10px/18px var(--sans); color:#fff; } .v-deals div:not(.best)::after { color:#333; }
  /* viz: tryon */
  .v-try { width:100px; height:170px; background:linear-gradient(#cfc7b8,#a79d8a); position:relative; border:1px solid var(--ink); } .v-try::before { content:""; position:absolute; left:24px; top:44px; width:52px; height:84px; background:#6e1f2c; clip-path:polygon(20% 0,80% 0,100% 30%,86% 44%,86% 100%,14% 100%,14% 44%,0 30%); opacity:0; transition:1s .6s; } .in .v-try::before { opacity:1; }
  .v-try::after { content:""; position:absolute; left:-10%; right:-10%; height:2px; background:#fff; box-shadow:0 0 14px 2px #fff; animation:scan 2.6s ease-in-out infinite; } @keyframes scan { 0%,100% { top:4%; } 50% { top:94%; } }
  /* colour lab */
  .lab { background:var(--ink); color:#f4f2ee; } .lab .kicker { color:#a39e92; } .lab .kicker b { color:#f4f2ee; }
  .lab-grid { display:grid; grid-template-columns:1fr 1fr; gap:60px; align-items:center; margin-top:50px; }
  .tones { display:flex; gap:14px; margin:30px 0 8px; } .tones button { padding:14px 22px; border:1px solid #ffffff66; background:transparent; color:#f4f2ee; font:600 11px var(--sans); letter-spacing:.16em; text-transform:uppercase; cursor:pointer; transition:.25s; } .tones button.on { background:#f4f2ee; color:#111; }
  .lab p { color:#b5b0a4; max-width:42ch; } .lab p.say { color:#f4f2ee; font:italic 400 24px var(--serif); margin-top:22px; min-height:3.2em; }
  .pal { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; height:340px; } .pal i { display:block; transform-origin:bottom; transition:transform .6s cubic-bezier(.2,.8,.2,1), background .6s; } .pal i.swap { transform:scaleY(.15); }
  .pal i:nth-child(1) { margin-top:0; } .pal i:nth-child(2) { margin-top:36px; } .pal i:nth-child(3) { margin-top:12px; } .pal i:nth-child(4) { margin-top:60px; } .pal i:nth-child(5) { margin-top:24px; }
  .avoidline { margin-top:14px; font:600 10px var(--sans); letter-spacing:.16em; text-transform:uppercase; color:#a39e92; }
  /* features */
  .feat { display:grid; grid-template-columns:repeat(3,1fr); gap:0; margin-top:70px; border:1px solid var(--ink); }
  .feat div { padding:34px 28px 40px; border-right:1px solid var(--ink); border-bottom:1px solid var(--ink); transition:.3s; position:relative; }
  .feat div:nth-child(3n) { border-right:0; } .feat div:nth-last-child(-n+3) { border-bottom:0; }
  .feat div:hover { background:var(--ink); color:#fff; } .feat div:hover p { color:#c9c4b8; }
  .feat small { font:700 10px var(--sans); letter-spacing:.18em; text-transform:uppercase; color:var(--mute); } .feat h4 { font:600 26px/1.15 var(--serif); margin:44px 0 10px; letter-spacing:-.01em; } .feat p { color:var(--mute); font-size:14px; }
  .tag-soon { position:absolute; top:30px; right:24px; border:1px solid currentColor; padding:2px 7px; font:700 9px var(--sans); letter-spacing:.14em; text-transform:uppercase; }
  /* demo */
  .demo { display:grid; grid-template-columns:1fr auto; gap:60px; align-items:center; }
  .phone { width:340px; height:700px; background:#111; border-radius:46px; padding:12px; box-shadow:0 40px 80px -30px #0006; position:relative; }
  .phone::before { content:""; position:absolute; top:20px; left:50%; width:90px; height:24px; background:#111; border-radius:20px; transform:translateX(-50%); z-index:3; }
  .phone iframe { width:100%; height:100%; border:0; border-radius:36px; background:var(--bg); }
  .demo ul { list-style:none; margin:34px 0; display:grid; gap:14px; } .demo li { padding-left:28px; position:relative; color:var(--mute); } .demo li::before { content:"→"; position:absolute; left:0; color:var(--ink); }
  /* cta */
  .final { text-align:center; padding-block:clamp(90px,14vw,200px); }
  .final h2 { font:600 clamp(48px,11vw,170px)/.94 var(--serif); letter-spacing:-.045em; } .final h2 i { font-weight:400; } .final .btn { margin-top:44px; padding:22px 44px; }
  footer { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; padding:26px var(--pad); border-top:1px solid var(--ink); font:600 10px var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--mute); }
  @media (max-width:860px) {
    nav .links { display:none; } .hero { grid-template-columns:1fr; padding-top:110px; } .stack { height:420px; margin-top:50px; } .scrollcue { display:none; }
    .step { grid-template-columns:1fr; gap:16px; padding:36px 0; } .lab-grid, .demo { grid-template-columns:1fr; gap:36px; } .pal { height:220px; }
    .feat { grid-template-columns:1fr; } .feat div { border-right:0 !important; border-bottom:1px solid var(--ink) !important; } .feat div:last-child { border-bottom:0 !important; }
    .demo .phone { margin:0 auto; } .kicker b { font-size:44px; }
  }
  @media (prefers-reduced-motion:reduce) { *, *::before, *::after { animation:none !important; transition:none !important; } .reveal { opacity:1; transform:none; } .hero h1 .w span { transform:none; } .hero p.lead, .hero .cta { opacity:1; } }
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<nav id="nav">
  <a class="logo" href="#top">All<i>uré</i></a>
  <div class="links"><a href="#how">How it works</a><a href="#colour">Colour</a><a href="#features">Features</a><a href="#demo">Live demo</a></div>
  <a class="btn sm" href="/app">Open app</a>
</nav>

<header class="hero" id="top">
  <div>
    <div class="kicker" style="margin-bottom:28px"><b>01</b>Personal AI stylist</div>
    <h1 id="h1">Swipe your way to a wardrobe that's <em>yours.</em></h1>
    <p class="lead">Upload five outfits you love. Alluré learns your taste and the colours you love, then dresses you for the weather, shows you in it, and helps you find the best price.</p>
    <div class="cta"><a class="btn" href="/app">Start swiping</a><a class="btn ghost" href="#demo">Watch it work</a></div>
  </div>
  <div class="stack" id="stack"></div>
  <div class="scrollcue">Scroll</div>
</header>

<div class="marquee"><div class="track" id="marquee"></div></div>

<section id="how">
  <div class="kicker reveal"><b>02</b>How it works</div>
  <h2 class="big reveal">Five steps from scrolling to <i>wearing.</i></h2>
  <div class="steps">
    <div class="step reveal"><div class="n">i</div><div><h3>Show us your best fits</h3><p>Drop in 3–5 photos of outfits you feel great in. The AI reads your aesthetic, how you dress and what you reach for.</p></div><div class="viz"><div class="v-slots"><i style="--k:1"></i><i style="--k:2"></i><i style="--k:3"></i><i style="--k:4"></i><i style="--k:5"></i></div></div></div>
    <div class="step reveal"><div class="n">ii</div><div><h3>Get your colour palette</h3><p>You choose your undertone, and it builds a palette to explore, a starting point and never a rule. Every card tells you why it was picked.</p></div><div class="viz"><div class="v-pal"><i style="--k:1;background:#c4683f"></i><i style="--k:2;background:#b88a5a"></i><i style="--k:3;background:#d8a42c"></i><i style="--k:4;background:#2f5d46"></i><i style="--k:5;background:#f1e9d8"></i></div></div></div>
    <div class="step reveal"><div class="n">iii</div><div><h3>Swipe like you mean it</h3><p>Right to like, left to pass, down to save. Pass on something and it never comes back. Like it and you get more in that spirit.</p></div><div class="viz v-swipe"><div class="t l">LIKE</div><div class="t r">NOPE</div><div class="c" id="swipeCard"></div></div></div>
    <div class="step reveal"><div class="n">iv</div><div><h3>Best price, whole outfit</h3><p>Tap any piece for its real listed price, compare live offers when shopping search is on, and see the shoes, bag and accessories that finish the look.</p></div><div class="viz"><div class="v-deals"><div style="--k:1;width:96%" data-p="₹1,759"></div><div style="--k:2;width:84%" data-p="₹1,599"></div><div style="--k:3;width:78%" data-p="₹1,449"></div><div class="best" style="--k:4;width:70%" data-p="₹1,359 ✓"></div></div></div></div>
    <div class="step reveal"><div class="n">v</div><div><h3>See it on you first</h3><p>AI try-on puts the outfit on your own photo before you spend a rupee.</p></div><div class="viz"><div class="v-try"></div></div></div>
  </div>
</section>

<section class="lab" id="colour">
  <div class="kicker reveal"><b>03</b>Colour guide</div>
  <h2 class="big reveal">The right colour changes <i>everything.</i></h2>
  <div class="lab-grid">
    <div class="reveal">
      <p>Some colours simply feel like you. Pick your undertone and Alluré suggests a starting palette to explore. No colour is off-limits. Try it:</p>
      <div class="tones" id="tones"></div>
      <p class="say" id="say"></p>
    </div>
    <div class="reveal" style="--d:.15s"><div class="pal" id="pal"><i></i><i></i><i></i><i></i><i></i></div><div class="avoidline" id="avoid"></div></div>
  </div>
</section>

<section id="features">
  <div class="kicker reveal"><b>04</b>Everything a stylist does</div>
  <h2 class="big reveal">Your stylist, <i>in your pocket.</i></h2>
  <div class="feat">
    <div class="reveal"><small>Taste</small><h4>Learns you from five photos</h4><p>Aesthetic, silhouettes, how you layer, what you actually wear.</p></div>
    <div class="reveal" style="--d:.1s"><small>Discovery</small><h4>A deck that learns</h4><p>Every swipe re-ranks what comes next. Passed items never return.</p></div>
    <div class="reveal" style="--d:.2s"><small>Colour</small><h4>A palette that starts with you</h4><p>Choose your undertone, get colours to explore, and a reason on every card.</p></div>
    <div class="reveal"><small>Try-on</small><h4>Wear it before you buy it</h4><p>Your photo, the outfit, one tap. Fewer returns, fewer regrets.</p></div>
    <div class="reveal" style="--d:.1s"><small>Deals</small><h4>Real prices, honest gaps</h4><p>Listed prices and live offers, with missing details shown, never guessed.</p></div>
    <div class="reveal" style="--d:.2s"><span class="tag-soon">Next</span><small>Inspiration</small><h4>Dress like your icons</h4><p>Pick who you look up to; get fits inspired by them, tuned to you.</p></div>
    <div class="reveal"><span class="tag-soon">Next</span><small>Weather</small><h4>Dressed for today</h4><p>Rain, cold or sun: a full outfit that makes sense for the day.</p></div>
    <div class="reveal" style="--d:.1s"><span class="tag-soon">Next</span><small>Wallet</small><h4>Buys it when the sale drops</h4><p>Save what you want, load the wallet, and Alluré checks out the second the sale goes live.</p></div>
    <div class="reveal" style="--d:.2s"><small>Privacy</small><h4>Your data stays yours</h4><p>Photos are analysed and not stored. Delete everything with one tap.</p></div>
  </div>
</section>

<section id="demo">
  <div class="kicker reveal"><b>05</b>Live demo</div>
  <div class="demo" style="margin-top:30px">
    <div class="reveal">
      <h2 class="big" style="margin-top:0">It's real. <i>Try it.</i></h2>
      <ul><li>Enter a name, set your style, and start swiping.</li><li>Drag cards: right like, left pass, down save.</li><li>Tap a card for its price, the full look and try-on.</li><li>Open Today for a weather-aware outfit.</li></ul>
      <a class="btn" href="/app">Open full screen</a>
    </div>
    <div class="phone reveal" style="--d:.15s"><iframe src="/app" title="Alluré app" loading="lazy"></iframe></div>
  </div>
</section>

<section class="final">
  <h2 class="reveal">Dress like <i>you</i> mean it.</h2>
  <a class="btn reveal" style="--d:.2s" href="/app">Start swiping</a>
</section>
<footer><span>Alluré © 2026</span><span>Built at the Road to YC hackathon</span><span>Prices in demo are simulated</span></footer>

<script>
const $ = (s) => document.querySelector(s);
// hero headline: split into words that rise in
(() => { const h = $('#h1'); let i = 0; const wrap = (n) => { [...n.childNodes].forEach(c => { if (c.nodeType === 3) { const f = document.createDocumentFragment(); c.textContent.split(/(\s+)/).forEach(t => { if (!t.trim()) return f.append(' '); const w = document.createElement('span'); w.className = 'w'; w.innerHTML = `<span style="--i:${i++}">${t}</span>`; f.append(w); }); c.replaceWith(f); } else if (c.nodeType === 1) wrap(c); }); }; wrap(h); })();
// reveal on scroll
const io = new IntersectionObserver((es) => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: .18 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));
// nav + progress + parallax
const prog = $('#progress'), nav = $('#nav'), cards = [];
addEventListener('scroll', () => { const y = scrollY, max = document.documentElement.scrollHeight - innerHeight; prog.style.width = (y / max * 100) + '%'; nav.classList.toggle('solid', y > 40);
  cards.forEach(([el, s]) => el.style.translate = `0 ${-y * s}px`); }, { passive: true });
// products → hero stack, marquee, swipe card
fetch('/api/products').then(r => r.json()).catch(() => []).then(files => {
  const items = files.map(f => ({ name: f.split('__')[0], src: '/products/' + encodeURIComponent(f) }));
  const pick = ['Zip Hoodie A', 'Rust', 'Loose Jeans A'].map(n => items.find(i => i.name.includes(n))).filter(Boolean);
  const hero = (pick.length === 3 ? pick : items.filter((_, i) => i % 9 === 1).slice(0, 3));
  const stack = $('#stack'); stack.innerHTML = '';
  (hero.length ? hero : [{ name: 'Linen Shirt' }, { name: 'Wide Jeans' }, { name: 'Camel Coat' }]).forEach((p, i) => { const d = document.createElement('div'); d.className = 'pcard'; d.dataset.name = p.name; if (p.src) d.style.backgroundImage = `url("${p.src}")`; else d.style.background = ['#c4683f', '#5b7fae', '#b88a5a'][i]; stack.append(d); cards.push([d, [.04, .09, .02][i]]); });
  const m = $('#marquee'), strip = [];
  const words = ['Minimal', 'Editorial', 'Yours', 'Colour-matched', 'Swipe', 'Try on'];
  (items.length ? items.filter((_, i) => i % 3 === 0).slice(0, 14) : []).forEach((it, i) => { strip.push(`<span>${words[i % words.length]}</span><img src="${it.src}" alt="">`); });
  if (!strip.length) words.forEach(w => strip.push(`<span>${w}</span>`));
  m.innerHTML = strip.join('') + strip.join('');
  if (items[3]) $('#swipeCard').style.backgroundImage = `url("${items[3].src}")`;
});
// colour lab
const TONES = [
  ["Warm", ["#6B7044", "#B85C38", "#F0E6CE", "#B98B61", "#207C7A"], "Earthy, golden tones are a good place to start."],
  ["Cool", ["#243B61", "#993C68", "#62758B", "#C2DCEB", "#227A60"], "Inky blues, berry and emerald make a crisp palette."],
  ["Neutral", ["#243B61", "#F1EDE3", "#365C46", "#BC7D84", "#3B3E42"], "A balanced mix: ivory, forest, rose and charcoal."],
];
const tones = $("#tones"), pal = [...document.querySelectorAll("#pal i")];
function setTone(k) { tones.querySelectorAll("button").forEach((b, i) => b.classList.toggle("on", i === k)); const [n, cols, say] = TONES[k];
  pal.forEach((p, i) => { p.classList.add("swap"); setTimeout(() => { p.style.background = cols[i]; p.classList.remove("swap"); }, 220 + i * 70); });
  $("#say").textContent = n + " undertone. " + say; $("#avoid").textContent = "A starting palette, not a rule"; }
TONES.forEach((t, i) => { const b = document.createElement("button"); b.textContent = t[0]; b.onclick = () => setTone(i); tones.append(b); });
setTone(0);
</script>
</body>
</html>

~~~

## Step 3: `app.html`
~~~html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Alluré</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
  :root { --bg:#f4f2ee; --card:#ffffff; --ink:#111111; --mute:#77736b; --line:#d9d6cf; --like:#1e7a4c; --nope:#b3261e; --save:#1f4fd8; --accent:#111111;
          --serif:"Playfair Display", "Iowan Old Style", Georgia, "Times New Roman", serif; --sans:"Inter", -apple-system, system-ui, sans-serif; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--ink); font:15px/1.5 var(--sans); display:flex; justify-content:center; min-height:100vh; -webkit-font-smoothing:antialiased; }
  #app { width:100%; max-width:430px; min-height:100vh; position:relative; padding:20px 20px 40px; overflow:hidden; }
  h1 { font:600 34px/1.08 var(--serif); letter-spacing:-.02em; }
  h2 { font:600 24px/1.15 var(--serif); letter-spacing:-.01em; margin-bottom:6px; }
  h3 { font:600 11px var(--sans); margin:26px 0 10px; color:var(--ink); text-transform:uppercase; letter-spacing:.16em; padding-top:10px; border-top:1px solid var(--ink); }
  .kicker { font:700 12px var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--mute); margin:26px 0 10px; }
  .kicker b { font:600 44px/1 var(--serif); letter-spacing:-.03em; color:var(--ink); margin-right:10px; vertical-align:-6px; }
  .mute { color:var(--mute); } .row { display:flex; gap:8px; align-items:center; } .grow { flex:1; }
  button { font:600 13px var(--sans); letter-spacing:.1em; text-transform:uppercase; border:1px solid var(--ink); cursor:pointer; border-radius:0; padding:16px 18px; background:var(--ink); color:#fff; transition:.15s; }
  button:hover { background:#000; transform:translateY(-1px); }
  button.ghost { background:transparent; color:var(--ink); }
  button.ghost:hover { background:var(--ink); color:#fff; }
  button:disabled { opacity:.3; cursor:default; transform:none; }
  .screen { display:none; } .screen.on { display:block; animation:fade .35s; }
  @keyframes fade { from { opacity:0; transform:translateY(8px);} }
  .top { display:flex; align-items:center; justify-content:space-between; padding-bottom:14px; border-bottom:1px solid var(--ink); margin-bottom:6px; }
  .logo { font:600 26px var(--serif); letter-spacing:-.02em; } .logo span { font-style:italic; font-weight:400; }
  .pill { font:600 10px var(--sans); letter-spacing:.14em; text-transform:uppercase; padding:6px 0; color:var(--mute); }
  #likedPill, #savedPill { color:var(--ink); border:1px solid var(--line); padding:6px 10px; }
  /* upload */
  .slots { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:22px 0; }
  .slot { aspect-ratio:3/4; border:1px solid var(--line); border-radius:0; display:flex; align-items:center; justify-content:center; color:var(--mute); font:300 30px var(--serif); background:var(--card) center/cover no-repeat; cursor:pointer; position:relative; }
  .slot:hover { border-color:var(--ink); } .slot.filled { border-color:var(--ink); }
  .slot .x { position:absolute; top:6px; right:6px; background:#fff; border:1px solid var(--ink); width:20px; height:20px; font:600 10px var(--sans); display:flex; align-items:center; justify-content:center; color:var(--ink); }
  .stack { display:flex; flex-direction:column; gap:10px; }
  /* profile */
  .swatches { display:flex; gap:8px; flex-wrap:wrap; } .sw { width:44px; height:44px; border-radius:0; border:1px solid var(--line); }
  .sw.avoid { position:relative; } .sw.avoid::after { content:""; position:absolute; inset:0; background:linear-gradient(135deg,transparent 46%,#111 47%,#111 53%,transparent 54%); }
  .box { background:var(--card); border:1px solid var(--line); border-radius:0; padding:18px; }
  .tag { display:inline-block; border:1px solid var(--line); padding:3px 9px; margin:2px 2px 2px 0; font:600 10px var(--sans); letter-spacing:.1em; text-transform:uppercase; }
  .spinner { width:34px; height:34px; border:2px solid var(--line); border-top-color:var(--ink); border-radius:50%; animation:spin 1s linear infinite; margin:60px auto 18px; }
  @keyframes spin { to { transform:rotate(360deg);} }
  /* deck */
  .deck { position:relative; height:calc(100vh - 230px); min-height:430px; max-height:580px; margin-top:14px; }
  .card { position:absolute; inset:0; border-radius:0; overflow:hidden; background:var(--card); border:1px solid var(--ink); touch-action:none; user-select:none; transition:transform .3s; box-shadow:10px 10px 0 #0000000d; }
  .card.drag { transition:none; }
  .card .art { height:72%; display:flex; align-items:center; justify-content:center; background:#ebe8e2; }
  .card .art svg, .card .art img { height:100%; max-width:100%; object-fit:cover; pointer-events:none; }
  .card .art svg { height:84%; }
  .card .info { padding:12px 16px; border-top:1px solid var(--ink); }
  .card .name { font:600 19px/1.2 var(--serif); } .match { font:600 13px var(--sans); color:var(--like); letter-spacing:.04em; white-space:nowrap; }
  .stamp { position:absolute; top:22px; padding:4px 12px; border:2px solid; font:700 20px var(--sans); letter-spacing:.2em; opacity:0; transform:rotate(-8deg); background:#fffc; z-index:2; }
  .stamp.like { left:18px; color:var(--like); } .stamp.nope { right:18px; color:var(--nope); transform:rotate(8deg); } .stamp.save { left:50%; top:auto; bottom:36%; transform:translateX(-50%); color:var(--save); }
  .actions { display:flex; justify-content:center; gap:14px; margin-top:20px; }
  .actions button { width:76px; height:52px; padding:0; font-size:18px; letter-spacing:0; background:transparent; border:1px solid var(--ink); color:var(--ink); }
  .actions button:hover { background:var(--ink); color:#fff; }
  .actions .n, .actions .s, .actions .l { color:var(--ink); }
  .hint { text-align:center; font:600 10px var(--sans); letter-spacing:.14em; text-transform:uppercase; margin-top:14px; }
  /* detail */
  .hero { background:#ebe8e2; border-radius:0; height:340px; display:flex; align-items:center; justify-content:center; margin-top:8px; overflow:hidden; border:1px solid var(--line); }
  .hero img { height:100%; max-width:100%; object-fit:cover; } .hero svg { height:85%; max-width:85%; }
  table { width:100%; border-collapse:collapse; } td { padding:12px 0; border-bottom:1px solid var(--line); } td:last-child { text-align:right; font:600 17px var(--serif); }
  .badge { font:700 9px var(--sans); letter-spacing:.1em; padding:2px 6px; margin-left:6px; border:1px solid; vertical-align:2px; }
  .b-price { color:var(--like);} .b-qual { color:var(--save);} .b-val { color:#a8561f; }
  .pairs { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
  .pair { background:var(--card); border:1px solid var(--line); padding:8px; text-align:left; font:500 11px/1.3 var(--sans); cursor:pointer; }
  .pair:hover { border-color:var(--ink); }
  .pair svg, .pair img { height:92px; width:100%; object-fit:cover; margin-bottom:6px; background:#ebe8e2; }
  .back { background:none; color:var(--mute); border:0; padding:10px 0; font:600 11px var(--sans); letter-spacing:.14em; }
  .back:hover { background:none; color:var(--ink); transform:none; }
  /* try-on */
  .tryon { position:relative; overflow:hidden; background:var(--card); aspect-ratio:3/4; color:#fff; border:1px solid var(--ink); }
  .tryon > img { width:100%; height:100%; object-fit:cover; }
  .tryon .overlay { position:absolute; left:50%; top:52%; transform:translate(-50%,-50%); width:62%; opacity:.92; mix-blend-mode:multiply; cursor:move; touch-action:none; }
  .list { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }
  input[type=range] { width:100%; accent-color:#111; }
  .toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%); background:var(--ink); color:#fff; padding:12px 20px; font:600 11px var(--sans); letter-spacing:.12em; text-transform:uppercase; opacity:0; transition:.3s; pointer-events:none; }
  .toast.on { opacity:1; z-index:300; }
  /* ---------- app shell: tab bar, sheets, splash ---------- */
  .tabbar { display:none; position:fixed; bottom:0; left:50%; transform:translateX(-50%); width:100%; max-width:430px; background:#f4f2eeec; backdrop-filter:blur(14px); border-top:1px solid var(--ink); z-index:40; padding-bottom:env(safe-area-inset-bottom); }
  body.tabs .tabbar { display:grid; grid-template-columns:repeat(5,1fr); }
  body.tabs #app { padding-bottom:104px; }
  .tab { background:none; color:var(--mute); border:0; padding:11px 0 13px; display:flex; flex-direction:column; align-items:center; gap:5px; font:700 8.5px var(--sans); letter-spacing:.14em; position:relative; }
  .tab:hover { background:none; transform:none; color:var(--ink); }
  .tab svg { width:22px; height:22px; stroke:currentColor; fill:none; stroke-width:1.4; stroke-linecap:square; }
  .tab.on { color:var(--ink); } .tab.on::before { content:""; position:absolute; top:-1px; left:26%; right:26%; height:3px; background:var(--ink); }
  .screen.sheet { display:block; position:fixed; left:50%; bottom:0; width:100%; max-width:430px; height:93vh; background:var(--bg); z-index:60; overflow-y:auto; padding:10px 20px 44px; border-top:1px solid var(--ink);
    transform:translateX(-50%) translateY(102%); visibility:hidden; transition:transform .5s cubic-bezier(.2,.85,.2,1), visibility 0s .5s; animation:none; }
  .screen.sheet.on { transform:translateX(-50%) translateY(0); visibility:visible; transition:transform .5s cubic-bezier(.2,.85,.2,1), visibility 0s; }
  .grab { width:44px; height:4px; background:var(--ink); opacity:.25; margin:2px auto 8px; cursor:pointer; }
  #scrim { position:fixed; inset:0; background:#11111155; opacity:0; pointer-events:none; transition:.4s; z-index:55; }
  body.sheetopen #scrim { opacity:1; pointer-events:auto; } body.sheetopen { overflow:hidden; }
  #splash { position:fixed; inset:0; background:var(--bg); z-index:400; display:flex; flex-direction:column; align-items:center; justify-content:center; transition:opacity .7s .2s; }
  #splash.out { opacity:0; pointer-events:none; }
  #splash .l { font:600 64px var(--serif); letter-spacing:-.03em; animation:fadeup .9s both; } #splash .l i { font-weight:400; }
  #splash .s { font:700 10px var(--sans); letter-spacing:.24em; text-transform:uppercase; color:var(--mute); margin-top:10px; animation:fadeup .9s .35s both; }
  #splash .bar { width:120px; height:1px; background:var(--line); margin-top:26px; position:relative; overflow:hidden; } #splash .bar::after { content:""; position:absolute; inset:0; background:var(--ink); transform:translateX(-100%); animation:load 1.2s .2s forwards; }
  @keyframes fadeup { from { opacity:0; transform:translateY(14px);} to { opacity:1; transform:none; } } @keyframes load { to { transform:none; } }
  body.tabs .deck { height:calc(100vh - 318px); min-height:380px; }
  /* chips, segmented control, wallet card, today */
  .chips { display:flex; flex-wrap:wrap; gap:8px; } .chip { padding:9px 13px; font:700 10px var(--sans); letter-spacing:.12em; background:transparent; color:var(--ink); }
  .chip.on { background:var(--ink); color:#fff; }
  .seg { display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--ink); margin:16px 0 18px; } .seg button { border:0; background:transparent; color:var(--ink); padding:12px; } .seg button.on { background:var(--ink); color:#fff; }
  .wcard { background:var(--ink); color:#f4f2ee; padding:26px 22px 22px; margin-top:18px; position:relative; overflow:hidden; }
  .wcard small { font:700 10px var(--sans); letter-spacing:.2em; text-transform:uppercase; color:#a39e92; } .wcard .amt { font:600 56px/1.05 var(--serif); letter-spacing:-.03em; margin:14px 0 18px; }
  .wcard::after { content:"A"; position:absolute; right:-10px; bottom:-60px; font:italic 400 200px var(--serif); color:#ffffff10; }
  .wcard .chips button { border-color:#f4f2ee66; color:#f4f2ee; } .wcard .chips button:hover { background:#f4f2ee; color:var(--ink); }
  .temp { font:600 clamp(88px,26vw,120px)/.9 var(--serif); letter-spacing:-.05em; } .temp sup { font-size:.4em; vertical-align:top; position:relative; top:.2em; font-weight:400; }
  .look { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:6px; } .look .pair svg, .look .pair img { height:150px; }
  .field { width:100%; border:1px solid var(--line); background:var(--card); padding:14px; font:500 14px var(--sans); margin-top:10px; border-radius:0; } .field:focus { outline:0; border-color:var(--ink); }
  .order { border:1px solid var(--ink); padding:14px 16px; margin-top:10px; background:var(--card); } .order b { font:600 17px var(--serif); }
  .empty { border:1px dashed var(--line); padding:44px 20px; text-align:center; } .empty h2 { margin-bottom:8px; }
</style>
</head>
<body>
<div id="app">

  <!-- 1. Upload -->
  <section class="screen on" id="s-upload">
    <div class="top"><div class="logo">All<span>uré</span></div><span class="pill" id="aiBadge">…</span></div>
    <div class="kicker"><b>01</b>Your style</div>
    <h1>Show us your five favourite fits.</h1>
    <p class="mute" style="margin-top:6px" id="upLead">Our AI reads your aesthetic and the colours that flatter you, then finds clothes you'll actually wear.</p>
    <p class="mute" id="upNote" style="font-size:12px;margin-top:8px"></p>
    <div class="slots" id="slots"></div>
    <input type="file" id="file" accept="image/*" multiple hidden>
    <div class="stack">
      <button id="analyzeBtn" disabled>Analyse my style</button>
      <button class="ghost" id="demoBtn">Skip — use a demo profile</button>
    </div>
  </section>

  <!-- 2. Analysing / profile -->
  <section class="screen" id="s-profile">
    <div id="profileBody"></div>
  </section>

  <!-- 3. Swipe deck -->
  <section class="screen" id="s-deck">
    <div class="top">
      <div class="logo">All<span>uré</span></div>
      <div class="row"><span class="pill" id="likedPill">♥ 0</span><span class="pill" id="savedPill">⬇ 0</span></div>
    </div>
    <div class="deck" id="deck"></div>
    <div class="actions">
      <button class="n" onclick="swipe('nope')" title="Nope (←)">✕</button>
      <button class="s" onclick="swipe('save')" title="Save (↓)">⬇</button>
      <button class="l" onclick="swipe('like')" title="Like (→)">♥</button>
    </div>
    <p class="hint mute">Swipe → like · ← pass · ↓ save · tap for prices &amp; try-on</p>
  </section>

  <!-- Welcome: display name -> POST /sessions -->
  <section class="screen" id="s-welcome"><div id="welcomeBody"></div></section>

  <!-- Stylist chat: POST /agent/shop -->
  <section class="screen" id="s-chat"><div id="chatBody"></div></section>

  <!-- Today: weather outfit -->
  <section class="screen" id="s-today"><div id="todayBody"></div></section>

  <!-- Saved / liked -->
  <section class="screen" id="s-list"><div id="listBody"></div></section>

  <!-- Wallet -->
  <section class="screen" id="s-wallet"><div id="walletBody"></div></section>

  <!-- Sheets: item detail + try-on slide up over any tab -->
  <section class="screen sheet" id="s-detail"><div class="grab" onclick="closeSheet()"></div><div id="detailBody"></div></section>
  <section class="screen sheet" id="s-sub"><div class="grab" onclick="closeSheet()"></div><div id="subBody"></div></section>
  <section class="screen sheet" id="s-tryon"><div class="grab" onclick="closeSheet()"></div><div id="tryonBody"></div></section>
</div>

<div id="scrim" onclick="closeSheet()"></div>
<nav class="tabbar">
  <button class="tab on" data-t="deck" onclick="go('deck')"><svg viewBox="0 0 24 24"><rect x="5" y="5" width="14" height="16"/><path d="M8 2.5h8"/></svg>Discover</button>
  <button class="tab" data-t="today" onclick="go('today')"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg>Today</button>
  <button class="tab" data-t="saved" onclick="go('saved')"><svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4-6 4z"/></svg>Saved</button>
  <button class="tab" data-t="chat" onclick="go('chat')"><svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z"/></svg>Stylist</button>
  <button class="tab" data-t="you" onclick="go('you')"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-5 4-7 8-7s7 2 8 7"/></svg>You</button>
</nav>
<div id="splash"><div class="l">All<i>uré</i></div><div class="s">Your personal stylist</div><div class="bar"></div></div>
<div class="toast" id="toast"></div>

<script>
// ---------- Garment art (SVG, coloured per product; swap for real photos via item.img) ----------
const SHAPES = {
  tee:      'M60 30 L85 20 Q100 34 115 20 L140 30 L175 60 L155 85 L140 72 L140 210 L60 210 L60 72 L45 85 L25 60 Z',
  shirt:    'M62 28 L88 18 L100 40 L112 18 L138 28 L172 70 L158 210 L140 110 L140 215 L60 215 L60 110 L42 210 L28 70 Z M100 40 L100 215',
  hoodie:   'M58 40 Q70 10 100 8 Q130 10 142 40 L178 70 L165 210 L145 205 L145 215 L55 215 L55 205 L35 210 L22 70 Z M78 150 L122 150 L118 185 L82 185 Z',
  jacket:   'M60 30 L88 18 L100 60 L112 18 L140 30 L176 72 L166 215 L142 215 L142 220 L58 220 L58 215 L34 215 L24 72 Z M100 60 L100 220',
  dress:    'M78 20 L90 16 Q100 30 110 16 L122 20 L130 70 L120 95 L170 225 L30 225 L80 95 L70 70 Z',
  kurta:    'M64 26 L88 16 Q100 34 112 16 L136 26 L172 66 L158 120 L142 100 L148 230 L52 230 L58 100 L42 120 L28 66 Z M100 34 L100 80',
  trousers: 'M60 15 L140 15 L150 230 L112 230 L100 80 L88 230 L50 230 Z',
  skirt:    'M70 40 L130 40 L170 200 L30 200 Z',
  shoes:    'M20 130 L20 100 Q40 96 60 80 L80 80 Q90 100 120 106 L172 118 Q186 124 182 140 L20 140 Z',
  bag:      'M45 90 L155 90 L165 205 L35 205 Z M72 90 Q72 45 100 45 Q128 45 128 90',
  watch:    'M85 20 L115 20 L115 70 L85 70 Z M85 150 L115 150 L115 200 L85 200 Z M100 72 A40 40 0 1 1 99.9 72 Z',
  cap:      'M40 130 Q40 60 100 60 Q160 60 160 130 Z M140 130 L195 140 L140 145 Z',
  sunglasses:'M20 90 L180 90 L176 100 L150 100 Q148 135 120 132 Q102 130 104 100 L96 100 Q98 130 80 132 Q52 135 50 100 L24 100 Z',
};
function garmentSVG(item) {
  if (item.img) return `<img src="${item.img}" alt="${item.name}">`;
  const dark = lum(item.hex) < .45;
  return `<svg viewBox="0 0 200 240" xmlns="http://www.w3.org/2000/svg"><path d="${SHAPES[item.type]}" fill="${item.hex}" stroke="${dark ? '#ffffff55' : '#00000040'}" stroke-width="3" stroke-linejoin="round" fill-rule="evenodd"/></svg>`;
}

// ---------- Catalog (team: replace with real products/images; keep the same fields) ----------
const RAW = [
  // name, type, hex, tags, base price (INR), brand
  ['Oversized Boxy Tee','tee','#f2efe8',['minimal','casual','streetwear'],799,'Bonkers Corner'],
  ['Washed Black Tee','tee','#26262b',['streetwear','edgy','minimal'],899,'Snitch'],
  ['Terracotta Linen Shirt','shirt','#c4683f',['boho','casual','classic'],1799,'Andamen'],
  ['Sage Linen Shirt','shirt','#9caf88',['minimal','classic','casual'],1699,'Uniqlo'],
  ['Crisp White Oxford','shirt','#fafafa',['classic','formal','preppy'],1999,'Arrow'],
  ['Powder Blue Oxford','shirt','#a9c4e2',['preppy','classic','formal'],1899,'Van Heusen'],
  ['Cobalt Overshirt','shirt','#2f55c6',['streetwear','casual'],2299,'H&M'],
  ['Charcoal Hoodie','hoodie','#3a3b40',['streetwear','sporty','casual'],2499,'Nike'],
  ['Lilac Hoodie','hoodie','#b9a6d6',['streetwear','romantic','casual'],1999,'Souled Store'],
  ['Forest Green Hoodie','hoodie','#2f5d46',['streetwear','sporty','vintage'],2199,'Adidas'],
  ['Camel Overcoat','jacket','#b88a5a',['classic','formal','minimal'],5999,'Zara'],
  ['Indigo Denim Jacket','jacket','#3b5b8c',['vintage','casual','streetwear'],3499,"Levi's"],
  ['Black Biker Jacket','jacket','#18181b',['edgy','streetwear'],6499,'AllSaints'],
  ['Olive Bomber','jacket','#6b6b3a',['streetwear','sporty','vintage'],3299,'Roadster'],
  ['Navy Blazer','jacket','#22304f',['formal','classic','preppy'],5499,'Mango'],
  ['Rust Slip Dress','dress','#a8492d',['romantic','boho','vintage'],2799,'Zara'],
  ['Emerald Midi Dress','dress','#1f7a5a',['romantic','classic','formal'],3299,'& Other Stories'],
  ['Little Black Dress','dress','#141416',['classic','formal','edgy','minimal'],2999,'Mango'],
  ['Butter Yellow Sundress','dress','#f3dc8b',['romantic','boho','casual'],2199,'H&M'],
  ['Blush Wrap Dress','dress','#e8b4b0',['romantic','preppy'],2599,'Forever New'],
  ['Mustard Chikankari Kurta','kurta','#d8a42c',['ethnic','boho','classic'],1899,'Fabindia'],
  ['Ivory Cotton Kurta','kurta','#f1e9d8',['ethnic','minimal','classic'],1599,'Manyavar'],
  ['Maroon Silk Kurta','kurta','#6e1f2c',['ethnic','formal','classic'],3499,'Manyavar'],
  ['Teal Block-print Kurta','kurta','#2a7f84',['ethnic','boho'],1499,'Jaypore'],
  ['Beige Pleated Trousers','trousers','#d6c4a6',['classic','minimal','formal'],2299,'Uniqlo'],
  ['Black Cargo Pants','trousers','#222225',['streetwear','edgy','sporty'],2499,'Snitch'],
  ['Mid-wash Wide Jeans','trousers','#5b7fae',['casual','vintage','streetwear'],2799,"Levi's"],
  ['Brown Corduroy Trousers','trousers','#6d4c35',['vintage','boho','classic'],2399,'Bershka'],
  ['Cream Satin Skirt','skirt','#efe3cf',['romantic','minimal','classic'],1799,'Zara'],
  ['Plaid Mini Skirt','skirt','#7b2f3a',['preppy','edgy','vintage'],1499,'Bershka'],
  // accessories & footwear (used for "complete the look")
  ['White Leather Sneakers','shoes','#f5f5f2',['minimal','casual','streetwear','sporty'],3999,'Adidas'],
  ['Black Chelsea Boots','shoes','#1b1b1d',['edgy','classic','formal'],5499,'Clarks'],
  ['Tan Loafers','shoes','#a8743f',['classic','preppy','formal'],3799,'Hush Puppies'],
  ['Kolhapuri Sandals','shoes','#8a5a32',['ethnic','boho'],1299,'Fabindia'],
  ['Retro Runners','shoes','#c9473d',['sporty','streetwear','vintage'],4999,'New Balance'],
  ['Woven Tote','bag','#cfb48a',['boho','casual','minimal'],1999,'Accessorize'],
  ['Black Crossbody','bag','#1d1d20',['minimal','edgy','classic'],2499,'Charles & Keith'],
  ['Gold Minimal Watch','watch','#c9a54e',['classic','minimal','formal'],4999,'Fossil'],
  ['Silver Steel Watch','watch','#b7bcc4',['classic','sporty','minimal'],3999,'Titan'],
  ['Washed Baseball Cap','cap','#3b4a6b',['streetwear','sporty','casual'],799,'New Era'],
  ['Tortoise Sunglasses','sunglasses','#5a3a22',['vintage','classic','boho'],1499,'Ray-Ban'],
  ['Black Square Sunglasses','sunglasses','#141414',['edgy','minimal','streetwear'],1299,'Vincent Chase'],
];
const ACCESSORY = ['shoes','bag','watch','cap','sunglasses'];
const TOPS = ['tee','shirt','hoodie','jacket','kurta'], BOTTOMS = ['trousers','skirt'];
let CATALOG = RAW.map(([name,type,hex,tags,price,brand], id) => ({ id, name, type, hex, tags, price, brand }));

// Real products: drop photos into /products named  Name__type__price__Brand.jpg  — colour is read from the photo.
const TYPE_TAGS = { tee:['casual','minimal','streetwear'], shirt:['classic','casual','preppy'], hoodie:['streetwear','sporty','casual'],
  jacket:['streetwear','classic','edgy'], dress:['romantic','classic'], kurta:['ethnic','classic','boho'], trousers:['classic','casual','minimal'],
  skirt:['romantic','preppy'], shoes:['casual','classic','streetwear'], bag:['classic','minimal'], watch:['classic','minimal'],
  cap:['streetwear','sporty'], sunglasses:['classic','edgy'] };
async function photoColour(src) { // dominant non-background colour of a product photo
  const img = await loadImg(src), c = document.createElement('canvas'); c.width = 40; c.height = 40;
  const x = c.getContext('2d'); x.drawImage(img, 0, 0, 40, 40);
  const d = x.getImageData(8, 12, 24, 20).data, buckets = {}; // central torso band: model photos have skin/background at the edges
  for (let i = 0; i < d.length; i += 4) {
    const h = rgbToHex(d[i], d[i+1], d[i+2]), [, s, l] = hsl(h);
    const cb = 128 - .169*d[i] - .331*d[i+1] + .5*d[i+2], cr = 128 + .5*d[i] - .419*d[i+1] - .081*d[i+2];
    if (cr >= 140 && cr <= 175 && cb >= 90 && cb <= 128 && l > .3 && l < .8 && s < .6) continue; // skip skin pixels (hands, neck)
    if (d[i+3] < 128 || (s < .12 && l > .85)) continue; // skip transparent + white/light-grey studio background
    const k = [d[i], d[i+1], d[i+2]].map(v => v >> 5).join(','), B = (buckets[k] ||= { n: 0, r: 0, g: 0, b: 0 });
    B.n++; B.r += d[i]; B.g += d[i+1]; B.b += d[i+2];
  }
  const top = Object.values(buckets).sort((a, b) => b.n - a.n)[0];
  return top ? rgbToHex(top.r / top.n, top.g / top.n, top.b / top.n) : '#cccccc';
}
async function loadProducts() {
  const files = await fetch('/api/products').then(r => r.json()).catch(() => []);
  const real = [];
  for (const f of files) {
    const [name, type, price, brand] = f.replace(/\.[^.]+$/, '').split('__').map(s => s.trim());
    const t = (type || '').toLowerCase();
    if (!SHAPES[t]) { console.warn('Skipping product (type must be one of ' + Object.keys(SHAPES).join(', ') + '):', f); continue; }
    const img = '/products/' + encodeURIComponent(f);
    real.push({ name, type: t, img, hex: await photoColour(img).catch(() => '#cccccc'), tags: TYPE_TAGS[t], price: +price || 1999, brand: brand || 'Store' });
  }
  if (!real.length) return;
  const covered = new Set(real.map(r => r.type)); // keep demo items only for categories with no real photos yet
  CATALOG = [...real, ...CATALOG.filter(c => !covered.has(c.type))].map((c, id) => ({ ...c, id }));
  console.log(`Loaded ${real.length} real products`);
}

// Seeded pseudo-random so mock offers are stable between renders.
const rnd = (seed) => { let x = Math.sin(seed * 9301 + 49297) * 233280; return x - Math.floor(x); };
function offers(item) {
  // ponytail: mocked marketplace offers; replace with a real price API / affiliate feed (see TEAM_PLAN.md).
  const stores = ['Myntra','Ajio','Amazon Fashion','Flipkart','Nykaa Fashion', item.brand + ' store'];
  const list = stores.map((store, i) => ({
    store,
    price: Math.round(item.price * (0.82 + rnd(item.id * 7 + i) * 0.36) / 10) * 10 - 1,
    quality: +(3.7 + rnd(item.id * 13 + i) * 1.2).toFixed(1),
    delivery: 1 + Math.floor(rnd(item.id * 3 + i) * 5),
  }));
  const minP = Math.min(...list.map(o => o.price)), maxQ = Math.max(...list.map(o => o.quality));
  list.forEach(o => o.value = (o.quality / maxQ) / (o.price / minP));
  const best = { price: list.find(o => o.price === minP), quality: list.find(o => o.quality === maxQ), value: list.reduce((a, b) => b.value > a.value ? b : a) };
  return { list: list.sort((a, b) => a.price - b.price), best };
}

// ---------- Colour maths ----------
const hexToRgb = (h) => [1,3,5].map(i => parseInt(h.slice(i, i+2), 16));
const rgbToHex = (r,g,b) => '#' + [r,g,b].map(v => Math.round(v).toString(16).padStart(2,'0')).join('');
const lum = (h) => { const [r,g,b] = hexToRgb(h); return (0.299*r + 0.587*g + 0.114*b) / 255; };
function hsl(h) {
  let [r,g,b] = hexToRgb(h).map(v => v/255); const mx = Math.max(r,g,b), mn = Math.min(r,g,b), l = (mx+mn)/2;
  if (mx === mn) return [0,0,l];
  const d = mx - mn, s = l > .5 ? d/(2-mx-mn) : d/(mx+mn);
  const hh = mx === r ? (g-b)/d + (g<b?6:0) : mx === g ? (b-r)/d + 2 : (r-g)/d + 4;
  return [hh*60, s, l];
}
function cdist(a, b) { // "redmean" perceptual approximation, 0..~765
  const [r1,g1,b1] = hexToRgb(a), [r2,g2,b2] = hexToRgb(b), rm = (r1+r2)/2;
  return Math.sqrt((2+rm/256)*(r1-r2)**2 + 4*(g1-g2)**2 + (2+(255-rm)/256)*(b1-b2)**2);
}
const isNeutral = (h) => { const [,s,l] = hsl(h); return s < .18 || l < .14 || l > .92; };
function harmony(a, b) { // 0..1, how well two colours pair
  if (isNeutral(a) || isNeutral(b)) return .9;
  const d = Math.abs(hsl(a)[0] - hsl(b)[0]) % 360, dh = Math.min(d, 360 - d);
  if (dh < 30) return .8;            // analogous
  if (dh > 150) return .85;          // complementary
  if (dh > 100 && dh < 140) return .6; // triadic-ish
  return .35;
}

// ---------- On-device style analysis (fallback when no Claude key) ----------
function loadImg(src) { return new Promise(r => { const i = new Image(); i.onload = () => r(i); i.src = src; }); }
async function localAnalyze(dataUrls) {
  const buckets = {};
  for (const u of dataUrls) {
    const img = await loadImg(u), c = document.createElement('canvas'); c.width = 48; c.height = 64;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0, 48, 64);
    const d = x.getImageData(10, 14, 28, 46).data; // centre of frame ≈ where the outfit is
    for (let i = 0; i < d.length; i += 4) {
      const k = [d[i], d[i+1], d[i+2]].map(v => v >> 5).join(','); // 8 levels per channel
      (buckets[k] ||= { n: 0, r: 0, g: 0, b: 0 }); const B = buckets[k]; B.n++; B.r += d[i]; B.g += d[i+1]; B.b += d[i+2];
    }
  }
  const ranked = Object.values(buckets).sort((a, b) => b.n - a.n).map(B => rgbToHex(B.r/B.n, B.g/B.n, B.b/B.n));
  const palette = [];
  for (const h of ranked) { if (palette.every(p => cdist(p, h) > 90)) palette.push(h); if (palette.length === 5) break; }
  const hs = palette.map(hsl), chroma = palette.filter(h => !isNeutral(h));
  const warm = chroma.filter(h => { const H = hsl(h)[0]; return H < 70 || H > 330; }).length >= chroma.length / 2;
  const light = hs.reduce((a, h) => a + h[2], 0) / hs.length > .5;
  const avgSat = hs.reduce((a, h) => a + h[1], 0) / hs.length;
  const tags = new Set();
  if (chroma.length <= 1) { tags.add('minimal'); tags.add('classic'); }
  if (avgSat > .45) { tags.add('streetwear'); tags.add('sporty'); }
  if (warm && avgSat < .5 && chroma.length) { tags.add('boho'); tags.add('vintage'); }
  if (light && chroma.length) { tags.add('romantic'); tags.add('preppy'); }
  if (!light && !chroma.length) tags.add('edgy');
  tags.add('casual');
  const season = (warm ? 'warm ' : 'cool ') + (light ? (warm ? 'spring' : 'summer') : (warm ? 'autumn' : 'winter'));
  const NAMES = { minimal:'Quiet Minimalist', streetwear:'Street Casual', boho:'Earthy Boho', romantic:'Soft Romantic', edgy:'Dark Edge', classic:'Modern Classic' };
  const aesthetic = NAMES[[...tags][0]] || 'Easy Casual';
  const avoid = warm ? ['#9fd3ff', '#e0b0ff'] : ['#ff9f1c', '#d4a017'];
  return { aesthetic, tags: [...tags].slice(0, 5), season, palette, avoid,
    summary: `You lean ${aesthetic.toLowerCase()} — your favourite fits reach for ${warm ? 'warm, earthy' : 'cool, crisp'} tones.` };
}
const DEMO = { aesthetic:'Earthy Minimalist', tags:['minimal','classic','boho','casual'],
  summary:'You gravitate to clean silhouettes and relaxed, natural fabrics.' };

// ---------- Skin tone → personal colour palette ----------
// Works for every skin tone: depth (fair→deep) sets how much contrast you can carry,
// undertone (warm/cool/neutral) sets which hues flatter. User can always override.
const DEPTHS = ['fair','light','medium','tan','deep'];
const SKIN_SWATCHES = { fair:'#f3d9c8', light:'#e6bc98', medium:'#c68e65', tan:'#a06a42', deep:'#5c3a24' };
const UNDERTONE_PALETTE = {
  warm:    { palette:['#c4683f','#b88a5a','#d8a42c','#6b6b3a','#2f5d46'], avoid:['#b9a6d6','#a9c4e2','#e8b4b0'] },
  cool:    { palette:['#22304f','#1f7a5a','#6e1f2c','#2f55c6','#b9a6d6'], avoid:['#d8a42c','#c4683f','#6b6b3a'] },
  neutral: { palette:['#2a7f84','#9caf88','#e8b4b0','#22304f','#7b2f3a'], avoid:['#ff2d95','#b6ff00'] }, // neutral undertones suit most colours; only neons fight them
};
const DEPTH_EXTRA = { // lighter skin: softer tones; deeper skin: high-contrast brights and crisp white
  fair:['#a9c4e2','#e8b4b0','#9caf88'], light:['#9caf88','#a9c4e2'], medium:['#f1e9d8','#2a7f84'],
  tan:['#fafafa','#2f55c6','#1f7a5a'], deep:['#fafafa','#d8a42c','#2f55c6','#c4683f'] };
const UNDERTONE_NOTE = { warm:'golden/olive', cool:'pink/rosy', neutral:'balanced' };

async function detectSkin(dataUrls) {
  // ponytail: classic YCbCr skin-pixel rule; wood/orange backgrounds can fool it — user override covers that.
  let n = 0, R = 0, G = 0, B = 0;
  for (const u of dataUrls) {
    const img = await loadImg(u), c = document.createElement('canvas'); c.width = 48; c.height = 64;
    const x = c.getContext('2d'); x.drawImage(img, 0, 0, 48, 64);
    const d = x.getImageData(0, 0, 48, 64).data;
    for (let i = 0; i < d.length; i += 4) {
      const r = d[i], g = d[i+1], b = d[i+2], y = .299*r + .587*g + .114*b;
      const cb = 128 - .169*r - .331*g + .5*b, cr = 128 + .5*r - .419*g - .081*b;
      if (y > 35 && cr >= 135 && cr <= 180 && cb >= 85 && cb <= 135 && r > g && r > b) { n++; R += r; G += g; B += b; }
    }
  }
  return n < 30 ? null : rgbToHex(R/n, G/n, B/n);
}
function classifySkin(hex, undertone) {
  const L = lum(hex), H = hsl(hex)[0];
  const depth = L > .82 ? 'fair' : L > .69 ? 'light' : L > .53 ? 'medium' : L > .36 ? 'tan' : 'deep'; // midpoints between SKIN_SWATCHES
  return { hex, depth, undertone: undertone || (H >= 24 ? 'warm' : H <= 17 ? 'cool' : 'neutral') };
}
function applySkin(P, skin) {
  const base = UNDERTONE_PALETTE[skin.undertone], lightSkin = ['fair','light'].includes(skin.depth);
  P.skin = skin;
  P.palette = [...new Set([...base.palette.slice(0, 3), ...DEPTH_EXTRA[skin.depth].filter(c => !base.avoid.includes(c)), ...base.palette.slice(3)])].slice(0, 6);
  P.avoid = base.avoid;
  P.season = skin.undertone === 'neutral' ? 'soft neutral' : `${skin.undertone} ${skin.undertone === 'warm' ? (lightSkin ? 'spring' : 'autumn') : (lightSkin ? 'summer' : 'winter')}`;
  P.skinNote = `${skin.depth[0].toUpperCase() + skin.depth.slice(1)} skin with a ${skin.undertone} (${UNDERTONE_NOTE[skin.undertone]}) undertone — ` +
    (['tan','deep'].includes(skin.depth) ? 'rich, saturated colours and crisp white make you pop.' : lightSkin ? 'softer, lighter shades flatter you; very bright colours can overpower.' : 'mid-tone and jewel colours balance you best.');
  return P;
}
const washesOut = (hex) => { const s = S.profile?.skin; return s && Math.abs(lum(hex) - lum(s.hex)) < .1 && cdist(hex, s.hex) < 160; };

// ---------- State ----------
const S = { photos: [], profile: null, deck: [], liked: [], saved: [], tagW: {}, ai: { claude:false, tryon:false }, icons: [], wallet: 0, orders: [], listTab: 'saved', tab: 's-deck' };
const ICONS = [['Billie Eilish',['streetwear','edgy','minimal']],['Zendaya',['classic','romantic','formal']],['Harry Styles',['vintage','romantic','boho']],['Rihanna',['edgy','streetwear','romantic']],
  ['Timothée Chalamet',['classic','minimal','formal']],['Hailey Bieber',['minimal','classic','casual']],['Alia Bhatt',['ethnic','romantic','casual']],['Ranveer Singh',['streetwear','edgy','boho']],['Virat Kohli',['sporty','classic','casual']]];
const $ = (id) => document.getElementById(id);
const SHEETS = ['s-detail', 's-tryon', 's-sub'], TAB_OF = { 's-chat':'chat', 's-deck':'deck', 's-today':'today', 's-list':'saved', 's-wallet':'wallet', 's-profile':'you' };
function show(id) { // tabs swap the main screen; sheets slide up over whatever tab is open
  const sheet = SHEETS.includes(id);
  document.querySelectorAll('.screen').forEach(s => { const isSheet = SHEETS.includes(s.id); if (sheet === isSheet) s.classList.toggle('on', s.id === id); else if (!sheet) s.classList.remove('on'); });
  if (sheet) { $(id).scrollTop = 0; } else { S.tab = id; window.scrollTo(0, 0); }
  document.body.classList.toggle('sheetopen', sheet);
  document.body.classList.toggle('tabs', (typeof B !== 'undefined' && B.live ? S.ready : !!S.profile) && !['s-upload', 's-welcome'].includes(S.tab));
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('on', t.dataset.t === TAB_OF[S.tab]));
}
function closeSheet() { clearTimeout(S.tryT); SHEETS.forEach(id => $(id).classList.remove('on')); document.body.classList.remove('sheetopen'); }
function go(t) { closeSheet(); ({ deck: () => S.deck.length ? (show('s-deck'), renderDeck()) : startDeck(), today: renderToday, saved: renderList, wallet: renderWallet, you: renderProfile })[t](); }
const toast = (t) => { const e = $('toast'); e.textContent = t; e.classList.add('on'); clearTimeout(toast.t); toast.t = setTimeout(() => e.classList.remove('on'), 1600); };
const inr = (n) => '₹' + n.toLocaleString('en-IN');

function score(item) {
  const P = S.profile;
  const colour = Math.max(...P.palette.map(p => 1 - Math.min(cdist(p, item.hex), 400) / 400)) - (P.avoid.some(a => cdist(a, item.hex) < 120) ? .35 : 0);
  const tag = item.tags.filter(t => P.tags.includes(t)).length / Math.min(item.tags.length, 3);
  const learned = item.tags.reduce((a, t) => a + (S.tagW[t] || 0), 0) / 6;
  const icon = Math.min(.15, S.icons.reduce((a, i) => a + item.tags.filter(t => ICONS[i][1].includes(t)).length, 0) * .04); // style icons nudge the ranking
  return Math.max(0, Math.min(1, .55 * colour + .35 * tag + .1 * (isNeutral(item.hex) ? .8 : 0) + learned + icon - (washesOut(item.hex) ? .25 : 0)));
}
function why(item) {
  const P = S.profile, closest = P.palette.reduce((a, p) => cdist(p, item.hex) < cdist(a, item.hex) ? p : a);
  const shared = item.tags.filter(t => P.tags.includes(t));
  const colourLine = washesOut(item.hex) ? `Close to your skin tone — may wash you out`
    : P.avoid.some(a => cdist(a, item.hex) < 120) ? `Clashes with your ${P.skin.undertone} undertone`
    : cdist(closest, item.hex) < 140 ? `Flatters your ${P.skin.depth}, ${P.skin.undertone}-undertone skin`
    : isNeutral(item.hex) ? 'A neutral that anchors your palette' : 'A stretch colour for you';
  const echo = S.icons.map(i => ICONS[i]).filter(([, tg]) => tg.some(t => item.tags.includes(t)))[0];
  return `${colourLine}${shared.length ? ' · fits your ' + shared.join(', ') + ' side' : ''}${echo ? ' · echoes ' + echo[0] : ''}.`;
}

// ---------- 1. Upload ----------
function renderSlots() {
  $('slots').innerHTML = Array.from({ length: 6 }, (_, i) => i < 5
    ? (S.photos[i] ? `<div class="slot filled" style="background-image:url(${S.photos[i]})"><span class="x" onclick="event.stopPropagation();S.photos.splice(${i},1);renderSlots()">✕</span></div>` : `<div class="slot" onclick="$('file').click()">+</div>`)
    : `<div class="slot" style="font-size:13px;text-align:center;padding:8px;cursor:default">${S.photos.length}/5 photos</div>`).join('');
  $('analyzeBtn').disabled = S.photos.length < 1;
  $('analyzeBtn').textContent = S.photos.length >= 5 ? 'Analyse my style' : `Analyse my style (${S.photos.length}/5)`;
}
function shrink(file) { // downscale so uploads are fast and fit API limits
  return new Promise(res => { const r = new FileReader(); r.onload = async () => {
    const img = await loadImg(r.result), k = Math.min(1, 900 / Math.max(img.width, img.height));
    const c = document.createElement('canvas'); c.width = img.width * k; c.height = img.height * k;
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height); res(c.toDataURL('image/jpeg', .85)); }; r.readAsDataURL(file); });
}
$('file').onchange = async (e) => { for (const f of [...e.target.files].slice(0, 5 - S.photos.length)) S.photos.push(await shrink(f)); e.target.value = ''; renderSlots(); };
$('demoBtn').onclick = () => { S.profile = applySkin({ ...DEMO }, classifySkin(SKIN_SWATCHES.medium, 'warm')); renderProfile(); };
function setSkin(depth, undertone) { applySkin(S.profile, { ...S.profile.skin, hex: SKIN_SWATCHES[depth], depth, undertone, guessed: false, manual: true }); renderProfile(); }
$('analyzeBtn').onclick = async () => {
  show('s-profile');
  $('profileBody').innerHTML = `<div class="spinner"></div><p class="mute" style="text-align:center">Reading your aesthetic, colour season and silhouettes…</p>`;
  try {
    if (!S.ai.claude) throw 0;
    const r = await fetch('/api/analyze', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ images: S.photos }) });
    if (!r.ok) throw new Error((await r.json()).error);
    S.profile = await r.json();
  } catch (e) { if (e) console.warn('Claude failed, using on-device analysis:', e); S.profile = await localAnalyze(S.photos); }
  // Skin tone drives the palette for everyone, whichever analysis ran.
  const ai = S.profile.skin || {};
  const hex = /^#[0-9a-f]{6}$/i.test(ai.hex || '') ? ai.hex : await detectSkin(S.photos);
  applySkin(S.profile, hex ? classifySkin(hex, ai.undertone) : { ...classifySkin(SKIN_SWATCHES.medium, 'neutral'), guessed: true });
  renderProfile();
};

// ---------- 2. Profile ----------
function renderProfile() {
  const P = S.profile; show('s-profile');
  $('profileBody').innerHTML = `
    <div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Your style DNA</span></div>
    <div class="kicker"><b>02</b>Your style DNA</div>
    <div class="box"><p class="mute" style="font-size:13px">You are</p><h1>${P.aesthetic}</h1><p style="margin-top:8px">${P.summary}</p>
      <div style="margin-top:10px">${P.tags.map(t => `<span class="tag">#${t}</span>`).join('')}</div></div>
    <h3>Your skin tone${P.skin.guessed ? ' · couldn\'t detect, pick yours' : P.skin.manual ? ' · set by you' : ' · auto-detected'}</h3>
    <div class="box"><div class="row"><div class="sw" style="background:${P.skin.hex};border-radius:50%"></div><p class="grow" style="font-size:14px">${P.skinNote}</p></div>
      <p class="mute" style="font-size:12px;margin:12px 0 6px">Not quite right? Adjust:</p>
      <div class="row">${DEPTHS.map(d => `<div class="sw" title="${d}" onclick="setSkin('${d}','${P.skin.undertone}')" style="background:${SKIN_SWATCHES[d]};border-radius:50%;width:36px;height:36px;cursor:pointer;outline:${P.skin.depth === d ? '3px solid var(--accent)' : 'none'};outline-offset:2px"></div>`).join('')}</div>
      <div class="row" style="margin-top:10px">${['warm','neutral','cool'].map(u => `<button class="${P.skin.undertone === u ? '' : 'ghost'}" style="padding:8px 12px;font-size:13px" onclick="setSkin('${P.skin.depth}','${u}')">${u}</button>`).join('')}</div></div>
    <h3>Your colours · ${P.season}</h3><div class="swatches">${P.palette.map(h => `<div class="sw" style="background:${h}" title="${h}"></div>`).join('')}</div>
    <h3>Go easy on</h3><div class="swatches">${P.avoid.map(h => `<div class="sw avoid" style="background:${h}" title="${h}"></div>`).join('')}</div>
    <h3>Who do you dress like?</h3><p class="mute" style="font-size:13px;margin-bottom:10px">Pick your style icons. We'll suggest pieces inspired by them, tuned to your colours.</p>
    <div class="chips">${ICONS.map(([n], i) => `<button class="chip ghost${S.icons.includes(i) ? ' on' : ''}" onclick="toggleIcon(${i}, this)">${n}</button>`).join('')}</div>
    <div class="stack" style="margin-top:26px"><button onclick="startDeck()">Start swiping →</button></div>`;
}

// ---------- 3. Deck ----------
function startDeck() {
  S.deck = CATALOG.filter(i => !ACCESSORY.includes(i.type)).sort((a, b) => score(b) - score(a));
  show('s-deck'); renderDeck();
}
function renderDeck() {
  $('likedPill').textContent = '♥ ' + S.liked.length; $('savedPill').textContent = '⬇ ' + S.saved.length;
  if (!S.deck.length) { $('deck').innerHTML = `<div class="box" style="text-align:center;margin-top:40px"><h2>You've seen it all ✨</h2><p class="mute">Check your likes and saves.</p><br><button onclick="renderList()">My collection</button></div>`; return; }
  $('deck').innerHTML = S.deck.slice(0, 3).reverse().map((it, i, arr) => {
    const depth = arr.length - 1 - i;
    return `<div class="card" data-id="${it.id}" style="transform:scale(${1 - depth * .04}) translateY(${depth * 14}px);z-index:${10 - depth}">
      <div class="stamp like">LIKE</div><div class="stamp nope">NOPE</div><div class="stamp save">SAVED</div>
      <div class="art" style="background:radial-gradient(circle at 50% 40%, ${it.hex}33, transparent 70%)">${garmentSVG(it)}</div>
      <div class="info"><div class="row"><div class="name grow">${it.name}</div><span class="match">${Math.round(score(it) * 100)}%</span></div>
        <div class="mute">${it.brand} · ${priceText(it, true)}</div>
        <div class="mute" style="font-size:13px;margin-top:4px">${why(it)}</div></div></div>`;
  }).join('');
  bindDrag($('deck').lastElementChild);
}
function bindDrag(card) {
  let sx, sy, dx = 0, dy = 0, down = false;
  const stamps = (k, v) => card.querySelector('.stamp.' + k).style.opacity = v;
  card.onpointerdown = (e) => { down = true; sx = e.clientX; sy = e.clientY; dx = dy = 0; card.classList.add('drag'); card.setPointerCapture(e.pointerId); };
  card.onpointermove = (e) => {
    if (!down) return; dx = e.clientX - sx; dy = e.clientY - sy;
    card.style.transform = `translate(${dx}px,${dy}px) rotate(${dx / 18}deg)`;
    stamps('like', Math.max(0, dx / 100)); stamps('nope', Math.max(0, -dx / 100)); stamps('save', Math.max(0, (dy - Math.abs(dx)) / 100));
  };
  card.onpointerup = () => {
    down = false; card.classList.remove('drag');
    if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return openDetail(card.dataset.id);
    if (dx > 100) swipe('like'); else if (dx < -100) swipe('nope'); else if (dy > 100) swipe('save');
    else { card.style.transform = ''; ['like','nope','save'].forEach(k => stamps(k, 0)); }
  };
}
function swipe(kind) {
  const it = S.deck[0]; if (!it) return;
  const card = $('deck').lastElementChild;
  card.querySelector('.stamp.' + kind).style.opacity = 1;
  card.style.transform = kind === 'like' ? 'translate(150%,0) rotate(25deg)' : kind === 'nope' ? 'translate(-150%,0) rotate(-25deg)' : 'translate(0,130%)';
  if (kind === 'like') S.liked.push(it); if (kind === 'save') S.saved.push(it);
  // learn: nudge tag weights so the rest of the deck re-ranks to your taste
  it.tags.forEach(t => S.tagW[t] = (S.tagW[t] || 0) + (kind === 'nope' ? -.08 : .1));
  S.deck.shift(); S.deck.sort((a, b) => score(b) - score(a));
  setTimeout(renderDeck, 260);
}
document.addEventListener('keydown', (e) => {
  if (!$('s-deck').classList.contains('on')) return;
  ({ ArrowRight: () => swipe('like'), ArrowLeft: () => swipe('nope'), ArrowDown: () => swipe('save'), Enter: () => S.deck[0] && openDetail(S.deck[0].id) })[e.key]?.();
});

// ---------- 4. Detail: best price, best quality, complete the look ----------
function completeLook(item) {
  const need = TOPS.includes(item.type) ? ['trousers','skirt'] : BOTTOMS.includes(item.type) ? ['tee','shirt','jacket'] : [];
  const pick = (types) => CATALOG.filter(c => types.includes(c.type) && c.id !== item.id)
    .map(c => ({ c, s: harmony(item.hex, c.hex) + .15 * c.tags.filter(t => item.tags.includes(t)).length + .3 * score(c) }))
    .sort((a, b) => b.s - a.s)[0]?.c;
  return [need.length && pick(need), pick(['shoes']), pick(['bag','watch']), pick(['sunglasses','cap'])].filter(Boolean);
}
function openDetail(id) {
  const it = findItem(id), o = offers(it), look = completeLook(it);
  const lookTotal = look.reduce((a, c) => a + offers(c).best.price.price, offers(it).best.price.price);
  S.current = it; show('s-detail');
  $('detailBody').innerHTML = `
    <button class="back" onclick="closeSheet()">← Close</button>
    <div class="hero" style="background:radial-gradient(circle at 50% 40%, ${it.hex}40, var(--card) 70%)">${garmentSVG(it)}</div>
    <div class="row" style="margin-top:14px"><h2 class="grow">${it.name}</h2><span class="match">${Math.round(score(it) * 100)}% match</span></div>
    <p class="mute">${it.brand} · ${why(it)}</p>
    <h3>Best deals across ${o.list.length} stores</h3>
    <table>${o.list.map(x => `<tr><td>${x.store}${x === o.best.price ? '<span class="badge b-price">LOWEST</span>' : ''}${x === o.best.quality ? '<span class="badge b-qual">TOP RATED</span>' : ''}${x === o.best.value ? '<span class="badge b-val">BEST VALUE</span>' : ''}<div class="mute" style="font-size:12px">★ ${x.quality} · ${x.delivery}-day delivery</div></td><td>${inr(x.price)}</td></tr>`).join('')}</table>
    <h3>Complete the look</h3>
    <div class="pairs">${look.map(c => `<div class="pair" onclick="openDetail('${c.id}')">${garmentSVG(c)}<div>${c.name}</div><div class="mute">${priceText(c)}</div></div>`).join('')}</div>
    <p class="mute" style="margin-top:8px;font-size:13px">Whole outfit at best prices: <b style="color:var(--ink)">${inr(lookTotal)}</b></p>
    <div class="stack" style="margin-top:18px">
      <button onclick="openTryOn()">✨ Try it on me</button>
      <button class="ghost" onclick="toast('Opening ${o.best.value.store}… (demo)')">Buy at ${o.best.value.store} · ${inr(o.best.value.price)}</button>
    </div>`;
}

// ---------- 5. AI try-on ----------
function svgToPng(item) { // render garment art to a PNG for the try-on model
  return new Promise(res => { const img = new Image(); img.onload = () => {
    const c = document.createElement('canvas'); c.width = 400; c.height = 480; const x = c.getContext('2d');
    x.fillStyle = '#fff'; x.fillRect(0, 0, 400, 480); x.drawImage(img, 0, 0, 400, 480); res(c.toDataURL('image/png')); };
    img.src = item.img || 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(garmentSVG(item)); });
}
async function openTryOn(personIdx = 0) {
  const it = S.current; show('s-tryon');
  const person = S.photos[personIdx];
  const head = `<button class="back" onclick="openDetail('${it.id}')">← Back</button><h2>Try-on · ${it.name}</h2>`;
  if (!person) {
    $('tryonBody').innerHTML = head + `<p class="mute">Upload a full-length photo of yourself to try this on.</p><br>
      <input type="file" id="tf" accept="image/*" hidden><button onclick="$('tf').click()">Upload photo</button>`;
    $('tf').onchange = async (e) => { S.photos.push(await shrink(e.target.files[0])); openTryOn(S.photos.length - 1); };
    return;
  }
  const picker = S.photos.length > 1 ? `<h3>Pick a photo</h3><div class="row">${S.photos.map((p, i) => `<img src="${p}" onclick="openTryOn(${i})" style="width:48px;height:64px;object-fit:cover;border-radius:8px;cursor:pointer;border:2px solid ${i === personIdx ? 'var(--accent)' : 'transparent'}">`).join('')}</div>` : '';
  if (S.ai.tryon) {
    $('tryonBody').innerHTML = head + `<div class="tryon"><img src="${person}" style="filter:blur(2px) brightness(.6)"><div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center"><div class="spinner" style="margin:0 0 12px"></div>Dressing you up…</div></div>`;
    try {
      const r = await fetch('/api/tryon', { method:'POST', headers:{'content-type':'application/json'},
        body: JSON.stringify({ person, garment: await svgToPng(it), description: `${it.name}, colour ${it.hex}` }) });
      const j = await r.json(); if (!r.ok) throw new Error(j.error);
      $('tryonBody').innerHTML = head + `<div class="tryon"><img src="${j.image}"></div>${picker}<div class="stack" style="margin-top:16px"><button onclick="toast('Added to bag (demo)')">Looks good — add to bag</button></div>`;
      return;
    } catch (e) { console.warn('try-on API failed, using preview overlay', e); toast('AI try-on unavailable — showing preview'); }
  }
  // Fallback: drag-and-scale overlay preview (works offline)
  $('tryonBody').innerHTML = head + `<p class="mute" style="font-size:13px;margin-bottom:8px">Preview mode — drag the piece onto yourself.</p>
    <div class="tryon" id="stage"><img src="${person}"><div class="overlay" id="ov">${garmentSVG(it)}</div></div>
    <h3>Size</h3><input type="range" min="25" max="110" value="62" oninput="$('ov').style.width=this.value+'%'">${picker}
    <div class="stack" style="margin-top:16px"><button onclick="toast('Added to bag (demo)')">Looks good — add to bag</button></div>`;
  const ov = $('ov'), st = $('stage'); let drag = false;
  ov.onpointerdown = (e) => { drag = true; ov.setPointerCapture(e.pointerId); };
  ov.onpointermove = (e) => { if (!drag) return; const b = st.getBoundingClientRect();
    ov.style.left = ((e.clientX - b.left) / b.width * 100) + '%'; ov.style.top = ((e.clientY - b.top) / b.height * 100) + '%'; };
  ov.onpointerup = () => drag = false;
}

// ---------- 6. Collection ----------
function renderList(tab) {
  if (typeof tab === 'string') S.listTab = tab; show('s-list');
  const arr = S.listTab === 'saved' ? S.saved : S.liked;
  const grid = arr.length ? `<div class="list">${arr.map(c => `<div class="pair" onclick="openDetail('${c.id}')">${garmentSVG(c)}<div>${c.name}</div><div class="mute">${priceText(c)}</div></div>`).join('')}</div>`
    : `<div class="empty"><h2>${S.listTab === 'saved' ? 'Nothing saved yet' : 'No likes yet'}</h2><p class="mute">${S.listTab === 'saved' ? 'Swipe down on a piece to keep it for later.' : 'Swipe right on pieces you love.'}</p></div>`;
  $('listBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">${S.saved.length + S.liked.length} pieces</span></div>
    <div class="kicker"><b>${String(S.saved.length).padStart(2, '0')}</b>Your collection</div>
    <div class="seg"><button class="${S.listTab === 'saved' ? 'on' : ''}" onclick="renderList('saved')">Saved · ${S.saved.length}</button><button class="${S.listTab === 'liked' ? 'on' : ''}" onclick="renderList('liked')">Liked · ${S.liked.length}</button></div>${grid}`;
}
$('likedPill').onclick = () => renderList('liked'); $('savedPill').onclick = () => renderList('saved');
$('likedPill').style.cursor = $('savedPill').style.cursor = 'pointer';

// ---------- Style icons ----------
function toggleIcon(i, btn) {
  const k = S.icons.indexOf(i); k < 0 ? S.icons.push(i) : S.icons.splice(k, 1); btn.classList.toggle('on', k < 0);
  if (S.deck.length) S.deck.sort((a, b) => score(b) - score(a)); // re-rank the deck around the new icons
  toast(k < 0 ? `Inspired by ${ICONS[i][0]}` : `Removed ${ICONS[i][0]}`);
}

// ---------- Today: weather outfit ----------
const WMO = (c) => c === 0 ? 'Clear sky' : c <= 3 ? 'Partly cloudy' : c <= 48 ? 'Foggy' : c <= 57 ? 'Drizzle' : c <= 67 ? 'Rain' : c <= 77 ? 'Snow' : c <= 82 ? 'Showers' : 'Thunderstorm';
async function renderToday() {
  show('s-today');
  $('todayBody').innerHTML = `<div class="spinner"></div><p class="mute" style="text-align:center">Checking the sky…</p>`;
  const [lat, lon] = S.coords || [28.61, 77.21], place = S.place || 'New Delhi';
  let w; // ponytail: Open-Meteo (free, no key); falls back to a demo day if offline
  try { const j = (await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,precipitation,weather_code&timezone=auto`).then(r => r.json())).current;
    w = { t: Math.round(j.temperature_2m), code: j.weather_code, rain: j.precipitation > 0 || (j.weather_code >= 51 && j.weather_code <= 67) || (j.weather_code >= 80) };
  } catch { w = { t: 24, code: 0, rain: false, offline: true }; }
  const mood = w.rain ? 'rain' : w.t < 16 ? 'cold' : w.t >= 29 ? 'hot' : 'mild';
  const best = (type, ok = () => true) => CATALOG.filter(c => c.type === type && ok(c)).sort((a, b) => score(b) - score(a))[0];
  const plan = { rain: [['jacket'], ['trousers'], ['shoes', c => !/Sandal|Flip/i.test(c.name)], ['bag']], cold: [[w.t < 9 ? 'jacket' : 'hoodie'], ['trousers'], ['shoes', c => /Boot/i.test(c.name)], ['cap']],
    hot: [['tee'], ['skirt'], ['shoes', c => /Sandal/i.test(c.name)], ['sunglasses']], mild: [['shirt'], ['trousers'], ['shoes', c => !/Flip|Slide/i.test(c.name)], ['bag']] }[mood];
  const line = { rain: 'Rain today. Stay dry in a water-repellent layer with closed shoes.', cold: 'Chilly out. Go cosy: layers, straight-leg trousers and boots.', hot: 'A hot one. Light, breathable pieces, and sunglasses.', mild: 'Perfect weather. Easy layers, and almost anything works.' }[mood];
  const pieces = plan.map(([t, f]) => best(t, f)).filter(Boolean), total = pieces.reduce((a, c) => a + offers(c).best.price.price, 0);
  $('todayBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">${new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}</span></div>
    <div class="kicker"><b>${mood === 'rain' ? '☂' : mood === 'hot' ? '☀' : mood === 'cold' ? '❄' : '◐'}</b>Today in ${place}</div>
    <div class="temp">${w.t}<sup>°C</sup></div><p style="margin:6px 0 4px;font:italic 400 22px var(--serif)">${WMO(w.code)}${w.offline ? ' · demo weather (offline)' : ''}</p>
    <p class="mute" style="max-width:34ch">${line}</p>
    <h3>Wear this today · ${inr(total)}</h3>
    <div class="look">${pieces.map(c => `<div class="pair" onclick="openDetail('${c.id}')">${garmentSVG(c)}<div>${c.name}</div><div class="mute">${priceText(c)}</div></div>`).join('')}</div>
    <div class="stack" style="margin-top:18px"><button onclick="S.current=CATALOG.find(c=>c.id===${pieces[0]?.id});openTryOn()">✨ Try the look on me</button>
      <button class="ghost" onclick="useLocation()">📍 Use my location</button></div>`;
}
function useLocation() {
  if (!navigator.geolocation) return toast('Location not available');
  navigator.geolocation.getCurrentPosition(p => { S.coords = [p.coords.latitude, p.coords.longitude]; S.place = 'your area'; renderToday(); }, () => toast('Location blocked, using New Delhi'));
}

// ---------- Wallet + sale auto-buy (simulation) ----------
function addMoney(n) { S.wallet += n; toast(`+${inr(n)} added (simulated)`); renderWallet(true); }
function saleDrop() {
  const items = S.saved.slice(), address = ($('addr') || {}).value || S.address;
  if (!items.length) return toast('Save a few pieces first (swipe down)');
  if (!address || !address.trim()) return toast('Add a delivery address first');
  S.address = address.trim();
  const total = items.reduce((a, c) => a + Math.round(offers(c).best.price.price * .7), 0);
  if (S.wallet < total) return toast(`Add ${inr(total - S.wallet)} more to your wallet`);
  S.wallet -= total; S.orders.unshift({ id: 'AL-' + (1040 + S.orders.length + 1), items, total, address: S.address });
  S.saved = []; toast('Sale is live. Order placed!'); renderWallet(true);
}
function renderWallet(keep) {
  show('s-wallet'); if (keep === true) window.scrollTo(0, 0);
  const sale = (c) => Math.round(offers(c).best.price.price * .7), watch = S.saved, need = watch.reduce((a, c) => a + sale(c), 0);
  $('walletBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Simulation</span></div>
    <div class="kicker"><b>04</b>Wallet</div>
    <div class="wcard"><small>Balance</small><div class="amt">${inr(S.wallet)}</div><div class="chips">${[500, 1000, 5000].map(n => `<button class="chip ghost" onclick="addMoney(${n})">+ ${inr(n)}</button>`).join('')}</div></div>
    <h3>Watching for the sale · ${watch.length} piece${watch.length === 1 ? '' : 's'}</h3>
    ${watch.length ? `<div class="list">${watch.map(c => `<div class="pair" onclick="openDetail('${c.id}')">${garmentSVG(c)}<div>${c.name}</div><div class="mute">sale ~ ${inr(sale(c))}</div></div>`).join('')}</div>
      <p class="mute" style="font-size:13px;margin-top:10px">Expected at 30% off: <b style="color:var(--ink)">${inr(need)}</b></p>` : `<div class="empty"><h2>Nothing to watch yet</h2><p class="mute">Swipe down on pieces you want. Alluré buys them the second the sale goes live.</p></div>`}
    <input class="field" id="addr" placeholder="Delivery address" value="${S.address || ''}">
    <div class="stack" style="margin-top:14px"><button onclick="saleDrop()">⚡ Simulate Black Friday drop</button></div>
    ${S.orders.length ? `<h3>Orders</h3>${S.orders.map(o => `<div class="order"><b>#${o.id} · ${inr(o.total)}</b><div class="mute" style="font-size:13px">${o.items.map(i => i.name).join(', ')}</div><div style="font-size:12px;margin-top:6px">Arriving in 3–5 days · ${o.address}</div></div>`).join('')}` : ''}
    <p class="mute" style="font-size:11px;margin-top:22px;text-align:center">Simulation only. No real payments are made.</p>`;
}

// ---------- boot ----------
renderSlots();
loadProducts();
const OFF = { renderToday, openDetail, openTryOn, swipe, startDeck, renderDeck, renderList, renderProfile, renderSlots };
setTimeout(() => { $('splash').classList.add('out'); setTimeout(() => $('splash').remove(), 1000); }, 1500);
</script>
<script>
/* ===== Live mode: the team's FastAPI backend (docs/BACKEND_BLUEPRINT.md, docs/API_CONTRACT.md) =====
   Same-origin proxy: /api/v1/* -> backend. If the backend is unreachable the app falls back to the offline demo above. */
const B = { live: false, token: null, name: '', caps: {}, prefs: {} };
const rid = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now() + '-' + Math.random());
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
const spin = (t) => `<div class="spinner"></div><p class="mute" style="text-align:center">${t}</p>`;
class ApiError extends Error { constructor(code, message, status, requestId) { super(message); Object.assign(this, { code, status, requestId }); } }
async function api(path, o = {}) {
  const headers = { ...(o.headers || {}) }; let body;
  if (B.token) headers.Authorization = 'Bearer ' + B.token;
  if (o.json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(o.json); } else if (o.form) body = o.form; // browser sets the multipart boundary
  const r = await fetch('/api/v1' + path, { method: o.method || (body ? 'POST' : 'GET'), headers, body, signal: o.signal });
  if (o.raw) { if (!r.ok) throw new ApiError('HTTP_ERROR', 'Request failed', r.status); return r; }
  let j; try { j = await r.json(); } catch { throw new ApiError('BAD_RESPONSE', 'Unexpected response from the server.', r.status); }
  if (!r.ok || !j.success) { if (r.status === 401 && B.token) sessionExpired(); throw new ApiError(j.error?.code || 'ERROR', j.error?.message || 'Request failed', r.status, j.request_id); }
  return j.data;
}
const explain = (e) => e.name === 'AbortError' ? 'Stopped waiting. The server may still be working.' : e.code === 'BACKEND_UNREACHABLE' ? 'Can’t reach the Alluré backend.'
  : e.status === 503 ? 'This feature isn’t enabled on the server yet.' : e.status === 429 ? 'Limit reached. Please try again later.' : e.status === 401 ? 'Your session expired.' : (e.message || 'Something went wrong.');
const errBox = (e, extra = '') => `<div class="empty"><h2>Not available</h2><p class="mute">${esc(explain(e))}</p>${e.requestId ? `<p class="mute" style="font-size:11px;margin-top:8px">ref ${esc(e.requestId)}</p>` : ''}${extra}</div>`;
function sessionExpired() { B.token = null; sessionStorage.removeItem('allure_token'); S.ready = false; showWelcome('Your session expired. Please reconnect.'); }

// ---------- product adapter: backend Product -> the card shape the UI already renders ----------
const COLOR_HEX = { beige: '#d6c4a6', olive: '#6b6b3a', black: '#18181b', white: '#fafafa', navy: '#22304f', red: '#c0392b', blue: '#3b5b8c', grey: '#8a8d91', gray: '#8a8d91', brown: '#6d4c35', green: '#2f5d46', cream: '#f1e9d8', burgundy: '#6e1f2c', pink: '#e8b4b0', yellow: '#d8a42c', orange: '#c4683f', purple: '#9677be', tan: '#b88a5a', neutral: '#cfc9bd' };
const ITEMS = new Map();
function typeOf(p) {
  const t = (p.title || '').toLowerCase();
  const rules = [[/t-?shirt|\btee\b|top\b/, 'tee'], [/hood|sweatshirt|knit|jumper/, 'hoodie'], [/shell|jacket|coat|blazer|bomber|puffer|windbreaker/, 'jacket'], [/shirt/, 'shirt'], [/dress/, 'dress'], [/skirt/, 'skirt'],
    [/trouser|pant|jean|short/, 'trousers'], [/sneaker|boot|shoe|sandal|loafer|flip/, 'shoes'], [/bag|tote|pouch/, 'bag'], [/cap\b|hat|beanie/, 'cap'], [/sunglass/, 'sunglasses'], [/watch/, 'watch']];
  return (rules.find(([re]) => re.test(t)) || [])[1] || { tops: 'tee', bottoms: 'trousers', footwear: 'shoes', 'one-pieces': 'dress', accessories: 'bag' }[p.category] || 'tee';
}
function fromApi(p, extra = {}) {
  const img = p.image_url && (/^\/products\//.test(p.image_url) || /^https:\/\//.test(p.image_url)) ? esc(p.image_url) : null; // never trust merchant strings in markup
  const it = { id: p.id, name: esc(p.title), type: typeOf(p), hex: COLOR_HEX[(p.colors || [])[0]] || '#cfc9bd', tags: p.aesthetics || [], price: p.price, currency: p.currency,
    brand: esc(p.brand || ''), merchant: esc(p.merchant || ''), url: /^https?:\/\//.test(p.merchant_url || '') ? p.merchant_url : null, img, demo: !!p.is_demo, raw: p, ...extra };
  ITEMS.set(String(p.id), it); return it;
}
const findItem = (id) => ITEMS.get(String(id)) || CATALOG.find((c) => String(c.id) === String(id));
function priceText(c, from) {
  if (!B.live) return (from ? 'from ' : '') + inr(offers(c).best.price.price);
  return c.price != null ? (c.currency === 'INR' || !c.currency ? inr(c.price) : c.price + ' ' + c.currency) : (c.demo ? 'Demo item · no price' : 'Price not listed');
}
const pairCard = (c, sub) => `<div class="pair" onclick="openDetail('${c.id}')">${garmentSVG(c)}<div>${c.name}</div><div class="mute">${sub ?? priceText(c)}</div></div>`;
const dataBlob = (u) => { const [h, b] = u.split(','), m = /:(.*?);/.exec(h)[1], bin = atob(b), a = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i); return new Blob([a], { type: m }); };

// ---------- navigation ----------
function go(t) {
  closeSheet();
  ({ deck: () => (S.deck.length || !B.live ? (show('s-deck'), renderDeck()) : startDeck()), today: renderToday, chat: renderChat, saved: renderList, you: renderProfile, wallet: () => go('you') })[t]();
}
function showWelcome(msg) {
  show('s-welcome');
  $('welcomeBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Find your kind of style</span></div>
    <div class="kicker"><b>00</b>Welcome</div><h1>What should we call you?</h1>
    <p class="mute" style="margin-top:8px">A name is all we need. Everything else you choose to share, when you choose to.</p>
    ${msg ? `<p style="margin-top:12px;color:var(--nope);font-size:13px">${esc(msg)}</p>` : ''}
    <input class="field" id="nameIn" maxlength="60" placeholder="Your name" autocomplete="off">
    <div class="stack" style="margin-top:14px"><button id="nameBtn">Continue</button></div>
    <p class="mute" style="font-size:11px;margin-top:18px">Prototype session: no password. Your data stays tied to this session and can be deleted any time from You.</p>`;
  const go_ = async () => { const name = $('nameIn').value.trim(); if (!name) return toast('Tell us your name'); $('nameBtn').disabled = true;
    try { const d = await api('/sessions', { json: { name } }); B.token = d.token; B.name = d.name; sessionStorage.setItem('allure_token', d.token); sessionStorage.setItem('allure_name', d.name); S.ready = true; prepUpload(); show('s-upload'); }
    catch (e) { $('nameBtn').disabled = false; toast(explain(e)); } };
  $('nameBtn').onclick = go_; $('nameIn').onkeydown = (e) => e.key === 'Enter' && go_();
}

// ---------- onboarding: exactly five reference photos -> POST /style/analyze ----------
function prepUpload() {
  document.querySelector('#s-upload h1').textContent = 'Show us your favourite fits.';
  $('upLead').textContent = 'Upload 1 to 5 outfits you love: the more you add, the better we know your taste. We read the clothes, never you.';
  $('upNote').textContent = B.caps.vision ? 'Only the photos you pick are uploaded, analysed, and not stored. Clothing only: no age, face or body analysis.'
    : 'AI photo analysis isn’t enabled on this server, so we’ll read the main colours in your photos right here on your device. Nothing is uploaded.';
  $('demoBtn').textContent = 'Set my style by hand';
  $('demoBtn').onclick = () => { S.ready = true; renderProfile().then(editPrefs); }; $('analyzeBtn').onclick = runAnalyze; renderSlots();
}
function renderSlots() { OFF.renderSlots(); if (!B.live) return; const n = S.photos.length; $('analyzeBtn').disabled = n < 1; $('analyzeBtn').textContent = n < 1 ? 'Add at least 1 photo' : B.caps.vision ? `Analyse my style (${n}/5)` : `Read my colours (${n}/5)`; }
const NAMED_COLORS = ['black','white','beige','navy','olive','brown','grey','blue','green','red','burgundy','cream'];
async function deviceRead() { // no vision model configured: dominant colours of the photos, computed in the browser and saved as colour preferences
  const read = await localAnalyze(S.photos), me = await api('/me'), P = me.preferences || {};
  const near = (hex) => NAMED_COLORS.reduce((a, n) => cdist(hex, COLOR_HEX[n]) < cdist(hex, COLOR_HEX[a]) ? n : a);
  const colours = [...new Set(read.palette.map(near))].slice(0, 5);
  B.prefs = await api('/me/preferences', { method: 'PUT', json: { aesthetics: P.aesthetics || [], preferred_colors: colours, silhouettes: P.silhouettes || [], garment_preferences: P.garment_preferences || [], budget: P.budget ?? null, size: P.size ?? null, department: P.department ?? null } });
  S.deck = []; S.seen.clear();
  return { device: true, style_profile: { aesthetics: [], preferred_colors: colours } };
}
async function runAnalyze() {
  const n = S.photos.length; if (n < 1) return toast('Add at least one photo');
  show('s-profile'); $('profileBody').innerHTML = spin(B.caps.vision ? 'Reading the clothes in your outfits…' : 'Reading the main colours in your photos…');
  S.analysis = null; S.analysisError = null;
  try {
    if (!B.caps.vision) S.analysis = await deviceRead();
    else {
      const send = (list) => { const form = new FormData(); list.forEach((p, i) => form.append('images', dataBlob(p), `outfit${i + 1}.jpg`)); return api('/style/analyze', { form }); };
      try { S.analysis = await send(S.photos); }
      catch (e) { if (e.code !== 'IMAGE_COUNT' || n >= 5) throw e; // older backend that insists on exactly five: repeat the photos to fill five slots
        S.analysis = await send(Array.from({ length: 5 }, (_, i) => S.photos[i % n])); }
      toast('Style profile saved');
    }
  } catch (e) { S.analysisError = e; }
  renderProfile();
}

// ---------- Discover: GET /recommendations, POST /swipes ----------
S.seen = new Set();
async function fetchFeed(includeSeen = false, limit = 24) { const d = await api(`/recommendations?limit=${limit}&include_seen=${includeSeen}`); return d.items.map((e) => fromApi(e.product, { score: e.score, reasons: e.reasons })); }
async function startDeck() {
  if (!B.live) return OFF.startDeck();
  show('s-deck'); $('deck').innerHTML = spin('Finding pieces for you…');
  try { S.deck = (await fetchFeed()).filter((i) => !S.seen.has(i.id)); } catch (e) { $('deck').innerHTML = errBox(e, '<br><button onclick="startDeck()">Try again</button>'); return; }
  renderDeck();
}
function renderDeck() {
  if (!B.live) return OFF.renderDeck();
  $('likedPill').textContent = '♥ ' + S.liked.length; $('savedPill').textContent = '⬇ ' + S.saved.length;
  if (!S.deck.length) { $('deck').innerHTML = `<div class="empty" style="margin-top:30px"><h2>You’ve seen everything ✨</h2><p class="mute">Passed pieces stay hidden. Want another look at the rest?</p><br><button onclick="again()">See them again</button></div>`; return; }
  $('deck').innerHTML = S.deck.slice(0, 3).reverse().map((it, i, arr) => { const depth = arr.length - 1 - i;
    return `<div class="card" data-id="${it.id}" style="transform:scale(${1 - depth * .04}) translateY(${depth * 14}px);z-index:${10 - depth}">
      <div class="stamp like">LIKE</div><div class="stamp nope">NOPE</div><div class="stamp save">SAVED</div>
      <div class="art" style="background:radial-gradient(circle at 50% 40%, ${it.hex}33, transparent 70%)">${garmentSVG(it)}</div>
      <div class="info"><div class="row"><div class="name grow">${it.name}</div>${it.demo ? '<span class="match" style="color:var(--mute)">DEMO</span>' : ''}</div>
        <div class="mute">${it.brand || 'Alluré catalogue'} · ${priceText(it)}</div>
        <div class="mute" style="font-size:13px;margin-top:4px">${esc((it.reasons || [])[0] || '')}</div></div></div>`; }).join('');
  bindDrag($('deck').lastElementChild);
}
async function again() { try { const all = await fetchFeed(true, 50); S.deck = all; renderDeck(); } catch (e) { toast(explain(e)); } }
async function sendSwipe(id, action, key, tries = 3) { // same Idempotency-Key on every retry of one action
  for (let i = 0; i < tries; i++) { try { return await api('/swipes', { json: { product_id: id, action }, headers: { 'Idempotency-Key': key } }); } catch (e) { if (e.status && e.status < 500) throw e; await new Promise((r) => setTimeout(r, 600 * (i + 1))); } }
  throw new ApiError('NETWORK', 'Could not reach the server.');
}
function swipe(kind) {
  if (!B.live) return OFF.swipe(kind);
  const it = S.deck[0]; if (!it) return; const card = $('deck').lastElementChild;
  card.querySelector('.stamp.' + kind).style.opacity = 1;
  card.style.transform = kind === 'like' ? 'translate(150%,0) rotate(25deg)' : kind === 'nope' ? 'translate(-150%,0) rotate(-25deg)' : 'translate(0,130%)';
  if (kind === 'like') S.liked.push(it); if (kind === 'save') S.saved.push(it);
  S.seen.add(it.id); S.deck.shift();
  sendSwipe(it.id, kind === 'nope' ? 'dislike' : kind, rid()).catch((e) => toast('Couldn’t record that swipe: ' + explain(e)));
  setTimeout(() => { renderDeck(); if (S.deck.length < 4) topUp(); }, 260);
}
let topping = false;
async function topUp() { if (topping) return; topping = true; try { const more = (await fetchFeed()).filter((i) => !S.seen.has(i.id) && !S.deck.some((d) => d.id === i.id)); if (more.length) { S.deck.push(...more); if (S.tab === 's-deck') renderDeck(); } } catch {} topping = false; }

// ---------- item detail: real price only, live offers on demand, outfit completion ----------
function openDetail(id) {
  if (!B.live) return OFF.openDetail(id);
  const it = findItem(id); if (!it) return; S.current = it; show('s-detail');
  $('detailBody').innerHTML = `<button class="back" onclick="closeSheet()">← Close</button>
    <div class="hero" style="background:radial-gradient(circle at 50% 40%, ${it.hex}40, var(--card) 70%)">${garmentSVG(it)}</div>
    <div class="row" style="margin-top:14px"><h2 class="grow">${it.name}</h2>${it.demo ? '<span class="match" style="color:var(--mute)">DEMO</span>' : ''}</div>
    <p class="mute">${it.brand || 'Alluré catalogue'}${it.merchant && it.merchant !== it.brand ? ' · ' + it.merchant : ''}</p>
    <h3>Why it suits you</h3>${(it.reasons || ['Part of the catalogue']).map((r) => `<p style="font-size:14px;margin:4px 0">· ${esc(r)}</p>`).join('')}
    <h3>Price</h3>
    <div class="row"><div class="grow" style="font:600 30px var(--serif)">${priceText(it)}</div></div>
    <p class="mute" style="font-size:12px;margin-top:4px">${it.demo ? 'Fictional example: no price, stock or purchase link.' : 'Listed price. Shipping, stock and size are unverified.'}</p>
    <div id="offerBox"></div>
    <h3>Complete the look</h3><div id="lookBox">${spin('Picking pieces that go with it…')}</div>
    <div class="stack" style="margin-top:18px"><button onclick="openTryOn()">✨ Try it on me</button>
      ${it.url ? `<a class="btn ghost" style="text-align:center;text-decoration:none;padding:16px 18px;border:1px solid var(--ink);color:var(--ink);font:600 13px var(--sans);letter-spacing:.1em;text-transform:uppercase" href="${esc(it.url)}" target="_blank" rel="noopener noreferrer">View at ${esc(it.merchant || 'merchant')}</a>` : ''}
      ${!it.demo && B.caps.shopping ? `<button class="ghost" onclick="liveOffers()">Compare live offers</button>` : ''}</div>
    ${!B.caps.shopping ? '<p class="mute" style="font-size:12px;margin-top:10px">Live price comparison needs shopping search enabled on the server.</p>' : ''}`;
  api('/outfits/complete', { json: { product_id: it.id } }).then((d) => {
    const items = d.items.map((e) => fromApi(e.product, { reasons: e.reasons }));
    $('lookBox') && ($('lookBox').innerHTML = items.length ? `<div class="pairs">${items.map((c) => pairCard(c)).join('')}</div>${d.known_total != null ? `<p class="mute" style="margin-top:8px;font-size:13px">Whole outfit: <b style="color:var(--ink)">${inr(d.known_total)}</b></p>` : '<p class="mute" style="margin-top:8px;font-size:12px">Total unknown: some pieces have no listed price.</p>'}` : '<p class="mute">No complementary pieces found yet.</p>');
  }).catch((e) => $('lookBox') && ($('lookBox').innerHTML = `<p class="mute">${esc(explain(e))}</p>`));
}
async function liveOffers() {
  const it = S.current; $('offerBox').innerHTML = spin('Searching live listings…');
  try {
    const s = await api('/products/search', { json: { query: [it.raw.brand, it.raw.title].filter(Boolean).join(' '), limit: 10 } });
    const cmp = await api('/prices/compare', { json: { target: it.raw, candidates: s.products } });
    const rows = (cmp.matches.length ? cmp.matches : s.products.map((p) => ({ product: p, label: 'similar_alternative' }))).filter((m) => m.label !== 'unrelated');
    const LAB = { exact_verified_match: 'Exact match', probable_match: 'Probable match', similar_alternative: 'Similar' };
    $('offerBox').innerHTML = `<h3>Live offers · ${esc(s.source)}</h3>${rows.length ? `<table>${rows.map((m) => `<tr><td>${esc(m.product.title)}<div class="mute" style="font-size:12px">${esc(m.product.merchant || '')} · ${LAB[m.label]}${m.missing_information?.length ? ' · missing: ' + esc(m.missing_information.join(', ')) : ''}</div></td><td>${m.product.price != null ? inr(m.product.price) : '–'}</td></tr>`).join('')}</table>` : '<p class="mute">No matching listings found.</p>'}
      ${cmp.lowest_observed ? `<p style="margin-top:8px;font-size:13px">Lowest verified: <b>${inr(cmp.lowest_observed.product.price)}</b> at ${esc(cmp.lowest_observed.product.merchant || 'merchant')}</p>` : ''}
      ${[...(s.warnings || []), ...(cmp.warnings || [])].map((w) => `<p class="mute" style="font-size:12px;margin-top:4px">${esc(w)}</p>`).join('')}`;
  } catch (e) { $('offerBox').innerHTML = `<p class="mute" style="margin-top:8px">${esc(explain(e))}</p>`; }
}

// ---------- Today: opt-in location or city search -> POST /stylist/daily ----------
const T = { loc: null, occasion: 'everyday' };
function renderToday() {
  if (!B.live) return OFF.renderToday();
  show('s-today');
  if (!T.loc) return todayPicker();
  dailyRun();
}
function todayPicker(note) {
  $('todayBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Today</span></div>
    <div class="kicker"><b>03</b>Dressed for today</div><h1>Where are you today?</h1>
    <p class="mute" style="margin-top:8px">We use your area only to read the weather. It’s never tracked or stored.${note ? ' ' + esc(note) : ''}</p>
    <div class="stack" style="margin-top:18px"><button onclick="useMyLocation()">📍 Use my location</button></div>
    <h3>Or choose a city</h3><div class="row"><input class="field" id="cityQ" placeholder="e.g. Gurugram" style="margin:0"><button onclick="citySearch()" style="padding:14px 16px">Search</button></div>
    <div id="cityRes" style="margin-top:10px"></div>`;
  $('cityQ').onkeydown = (e) => e.key === 'Enter' && citySearch();
}
function useMyLocation() {
  if (!navigator.geolocation) return todayPicker('Location isn’t available here.');
  navigator.geolocation.getCurrentPosition((p) => { T.loc = { latitude: +p.coords.latitude.toFixed(2), longitude: +p.coords.longitude.toFixed(2), label: 'Your area' }; dailyRun(); },
    () => todayPicker('Location was blocked, so pick a city instead.'), { enableHighAccuracy: false, timeout: 10000 });
}
async function citySearch() {
  const q = $('cityQ').value.trim(); if (q.length < 2) return toast('Type at least 2 letters'); $('cityRes').innerHTML = spin('Searching…');
  try { const r = await api('/locations/search?q=' + encodeURIComponent(q));
    $('cityRes').innerHTML = r.length ? r.map((c, i) => `<button class="ghost" style="width:100%;text-align:left;margin-bottom:8px" onclick="pickCity(${i})">${esc(c.name)}${c.region ? ', ' + esc(c.region) : ''} · ${esc(c.country || '')}</button>`).join('') : '<p class="mute">No cities found.</p>'; T.cities = r;
  } catch (e) { $('cityRes').innerHTML = `<p class="mute">${esc(explain(e))}</p>`; }
}
function pickCity(i) { const c = T.cities[i]; T.loc = { latitude: +c.latitude.toFixed(2), longitude: +c.longitude.toFixed(2), label: c.name }; dailyRun(); }
async function dailyRun() {
  $('todayBody').innerHTML = spin('Reading the sky…');
  try {
    const d = await api('/stylist/daily', { json: { location: T.loc, occasion: T.occasion } }), w = d.weather, cur = w.current || {};
    const items = d.outfit.map((e) => fromApi(e.product, { reasons: e.reasons }));
    $('todayBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">${new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short' })}</span></div>
      <div class="kicker"><b>03</b>Today · ${esc(T.loc.label || '')}</div>
      <div class="temp">${Math.round(cur.apparent_temperature)}<sup>°C</sup></div>
      <p style="margin:6px 0;font:italic 400 20px var(--serif)">Feels like · ${esc((w.tags || []).join(', '))}${w.precipitation_probability_percent != null ? ` · ${w.precipitation_probability_percent}% chance of precipitation` : ''}</p>
      <p style="margin-top:10px">${esc(d.greeting)}</p>
      <h3>Wear this</h3>${items.length ? `<div class="look">${items.map((c, i) => pairCard(c, `${priceText(c)}<br><span style="font-size:11px">${esc((d.outfit[i].reasons || [])[0] || '')}</span>`)).join('')}</div>` : '<p class="mute">No outfit matched today’s weather yet.</p>'}
      <h3>Styling notes</h3>${d.styling_notes.map((n) => `<p style="font-size:14px;margin:4px 0">· ${esc(n)}</p>`).join('')}
      ${[...(d.warnings || []), ...(d.occasion_applied === false ? ['Occasion doesn’t change the picks yet.'] : [])].map((n) => `<p class="mute" style="font-size:12px;margin-top:6px">${esc(n)}</p>`).join('')}
      <p class="mute" style="font-size:11px;margin-top:14px">Weather: <a href="${esc(w.source_url || 'https://open-meteo.com/')}" target="_blank" rel="noopener noreferrer" style="color:inherit">${esc(w.source || 'Open-Meteo')}</a> · read ${new Date(w.retrieved_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })} · forecast is guidance, not a guarantee</p>
      <div class="stack" style="margin-top:16px"><button class="ghost" onclick="T.loc=null;renderToday()">Change location</button></div>`;
  } catch (e) { $('todayBody').innerHTML = errBox(e, '<br><button onclick="renderToday()">Try again</button> <button class="ghost" onclick="T.loc=null;renderToday()">Change location</button>'); }
}

// ---------- Saved: GET /saved (likes are session-only: the API has no likes list) ----------
async function renderList(tab) {
  if (!B.live) return OFF.renderList(tab);
  if (typeof tab === 'string') S.listTab = tab; show('s-list');
  $('listBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Collection</span></div>${spin('Loading…')}`;
  let arr = [], err; if (S.listTab === 'saved') { try { arr = (await api('/saved')).products.map((p) => fromApi(p)); } catch (e) { err = e; } } else arr = S.liked;
  const grid = err ? errBox(err) : arr.length ? `<div class="list">${arr.map((c) => pairCard(c)).join('')}</div>` : `<div class="empty"><h2>${S.listTab === 'saved' ? 'Nothing saved yet' : 'No likes yet'}</h2><p class="mute">${S.listTab === 'saved' ? 'Swipe down on a piece to keep it for later.' : 'Swipe right on pieces you love.'}</p></div>`;
  $('listBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Collection</span></div>
    <div class="kicker"><b>${String(arr.length).padStart(2, '0')}</b>${S.listTab === 'saved' ? 'Saved' : 'Liked this session'}</div>
    <div class="seg"><button class="${S.listTab === 'saved' ? 'on' : ''}" onclick="renderList('saved')">Saved</button><button class="${S.listTab === 'liked' ? 'on' : ''}" onclick="renderList('liked')">Liked</button></div>${grid}`;
}
$('likedPill').onclick = () => renderList('liked'); $('savedPill').onclick = () => renderList('saved');

// ---------- Stylist chat: POST /agent/shop (not streamed; up to ~95 s) ----------
function renderChat() {
  show('s-chat');
  if (!B.live) { $('chatBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div></div><div class="empty" style="margin-top:20px"><h2>Backend offline</h2><p class="mute">The stylist assistant needs the Alluré backend.</p></div>`; return; }
  $('chatBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">Stylist</span></div>
    <div class="kicker"><b>04</b>Ask your stylist</div><h1>What are you shopping for?</h1>
    <p class="mute" style="margin-top:8px">It checks your style, your wardrobe and the catalogue with real tools. It can’t buy anything, and it won’t invent prices.</p>
    <textarea class="field" id="chatIn" rows="3" maxlength="2000" placeholder="e.g. A minimalist shirt for a rainy day"></textarea>
    <div class="chips" style="margin-top:8px">${['A minimalist shirt', 'Something for rain', 'Outfit from my wardrobe'].map((q) => `<button class="chip ghost" onclick="$('chatIn').value='${q}'">${q}</button>`).join('')}</div>
    <div class="stack" style="margin-top:12px"><button id="chatBtn" onclick="askAgent()">Ask</button></div><div id="chatOut" style="margin-top:16px"></div>`;
  if (S.lastAgent) showAgent(S.lastAgent);
}
async function askAgent() {
  const message = $('chatIn').value.trim(); if (message.length < 2) return toast('Ask something first');
  const ctl = new AbortController(), t0 = Date.now(), kill = setTimeout(() => ctl.abort(), 95000); $('chatBtn').disabled = true;
  const tick = setInterval(() => { const o = $('chatOut'); if (o) o.innerHTML = spin(`Your stylist is working… ${Math.round((Date.now() - t0) / 1000)}s (can take up to 90s)`); }, 1000);
  $('chatOut').innerHTML = spin('Your stylist is working…');
  try { S.lastAgent = await api('/agent/shop', { json: { message, ...(T.loc ? { location: T.loc } : {}) }, signal: ctl.signal }); showAgent(S.lastAgent); }
  catch (e) { $('chatOut') && ($('chatOut').innerHTML = errBox(e)); }
  clearTimeout(kill); clearInterval(tick); $('chatBtn') && ($('chatBtn').disabled = false);
}
function showAgent(d) {
  const label = { completed: 'Done', limited: 'Hit a limit: partial answer', timed_out: 'Timed out: partial answer', unavailable: 'Assistant unavailable' }[d.status] || d.status;
  const prods = (d.products || []).map((p) => fromApi(p));
  $('chatOut').innerHTML = `<p class="mute" style="font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700">${esc(label)}${d.duration_ms ? ' · ' + Math.round(d.duration_ms / 100) / 10 + 's' : ''}</p>
    <div class="box" style="margin-top:8px;white-space:pre-wrap">${esc(d.answer || 'No answer was produced.')}</div>
    ${prods.length ? `<h3>Pieces it found</h3><div class="list">${prods.map((c) => pairCard(c)).join('')}</div>` : ''}
    ${(d.warnings || []).map((w) => `<p class="mute" style="font-size:12px;margin-top:6px">${esc(w)}</p>`).join('')}
    ${(d.trace || []).length ? `<details style="margin-top:12px"><summary class="mute" style="cursor:pointer;font-size:12px">How it got this (${d.trace.length} steps)</summary>${d.trace.map((t) => `<p style="font-size:12px;margin:4px 0">· ${esc(t.tool || t.name || 'step')} → ${esc(t.status || '')}${t.duration_ms ? ' · ' + Math.round(t.duration_ms) + 'ms' : ''}</p>`).join('')}</details>` : ''}`;
}

// ---------- You: profile, colour guide, inspirations, wardrobe, hair, privacy ----------
const V = { aesthetics: ['minimalist', 'streetwear', 'smart_casual', 'casual', 'outdoor', 'classic', 'edgy', 'vintage', 'boho', 'sporty'],
  colors: ['black', 'white', 'beige', 'navy', 'olive', 'brown', 'grey', 'blue', 'green', 'red', 'burgundy', 'cream'], silhouettes: ['relaxed', 'oversized', 'straight', 'regular', 'slim'], garments: ['tops', 'bottoms', 'footwear', 'one-pieces', 'accessories'] };
const chipSet = (name, opts, sel) => `<div class="chips" data-set="${name}">${opts.map((o) => `<button class="chip ghost${sel.includes(o) ? ' on' : ''}" onclick="this.classList.toggle('on')">${o.replace('_', ' ')}</button>`).join('')}</div>`;
const readSet = (name) => [...document.querySelectorAll(`[data-set="${name}"] .chip.on`)].map((b) => b.textContent.trim().replace(' ', '_'));
const openSub = (html) => { $('subBody').innerHTML = html; show('s-sub'); };
async function renderProfile() {
  if (!B.live) return OFF.renderProfile();
  show('s-profile'); $('profileBody').innerHTML = spin('Loading…');
  try { const me = await api('/me'); B.prefs = me.preferences || {}; B.name = me.name; } catch (e) { $('profileBody').innerHTML = errBox(e); return; }
  const P = B.prefs, A = S.analysis?.style_profile, tags = (a) => (a || []).map((t) => `<span class="tag">${esc(t)}</span>`).join('') || '<span class="mute" style="font-size:13px">Not set</span>';
  $('profileBody').innerHTML = `<div class="top"><div class="logo">All<span>uré</span></div><span class="pill">You</span></div>
    <div class="kicker"><b>05</b>${esc(B.name)}</div>
    ${S.analysisError ? `<div class="box" style="margin-bottom:14px"><b>Photo analysis</b><p class="mute" style="font-size:13px;margin-top:4px">${esc(explain(S.analysisError))} You can set your style by hand below.</p></div>` : ''}
    ${A ? `<div class="box" style="margin-bottom:14px"><b>${S.analysis.device ? 'Colours in your photos' : 'From your outfits'}</b><p class="mute" style="font-size:12px;margin:4px 0 8px">${S.analysis.device ? 'Read on your device, nothing uploaded. Add your aesthetics below to refine.' : 'Clothing only. Photos aren’t stored. Edit anything below.'}</p>${tags([...A.aesthetics, ...A.preferred_colors].slice(0, 10))}</div>` : ''}
    <h3>Your style</h3><div class="box"><p class="mute" style="font-size:12px">Aesthetics</p>${tags(P.aesthetics)}<p class="mute" style="font-size:12px;margin-top:10px">Colours</p>${tags(P.preferred_colors)}<p class="mute" style="font-size:12px;margin-top:10px">Silhouettes</p>${tags(P.silhouettes)}
      <div class="stack" style="margin-top:14px"><button class="ghost" onclick="editPrefs()">Edit my style</button></div></div>
    <h3>Explore</h3><div class="stack">
      <button class="ghost" onclick="colourGuide()">Colour guide</button><button class="ghost" onclick="inspirationsUI()">Style inspirations</button>
      <button class="ghost" onclick="wardrobeUI()">My wardrobe</button><button class="ghost" onclick="hairUI()">Hair ideas</button>
      <button class="ghost" onclick="S.photos.length=0;renderSlots();prepUpload();show('s-upload')">${B.caps.vision ? 'Analyse my outfits' : 'Read colours from my photos'}</button></div>
    <h3>Coming next</h3><p class="mute" style="font-size:13px">Sale alerts and wallet auto-buy, a wardrobe that tags itself, and outfits that mix your wardrobe with live shopping. These aren’t built yet.</p>
    <h3>Privacy</h3><p class="mute" style="font-size:13px">Deleting removes your profile, swipes, wardrobe photos and try-on records. Outside AI providers keep their own records.</p>
    <div class="stack" style="margin-top:10px"><button class="ghost" id="delBtn" onclick="deleteMe()">Delete my data</button></div>`;
}
function editPrefs() {
  const P = B.prefs;
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>Your style</h2><p class="mute" style="font-size:13px">Saving replaces your explicit choices. What Alluré has learned from your swipes is kept.</p>
    <h3>Aesthetics</h3>${chipSet('aesthetics', V.aesthetics, P.aesthetics || [])}<h3>Colours you like</h3>${chipSet('colors', V.colors, P.preferred_colors || [])}
    <h3>Silhouettes</h3>${chipSet('silhouettes', V.silhouettes, P.silhouettes || [])}<h3>Garments</h3>${chipSet('garments', V.garments, P.garment_preferences || [])}
    <h3>Budget and size (optional)</h3><input class="field" id="pBudget" type="number" min="1" placeholder="Max price per item (₹)" value="${P.budget ?? ''}"><input class="field" id="pSize" maxlength="30" placeholder="Size (e.g. M)" value="${esc(P.size || '')}">
    <div class="stack" style="margin-top:16px"><button onclick="savePrefs()">Save</button></div>`);
}
async function savePrefs() {
  const budget = parseFloat($('pBudget').value);
  try { B.prefs = await api('/me/preferences', { method: 'PUT', json: { aesthetics: readSet('aesthetics'), preferred_colors: readSet('colors'), silhouettes: readSet('silhouettes'), garment_preferences: readSet('garments'), budget: budget > 0 ? budget : null, size: $('pSize').value.trim() || null, department: B.prefs.department ?? null } });
    S.deck = []; S.seen.clear(); toast('Saved. Your feed will reflect this.'); closeSheet(); renderProfile(); } catch (e) { toast(explain(e)); }
}
function colourGuide(r) {
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>Colour guide</h2><p class="mute" style="font-size:13px">A starting palette to explore, based on the undertone <i>you</i> choose. It’s styling guidance, not a measurement of your skin, and no colour is off-limits.</p>
    <h3>Your undertone</h3><div class="seg" style="grid-template-columns:repeat(4,1fr)" id="utSeg">${['warm', 'cool', 'neutral', 'unsure'].map((u, i) => `<button class="${u === 'unsure' ? 'on' : ''}" onclick="document.querySelectorAll('#utSeg button').forEach(b=>b.classList.remove('on'));this.classList.add('on')" style="padding:12px 4px;font-size:11px">${u}</button>`).join('')}</div>
    <p class="mute" style="font-size:12px">Not sure? Silver jewellery flattering usually means cool, gold means warm, both means neutral.</p>
    <h3>Feel</h3><div class="seg" style="grid-template-columns:repeat(3,1fr)" id="prSeg">${['muted', 'balanced', 'vibrant'].map((u) => `<button class="${u === 'balanced' ? 'on' : ''}" onclick="document.querySelectorAll('#prSeg button').forEach(b=>b.classList.remove('on'));this.classList.add('on')" style="padding:12px 4px;font-size:11px">${u}</button>`).join('')}</div>
    <label style="display:flex;gap:10px;font-size:13px;margin:10px 0"><input type="checkbox" id="palConsent"> I’d like colour suggestions based on the undertone I chose.</label>
    <div class="stack"><button onclick="runPalette()">Show my palette</button></div><div id="palOut" style="margin-top:16px"></div>`);
}
async function runPalette() {
  if (!$('palConsent').checked) return toast('Tick the box to opt in');
  const pick = (id) => document.querySelector(`#${id} button.on`).textContent.trim();
  try { const d = await api('/style/palette', { json: { undertone: pick('utSeg'), consent: true, preference: pick('prSeg') } });
    $('palOut').innerHTML = `<div class="swatches">${d.colors.map((c) => `<div><div class="sw" style="background:${esc(c.hex)};width:56px;height:56px"></div><div class="mute" style="font-size:11px;margin-top:4px">${esc(c.name)}</div></div>`).join('')}</div>
      <p style="font-size:14px;margin-top:12px">${esc(d.explanation)}</p>${(d.warnings || []).map((w) => `<p class="mute" style="font-size:12px;margin-top:4px">${esc(w)}</p>`).join('')}`;
  } catch (e) { $('palOut').innerHTML = `<p class="mute">${esc(explain(e))}</p>`; }
}
const INSPO = [['Billie Eilish', ['streetwear', 'edgy']], ['Zendaya', ['classic', 'smart_casual']], ['Harry Styles', ['vintage', 'boho']], ['Hailey Bieber', ['minimalist', 'casual']], ['Virat Kohli', ['sporty', 'classic']]];
async function inspirationsUI() {
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>Style inspirations</h2>${spin('Loading…')}`);
  const cur = (B.prefs.inspirations || []);
  const draw = () => openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>Style inspirations</h2><p class="mute" style="font-size:13px">Pick who you look up to and the styles you borrow from them. Alluré nudges your feed toward those styles. It doesn’t copy their outfits, and no one endorses this.</p>
    <h3>Following</h3>${cur.length ? cur.map((x, i) => `<div class="order row"><div class="grow"><b>${esc(x.name)}</b><div>${(x.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join('')}</div></div><button class="ghost" style="padding:8px 12px" onclick="inspoRemove(${i})">Remove</button></div>`).join('') : '<p class="mute" style="font-size:13px">No one yet.</p>'}
    <h3>Quick add</h3><div class="chips">${INSPO.map(([n, t], i) => `<button class="chip ghost" onclick="inspoAdd(${i})">${n}</button>`).join('')}</div>
    <h3>Someone else</h3><input class="field" id="inName" maxlength="80" placeholder="Name"><div style="margin-top:8px">${chipSet('inTags', V.aesthetics, [])}</div><div class="stack" style="margin-top:12px"><button onclick="inspoAddCustom()">Add</button></div>`);
  inspoState.cur = cur; inspoState.draw = draw; draw();
}
const inspoState = {};
async function inspoSave(list) { try { const d = await api('/me/inspirations', { method: 'PUT', json: { inspirations: list } }); B.prefs.inspirations = d.inspirations; inspoState.cur.splice(0, inspoState.cur.length, ...d.inspirations); S.deck = []; S.seen.clear(); inspoState.draw(); toast('Updated'); } catch (e) { toast(explain(e)); } }
const inspoAdd = (i) => inspoSave([...inspoState.cur.filter((x) => x.name !== INSPO[i][0]), { name: INSPO[i][0], tags: INSPO[i][1] }]);
function inspoAddCustom() { const n = $('inName').value.trim(); if (!n) return toast('Enter a name'); inspoSave([...inspoState.cur.filter((x) => x.name !== n), { name: n, tags: readSet('inTags') }]); }
const inspoRemove = (i) => inspoSave(inspoState.cur.filter((_, k) => k !== i));

async function wardrobeUI() {
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>My wardrobe</h2>${spin('Loading…')}`);
  let items = []; try { items = (await api('/wardrobe')).items; } catch (e) { return openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>My wardrobe</h2>${errBox(e)}`); }
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>My wardrobe</h2><p class="mute" style="font-size:13px">Pieces you own. Photos are private to your session. Add a name and colour yourself; Alluré doesn’t read the photo.</p>
    <div class="list" id="wGrid">${items.map((p) => `<div class="pair"><div class="wimg" data-w="${esc(p.id)}" style="height:110px;background:#ebe8e2"></div><div>${esc(p.title)}</div><div class="mute">${esc(p.category)} · ${esc((p.colors || [])[0] || '')}</div><button class="ghost" style="padding:6px 8px;margin-top:6px;font-size:10px" onclick="wardrobeDel('${esc(p.id)}')">Delete</button></div>`).join('') || '<div class="empty" style="grid-column:1/-1"><p class="mute">Nothing here yet.</p></div>'}</div>
    ${items.length >= 2 ? '<div class="stack" style="margin-top:12px"><button onclick="wardrobeOutfit()">Build an outfit from what I own</button></div><div id="wOut"></div>' : ''}
    <h3>Add a piece</h3><input type="file" id="wFile" accept="image/jpeg,image/png,image/webp" class="field"><input class="field" id="wTitle" maxlength="120" placeholder="Name (e.g. Grey hoodie)">
    <select class="field" id="wCat">${V.garments.map((g) => `<option>${g}</option>`).join('')}</select><input class="field" id="wColor" maxlength="40" placeholder="Main colour (e.g. grey)">
    <p class="mute" style="font-size:11px;margin-top:6px">Only the photo you pick is uploaded, to your private wardrobe.</p><div class="stack" style="margin-top:10px"><button onclick="wardrobeAdd()">Add to wardrobe</button></div>`);
  items.forEach(async (p) => { try { const b = await (await api(`/wardrobe/${p.id}/image`, { raw: true })).blob(); const el = document.querySelector(`[data-w="${p.id}"]`); if (el) el.style.cssText += `;background:url(${URL.createObjectURL(b)}) center/cover`; } catch {} });
}
async function wardrobeAdd() {
  const f = $('wFile').files[0], title = $('wTitle').value.trim(); if (!f || !title) return toast('Pick a photo and give it a name');
  const form = new FormData(); form.append('image', f); form.append('title', title); form.append('category', $('wCat').value); form.append('color', $('wColor').value.trim() || 'neutral');
  try { await api('/wardrobe', { form }); toast('Added'); wardrobeUI(); } catch (e) { toast(explain(e)); }
}
async function wardrobeDel(id) { try { await api('/wardrobe/' + id, { method: 'DELETE' }); wardrobeUI(); } catch (e) { toast(explain(e)); } }
async function wardrobeOutfit() {
  try { const d = await api('/wardrobe/outfits', { method: 'POST' });
    $('wOut').innerHTML = `<h3>An outfit from your wardrobe</h3>${d.items.length ? d.items.map((e) => `<p style="font-size:14px;margin:4px 0">· ${esc(e.product.title)} <span class="mute">(${esc(e.product.category)})</span></p>`).join('') : '<p class="mute">Add a top, bottom and shoes to build one.</p>'}<p class="mute" style="font-size:12px;margin-top:6px">${esc(d.notice)}</p>`;
  } catch (e) { $('wOut').innerHTML = `<p class="mute">${esc(explain(e))}</p>`; }
}
function hairUI() {
  openSub(`<button class="back" onclick="closeSheet()">← Close</button><h2>Hair ideas</h2><p class="mute" style="font-size:13px">Suggestions from the choices you enter. No photo is analysed.</p>
    <h3>Length</h3><div class="seg" style="grid-template-columns:repeat(3,1fr)" id="hlSeg">${['short', 'medium', 'long'].map((u) => `<button class="${u === 'medium' ? 'on' : ''}" onclick="document.querySelectorAll('#hlSeg button').forEach(b=>b.classList.remove('on'));this.classList.add('on')" style="padding:12px 4px;font-size:11px">${u}</button>`).join('')}</div>
    <h3>Texture</h3><select class="field" id="hTex">${['unsure', 'straight', 'wavy', 'curly', 'coily'].map((t) => `<option>${t}</option>`).join('')}</select>
    <h3>Goal</h3><input class="field" id="hGoal" maxlength="400" placeholder="Low-maintenance everyday styling"><div class="stack" style="margin-top:12px"><button onclick="hairRun()">Get ideas</button></div><div id="hOut" style="margin-top:14px"></div>`);
}
async function hairRun() {
  $('hOut').innerHTML = spin('Thinking…');
  try { const d = await api('/stylist/hair', { json: { length: document.querySelector('#hlSeg button.on').textContent.trim(), texture: $('hTex').value, goal: $('hGoal').value.trim() || 'low-maintenance everyday styling' } });
    $('hOut').innerHTML = `<div class="box" style="white-space:pre-wrap">${esc(d.advice)}</div><p class="mute" style="font-size:11px;margin-top:6px">Model-generated suggestions, not guaranteed results.</p>`;
  } catch (e) { $('hOut').innerHTML = errBox(e); }
}
function deleteMe() {
  $('delBtn').outerHTML = `<p style="font-size:13px;margin:8px 0">This permanently deletes your data. It can’t be undone.</p><div class="row"><button onclick="deleteConfirm()">Yes, delete everything</button><button class="ghost" onclick="renderProfile()">Cancel</button></div>`;
}
async function deleteConfirm() { try { await api('/me', { method: 'DELETE' }); } catch (e) { return toast(explain(e)); } sessionStorage.clear(); location.reload(); }

// ---------- Try-on: POST /tryon (202) then poll GET /tryon/{id} every 3 s ----------
const TF = { person: null, garment: null };
function openTryOn() {
  if (!B.live) return OFF.openTryOn();
  const it = S.current; show('s-tryon'); S.tryKey = null; clearTimeout(S.tryT);
  const cat = { tops: 'tops', bottoms: 'bottoms', 'one-pieces': 'one-pieces' }[it.raw?.category] || 'auto', auto = !!it.img;
  $('tryonBody').innerHTML = `<button class="back" onclick="openDetail('${it.id}')">← Back</button><h2>Try-on · ${it.name}</h2>
    ${B.caps.tryon ? '' : '<div class="box" style="margin-bottom:12px"><b>AI try-on isn’t enabled on this server yet.</b><p class="mute" style="font-size:13px;margin-top:4px">It needs a FASHN key. You can still use the manual preview below.</p></div>'}
    <p class="mute" style="font-size:12px;margin-bottom:6px">1 · A full-length photo of you</p><input type="file" id="tfPerson" accept="image/jpeg,image/png,image/webp" class="field" style="margin:0">
    <p class="mute" style="font-size:12px;margin:12px 0 6px">2 · The garment${auto ? ' (using this product’s photo)' : ': upload a photo of it'}</p>${auto ? `<div style="width:90px;height:110px;background:#ebe8e2 center/cover url(${it.img});border:1px solid var(--line)"></div>` : '<input type="file" id="tfGarment" accept="image/jpeg,image/png,image/webp" class="field" style="margin:0">'}
    <p class="mute" style="font-size:12px;margin:12px 0 6px">3 · Category</p><select class="field" id="tfCat" style="margin:0">${['auto', 'tops', 'bottoms', 'one-pieces'].map((c) => `<option ${c === cat ? 'selected' : ''}>${c}</option>`).join('')}</select>
    <label style="display:flex;gap:10px;font-size:13px;margin:14px 0"><input type="checkbox" id="tfConsent"> I have permission to use these photos. They’re sent to an AI provider for this one generation.</label>
    <div class="stack"><button id="tfGo" onclick="tryonSubmit()">Generate my try-on</button><button class="ghost" onclick="OFF.openTryOn()">Manual preview (not AI)</button></div><div id="tfOut" style="margin-top:16px"></div>`;
}
async function tryonSubmit() {
  const it = S.current, person = $('tfPerson').files[0]; let garment = $('tfGarment')?.files[0];
  if (!person) return toast('Add a photo of you'); if (!$('tfConsent').checked) return toast('Please confirm you have permission');
  $('tfGo').disabled = true; $('tfOut').innerHTML = spin('Sending…');
  try {
    if (!garment) { if (!it.img) { $('tfGo').disabled = false; return toast('Add a photo of the garment'); } garment = await (await fetch(it.img)).blob(); }
    const form = new FormData(); form.append('person_image', person); form.append('garment_image', garment, 'garment.jpg'); form.append('consent', 'true'); form.append('category', $('tfCat').value);
    S.tryKey = S.tryKey || rid(); // one key per distinct submission; reused if the same request is retried
    const d = await api('/tryon', { form, headers: { 'Idempotency-Key': S.tryKey } }); tryonPoll(d.job_id, Date.now());
  } catch (e) { $('tfGo').disabled = false; S.tryKey = null; $('tfOut').innerHTML = errBox(e); }
}
async function tryonPoll(id, t0) {
  try { const d = await api('/tryon/' + id), box = $('tfOut'); if (!box) return;
    if (d.status === 'completed' && d.generated_image_url) { $('tfGo').disabled = false; S.tryKey = null; const before = URL.createObjectURL($('tfPerson').files[0]);
      box.innerHTML = `<div class="tryon" id="cmp" style="aspect-ratio:3/4"><img src="${before}" style="position:absolute;inset:0"><img src="${esc(d.generated_image_url)}" id="cmpAfter" style="position:absolute;inset:0;clip-path:inset(0 0 0 50%)"></div>
        <input type="range" min="0" max="100" value="50" oninput="$('cmpAfter').style.clipPath='inset(0 0 0 '+this.value+'%)'" style="margin-top:10px"><p class="mute" style="font-size:12px">Drag to compare: you, and the AI preview.</p><p class="mute" style="font-size:12px;margin-top:6px">${esc(d.notice || 'AI appearance preview, not a guarantee of fit.')}</p>`; return; }
    if (d.status === 'failed') { $('tfGo').disabled = false; S.tryKey = null; box.innerHTML = `<div class="empty"><h2>That didn’t work</h2><p class="mute">${esc(d.error?.message || 'The try-on failed.')}</p></div>`; return; }
    box.innerHTML = spin(`${d.status === 'queued' ? 'In the queue' : 'Dressing you up'}… ${Math.round((Date.now() - t0) / 1000)}s`); S.tryT = setTimeout(() => tryonPoll(id, t0), 3000);
  } catch (e) { $('tfOut') && ($('tfOut').innerHTML = errBox(e)); $('tfGo') && ($('tfGo').disabled = false); }
}

// ---------- boot ----------
(async () => {
  try { const h = await fetch('/api/v1/health').then((r) => r.json()); B.live = !!h.success; B.caps = h.data?.providers || {}; } catch { B.live = false; }
  $('aiBadge').textContent = B.live ? 'Backend connected' : 'Offline demo';
  if (!B.live) { $('upNote').textContent = 'Offline demo: the Alluré backend isn’t connected, so everything runs on this device with sample data.'; return; }
  B.token = sessionStorage.getItem('allure_token');
  if (!B.token) return showWelcome();
  try { const me = await api('/me'); B.name = me.name; B.prefs = me.preferences || {}; S.ready = true; startDeck(); } catch { showWelcome(); }
})();
</script>
</body>
</html>

~~~

## Step 4: `seed_hm_catalogue.py`
Seeds the backend database with the H&M listing snapshot in `products/` (real INR prices and photos; colour from the photo; fits only from words in the title; merchant_url/gtin/size left null).
~~~python
"""Seed the team backend's catalogue with the H&M India listing snapshot in ./products.

Why: the backend ships 10 fictional fixtures with no prices or photos. The files in ./products are real H&M India
listings (names and INR prices observed on hm.com on 2026-11-18, photos from the listing). This inserts them as
non-demo products so the swipe deck, saved list, daily stylist and outfit completion work on real-looking data.

Honesty rules kept (see docs/BACKEND_BLUEPRINT.md section 10):
  * price/brand/merchant come from the listing; merchant_url, gtin, model_number and size stay null (never invented);
  * colours come from the photo (nearest named colour); fits come only from words in the listing title;
  * aesthetics/weather_tags are curated rules by garment type, so source is 'hm_in_listing_snapshot', not live data;
  * image_url is a path served by the Alluré web server (/products/<file>).

Usage (backend stopped or running; SQLite WAL is safe):
    python3 seed_hm_catalogue.py --db backend/runtime/stylematch.sqlite3
Needs Pillow (already in backend/requirements.txt). Re-running updates the same rows.
"""
import argparse, hashlib, json, re, sqlite3, urllib.parse
from pathlib import Path
from PIL import Image

NAMED = {  # backend colour vocabulary -> reference RGB
    'black': (24, 24, 27), 'white': (250, 250, 250), 'grey': (138, 141, 145), 'beige': (214, 196, 166), 'cream': (241, 233, 216),
    'brown': (109, 76, 53), 'olive': (107, 107, 58), 'green': (47, 93, 70), 'navy': (34, 48, 79), 'blue': (59, 91, 140),
    'red': (192, 57, 43), 'burgundy': (110, 31, 44), 'pink': (232, 180, 176), 'yellow': (216, 164, 44), 'orange': (196, 104, 63), 'purple': (150, 120, 190),
}
CATEGORY = {'tee': 'tops', 'shirt': 'tops', 'hoodie': 'tops', 'jacket': 'tops', 'kurta': 'tops', 'trousers': 'bottoms', 'skirt': 'bottoms',
            'dress': 'one-pieces', 'shoes': 'footwear', 'bag': 'accessories', 'watch': 'accessories', 'cap': 'accessories', 'sunglasses': 'accessories'}
AESTHETICS = {'tee': ['casual', 'minimalist'], 'shirt': ['smart_casual', 'classic'], 'hoodie': ['streetwear', 'casual'], 'jacket': ['outdoor', 'streetwear'],
              'trousers': ['casual', 'minimalist'], 'skirt': ['classic'], 'dress': ['classic', 'smart_casual'], 'shoes': ['casual'], 'bag': ['minimalist'],
              'cap': ['streetwear'], 'sunglasses': ['classic']}
WEATHER = {'tee': ['warm', 'hot'], 'shirt': ['mild', 'warm'], 'hoodie': ['cold', 'mild'], 'jacket': ['cold', 'mild'], 'trousers': ['mild', 'cold'], 'skirt': ['warm', 'mild'],
           'dress': ['warm', 'mild'], 'shoes': ['mild'], 'bag': ['mild'], 'cap': ['warm', 'mild'], 'sunglasses': ['warm', 'hot']}


def dominant(path):
    img = Image.open(path).convert('RGB').resize((40, 40))
    px = [img.getpixel((x, y)) for x in range(8, 32) for y in range(12, 32)]  # central torso band
    def keep(p):
        r, g, b = p; mx, mn = max(p), min(p); sat = 0 if mx == 0 else (mx - mn) / mx
        skin = r > g > b and 0.2 < sat < 0.6 and r > 95 and mx - mn > 15 and r - b > 25
        return not (skin or (sat < 0.12 and mx > 215))  # drop skin and light studio background
    px = [p for p in px if keep(p)] or px
    return tuple(sum(c) / len(px) for c in zip(*px))


def nearest(rgb):
    return min(NAMED, key=lambda n: sum((a - b) ** 2 for a, b in zip(NAMED[n], rgb)))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--db', required=True); ap.add_argument('--products', default=str(Path(__file__).parent / 'products'))
    a = ap.parse_args(); db = sqlite3.connect(a.db); n = 0
    db.execute('CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
    for f in sorted(Path(a.products).iterdir()):
        if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'): continue
        parts = [s.strip() for s in f.stem.split('__')]
        if len(parts) < 4 or parts[1] not in CATEGORY: print('skip', f.name); continue
        title, typ, price, brand = parts[0], parts[1], float(parts[2]), parts[3]
        low = title.lower()
        fits = [w for w in ('relaxed', 'loose', 'oversized', 'slim', 'regular', 'straight') if w in low]
        fits = ['relaxed' if w == 'loose' else w for w in fits]
        functional = ['water_resistant'] if 'water-repellent' in low or 'rain' in low else []
        weather = WEATHER[typ] + (['rain'] if functional else [])
        p = dict(id='hm-' + re.sub(r'[^a-z0-9]+', '-', low).strip('-') + '-' + hashlib.sha1(f.name.encode()).hexdigest()[:6],
                 title=title, brand=brand, category=CATEGORY[typ], colors=[nearest(dominant(f))], aesthetics=AESTHETICS[typ], fits=fits, weather_tags=weather,
                 functional_tags=functional, size=None, model_number=None, gtin=None, price=price, shipping_cost=None, currency='INR',
                 image_url='/products/' + urllib.parse.quote(f.name), merchant_url=None, merchant=brand, source='hm_in_listing_snapshot', is_demo=False,
                 observed_at='2026-11-18T00:00:00+00:00')
        db.execute('INSERT INTO products VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (p['id'], json.dumps(p))); n += 1
    db.commit(); print(f'seeded {n} products into {a.db}')


if __name__ == '__main__':
    main()

~~~

## Step 5: `backend_accept_1_to_5_images.patch`
~~~diff
--- a/backend/app/main.py	2026-11-18 17:16:16
+++ b/backend/app/main.py	2026-11-18 17:16:16
@@ -122,9 +122,9 @@
 
 @app.post('/api/v1/style/analyze')
 async def analyze(request:Request,user:User,images:Annotated[list[UploadFile],File()]):
-    if len(images)!=5: raise ProviderError('IMAGE_COUNT','Exactly five outfit references are required.',422)
+    if not 1<=len(images)<=5: raise ProviderError('IMAGE_COUNT','Provide between one and five outfit references.',422)
     raw=[await image_bytes(image) for image in images]
-    prompt=('Analyse only clothing in these five reference images. Do not infer age, ethnicity, health, body measurements, attractiveness, or other sensitive traits. '
+    prompt=('Analyse only clothing in these reference images (one to five). Do not infer age, ethnicity, health, body measurements, attractiveness, or other sensitive traits. '
         'Return one entry per image. Use lowercase aesthetic tags, common colour names, silhouettes and garment categories. '
         'Garment categories should be tops, bottoms, footwear, one-pieces, accessories. Material descriptions are visual guesses, explicitly qualified. '
         'Include ambiguity in uncertainty. These are references, not proof of ownership or personal identity.')
@@ -145,7 +145,7 @@
         for key,value in consolidated.items():
             if not p.get(key): p[key]=value
         conn.execute('UPDATE users SET preferences=? WHERE id=?',(json.dumps(p),user['id']))
-    return ok(request,{'style_profile':consolidated,'per_image':[x.model_dump() for x in result.images],'confidence':None,'source_image_count':5,'aggregation':'frequency across images; explicit saved preferences take precedence','images_stored':False})
+    return ok(request,{'style_profile':consolidated,'per_image':[x.model_dump() for x in result.images],'confidence':None,'source_image_count':len(images),'aggregation':'frequency across the supplied images; explicit saved preferences take precedence','images_stored':False})
 
 @app.get('/api/v1/recommendations')
 async def recommendations(request:Request,user:User,limit:int=Query(12,ge=1,le=50),include_seen:bool=False):
--- a/backend/app/schemas.py	2026-11-18 17:16:16
+++ b/backend/app/schemas.py	2026-11-18 17:16:16
@@ -80,7 +80,7 @@
     uncertainty: list[str]
 
 class VisionResult(Strict):
-    images: list[VisionImage] = Field(min_length=5,max_length=5)
+    images: list[VisionImage] = Field(min_length=1,max_length=5)
 
 class PaletteIn(Strict):
     undertone: Literal['warm','cool','neutral','unsure']
~~~

## Step 6: product photos
Each manifest line is `type|price|name|image-hash` (H&M India listings). Save each as `products/<name>__<type>__<price>__H&M.jpg` from `https://image.hm.com/assets/hm/<image-hash>.jpg?imwidth=500` using a normal browser User-Agent. File names must match exactly: the app reads type, price and brand from them. `type` is one of tee, shirt, hoodie, jacket, dress, kurta, trousers, skirt, shoes, bag, watch, cap, sunglasses.

~~~text
shirt|1799|Regular Fit Oxford Shirt A|31/73/31739c9891c6103512e90b89b7b427dec2bfe2c0
shirt|1999|Regular Fit Corduroy Shirt A|d5/f7/d5f777e17f1d5f3945011e4e819449e3053554d4
shirt|1499|Relaxed Motif Oxford Shirt|39/2a/392a8837be49a0752c1737358ffecb330f807f34
shirt|1799|Regular Fit Oxford Shirt B|3e/96/3e96fe2879706433dfb4fad614056d6a10a96caa
shirt|2299|Loose Fit Flannel Shirt|25/52/25525739e9a44926f6cde293ab870fceec8c274b
shirt|1799|Regular Fit Oxford Shirt C|8d/9e/8d9e24829696c5ee5b73cd330d9a6f168c1abf06
shirt|1999|Regular Fit Corduroy Shirt B|4a/ab/4aabcd55fa73aed631a45ee74778c818e70d78ec
hoodie|999|Loose Fit Sweatshirt A|b0/7e/b07e11b69eada9f82e8312e3803ec017149cc02c
hoodie|1499|Loose Fit Hoodie A|87/a9/87a948945e8541c19e45c87372ac289d506fcf84
hoodie|999|Loose Fit Sweatshirt B|70/ef/70ef9a42c196b9cc587986bb18c36880abd374fe
hoodie|1499|Loose Fit Hoodie B|87/d2/87d2343b95dc263aea489f1e0ebe0fc64566181a
hoodie|1499|Zip Hoodie A|f4/1a/f41a43aca655f56ceffcd9ad3d0cfecc9188adf6
hoodie|1499|Zip Hoodie B|a9/45/a9458b1360141c8db0fed49d77d0f863a7fbc0a9
hoodie|999|Loose Fit Sweatshirt C|1d/34/1d348ad5a1887410dc77c6bef22ab692f364fd75
jacket|2999|Lightweight Puffer Jacket|9d/f3/9df3a710210e7d8bf93ecde3e8bf6fc2a32ee08d
jacket|2999|Nylon Windbreaker|4d/d3/4dd3c9514ae37488f58eb0d48c57cca9022b9b25
jacket|2599|Lightweight Bomber Jacket|0f/74/0f74112fa852da71dc69533b192b38024ecb4ff9
jacket|6999|Aviator Jacket|02/28/0228dd4ca099486b69f0bba1a3021df0c3986f8d
jacket|2999|Stand Collar Puffer Jacket|9f/94/9f947bb41df56cd7ad2a4652f63399e18744eded
jacket|4999|Coated Jacket|0e/c4/0ec493b2a4a31125b8764405123e8d0a555257aa
trousers|1999|Loose Sweatpants A|9d/cb/9dcb3b8d7613acc483d147045d7bd3f049704bbf
trousers|1999|Loose Sweatpants B|d0/a8/d0a8cc841f0a95e8477f659a403c343557ba0ff1
trousers|1499|Relaxed Sweatpants A|f8/ff/f8ffe97438e836db782241a13b40ad41dd00c531
trousers|1999|Relaxed Interlock Sweatpants|fd/dc/fddc0c2d0401115b0893806ba2d6d453d64fbf39
trousers|1499|Relaxed Sweatpants B|2c/57/2c57deb9b93d0e88bf527f9f9a34378924fbbcf8
trousers|1999|Loose Straight Jeans A|ab/97/ab9736464110b25f1b90ca6028a6cae3272b9e33
trousers|2499|Loose Jeans A|ee/3e/ee3e327724f842844c37c205426bd26c3a492f9c
trousers|2499|Loose Jeans B|df/39/df3974d46c35910e0ec577707a4f6a2e4314460d
trousers|1999|Relaxed Jeans|0d/4f/0d4fc3272697a2b8f364181c76e1b8e313d20368
trousers|2499|Regular Jeans|8c/a3/8ca33ace134a38aa1b964263b4ab5ad3dc67f0e0
dress|999|Draped Halterneck Dress|d0/bd/d0bd507b15fc08ae41cf6107cb9e8b79a3ee29da
dress|2999|Brocade Keyhole Dress|8f/fc/8ffc4bf7a8a1e625fde6131d0aca8f9711d16b40
dress|2799|Sequined Dress A|e2/5e/e25ee29fa955b28d12164c9ee3d231c9ef992a32
dress|2799|Balloon Sleeve Satin Dress|44/6c/446ccc25732a238e4854583d48e8b6bc80de9b0f
dress|2299|Bow Collar A-line Dress|a3/c8/a3c892edff25577f94e3ee42eb32936c397c85a9
dress|1499|Metal Detail Draped Dress|05/8e/058ed40a66d7e0ffaeb38ca3bd0d069e8dbfc680
skirt|1499|Satin Maxi Skirt|9f/27/9f274219a7596bcc4f21e1903db962248e912078
skirt|1499|Coated Skirt|00/cd/00cdc4de8fd16368e085043515dbe9a9dc0b58db
skirt|1499|Mini Skirt|98/a0/98a0511d5befde33f54681c7a276a31e286cb3fd
skirt|1999|Midi Skirt|84/0e/840ed34811d3565bb0c97379154fc1c75d22101d
tee|999|Lace Trim Rib Top A|ee/73/ee73de25e9c1798e668b374fd330f270f7eb612e
tee|999|Lace Trim Rib Top B|27/de/27de8dfa15a3adddfe53dbe190233c3b4682352c
tee|999|Long Sleeve Cotton Top A|66/13/6613b28541bd22a7fd08bd53e540e25154114161
tee|999|Long Sleeve Cotton Top B|f8/04/f804beec1607a4db2f40f3de1605f7e14f99acd2
tee|799|Long Sleeve Cotton Top C|68/57/68574d3f01b389ea367e08c7710ff2485cd14a72
shoes|2999|Chelsea Boots A|ea/24/ea241f65f52c616ad4e0f3a757a4976d1f5ebb7a
shoes|2999|Chelsea Boots B|7a/5d/7a5daa89197f672226b9340380c0ae997adfe057
shoes|5499|Ankle Boots|f7/c2/f7c2989f5752df269a530747c83968fd09ce5ec5
shoes|2999|Slide Sandals|e9/f7/e9f7fe5daeb0df5fb16d21fa7175294588890a1d
bag|1499|Nylon Crossbody Bag|00/c1/00c1ee49dc676db23f0854655b02bd7c420c36f2
bag|2299|Tote Bag|77/74/77741b589ef99ff42d7dc6d98e3dd6568c436bb3
bag|1499|Coated Pouch|b2/f3/b2f39ff9311f5a8272f3e59df4fe21444ba71917
bag|1999|Crossbody Bag|dd/a8/dda8704e8d786e3fc8209e387a7e30931008fe38
cap|999|Motif Cotton Twill Cap|55/37/553794c4352200b78ed4598b1084469331efdb7f
cap|999|Cotton Twill Cap|19/2d/192d108ef8a8f9368a4a712b411c09804a5a92fd
sunglasses|999|Aviator Sunglasses|fd/bc/fdbc6939d5fa56f4e329657244ba659a221fe6b9
sunglasses|1499|Premium Sunglasses A|bb/bd/bbbd9ed41c4945c32745015e6535628d7ce1fb62
sunglasses|999|Rectangular Sunglasses|ce/c7/cec706172719a3c81c577fe41c1c9c205d962ca0
~~~

~~~bash
mkdir -p products && while IFS='|' read -r type price name hash; do
  curl -s -m 25 -A "Mozilla/5.0" -o "products/${name}__${type}__${price}__H&M.jpg" "https://image.hm.com/assets/hm/${hash}.jpg?imwidth=500"
done < manifest.txt
~~~

## Step 7: run and verify
1. Start the backend (port 8766). Optionally `python3 seed_hm_catalogue.py --db <backend>/runtime/stylematch.sqlite3` for real products.
2. `node server.js`, open http://localhost:3000 (website) and http://localhost:3000/app (app).
3. App: enter a name → add 1–5 photos (or "Set my style by hand") → swipe → tap a card (price, outfit, try-on) → Today (city search) → Stylist → You (colour guide, inspirations, wardrobe).
4. Stop the backend and reload `/app`: it must show "Offline demo" and still work.
5. Report anything that doesn't work. Do not change the design.

## Honest limits
Offline-demo prices are simulated. AI photo analysis, try-on, live offers and the stylist chat only work when the backend has the matching provider configured. Wallet auto-buy, sale alerts and wardrobe auto-tagging are roadmap, not built.
