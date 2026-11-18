// Zero-dependency frontend server. AI and identity stay in the existing FastAPI backend.
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const root=__dirname;
const backend=new URL(process.env.ALLURE_BACKEND || 'http://127.0.0.1:8766');
const files={'/':'index.html','/app':'app.html','/story':'story.html','/film':'film.html','/brand.js':'brand.js','/brand.css':'brand.css','/brand/allure-logo.png':'brand/allure-logo.png','/manifest.webmanifest':'manifest.webmanifest','/styles.css':'styles.css','/app.js':'app.js','/landing.js':'landing.js'};
http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  if(url.pathname.startsWith('/api/v1/') || url.pathname.startsWith('/assets/')) {
    const proxy=http.request({hostname:backend.hostname,port:backend.port||80,path:req.url,method:req.method,headers:{...req.headers,host:backend.host}},up=>{res.writeHead(up.statusCode,up.headers);up.pipe(res)});
    proxy.on('error',()=>{if(!res.headersSent)res.writeHead(503,{'Content-Type':'application/json'});res.end(JSON.stringify({success:false,error:{code:'BACKEND_OFFLINE',message:'Start the ALLURÉ backend on port 8766.'}}))});req.pipe(proxy);return;
  }
  const file=files[url.pathname];
  if(!file){res.writeHead(404);res.end('Not found');return;}
  const contentType=file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.css')?'text/css':file.endsWith('.png')?'image/png':file.endsWith('.webmanifest')?'application/manifest+json':'text/javascript';
  fs.readFile(path.join(root,file),(error,data)=>{if(error){res.writeHead(500);res.end('File unavailable');return;}res.writeHead(200,{'Content-Type':contentType,'X-Content-Type-Options':'nosniff'});res.end(data)});
}).listen(process.env.PORT||3000,'127.0.0.1',()=>console.log('ALLURÉ website: http://localhost:'+(process.env.PORT||3000)));
