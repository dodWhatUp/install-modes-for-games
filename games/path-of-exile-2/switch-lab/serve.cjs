'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, 'POE2-Switch-Lab.html'));
const server = http.createServer((request, response) => {
  if (request.url !== '/' || request.method !== 'GET') { response.writeHead(404); response.end(); return; }
  response.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'});
  response.end(html);
});
server.listen(0, '127.0.0.1', () => console.log('Lab: http://127.0.0.1:' + server.address().port + '/'));
