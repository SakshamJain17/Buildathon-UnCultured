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
