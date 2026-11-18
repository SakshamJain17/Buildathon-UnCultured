// Renders video/film.html to an MP4/WebM by playing it in headless Chrome and recording the canvas.
// Usage: node video/render.js        Output: video/allure-film.mp4 (or .webm)
const http = require('http'), fs = require('fs'), path = require('path'), { spawn } = require('child_process');
const ROOT = path.join(__dirname, '..'), PORT = 3077;
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
let chrome;
const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  if (req.method === 'POST' && url === '/out') {
    const type = new URL(req.url, 'http://x').searchParams.get('type') || '';
    const out = path.join(__dirname, 'allure-film.' + (type.includes('mp4') ? 'mp4' : 'webm'));
    const ws = fs.createWriteStream(out); req.pipe(ws);
    ws.on('finish', () => { res.end('ok'); console.log('saved', out, (fs.statSync(out).size / 1e6).toFixed(1) + ' MB'); chrome && chrome.kill(); server.close(); setTimeout(() => process.exit(0), 300); });
    return;
  }
  if (url === '/film') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); return fs.createReadStream(path.join(__dirname, 'film.html')).pipe(res); }
  if (url === '/api/stills') { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify(fs.readdirSync(path.join(__dirname, 'stills')).filter((f) => f.endsWith('.jpg')))); }
  if (url.startsWith('/stills/')) { const f = path.join(__dirname, 'stills', path.basename(url)); if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'image/jpeg' }); return fs.createReadStream(f).pipe(res); } }
  if (url === '/api/products') { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end(JSON.stringify(fs.readdirSync(path.join(ROOT, 'products')))); }
  if (url.startsWith('/products/')) { const f = path.join(ROOT, 'products', path.basename(decodeURIComponent(url.slice(10)))); if (fs.existsSync(f)) { res.writeHead(200, { 'Content-Type': 'image/jpeg' }); return fs.createReadStream(f).pipe(res); } }
  res.writeHead(404); res.end();
});
server.listen(PORT, () => {
  if (process.argv.includes('--serve')) return console.log(`preview: http://localhost:${PORT}/film  (Space to play, ?t=42 for a still)`);
  const profile = fs.mkdtempSync(path.join(require('os').tmpdir(), 'allure-render-'));
  chrome = spawn(CHROME, ['--headless=new', '--window-size=1920,1080', '--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows', '--user-data-dir=' + profile, `http://localhost:${PORT}/film?render=1`], { stdio: 'ignore' });
  console.log('recording 72 s in headless Chrome…');
});
