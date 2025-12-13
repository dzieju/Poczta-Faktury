#!/usr/bin/env node
//
// tools/invoice-preview/server.js
//
// Simple Express service that lists invoice files from a directory and serves them.
// Config:
//  - PORT (default 3000)
//  - INVOICES_DIR (default: path.join(__dirname, '..', '..', 'invoices'))
//
const express = require('express');
const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const mime = require('mime-types');

const app = express();

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const DEFAULT_INVOICES_DIR = path.join(__dirname, '..', '..', 'invoices');
const INVOICES_DIR = process.env.INVOICES_DIR ? path.resolve(process.env.INVOICES_DIR) : DEFAULT_INVOICES_DIR;

// Allowed extensions to show in the preview UI
const ALLOWED_EXT = new Set(['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.txt']);

// Utility function for filename sanitization (reserved for future use)
function sanitizeFilename(name) {
  // remove any path segments
  return path.basename(name);
}

async function listInvoices() {
  try {
    await fs.access(INVOICES_DIR);
  } catch (e) {
    return { error: `Invoices directory not found: ${INVOICES_DIR}` };
  }

  const entries = await fs.readdir(INVOICES_DIR, { withFileTypes: true });
  const files = [];
  for (const e of entries) {
    if (!e.isFile()) continue;
    const name = e.name;
    const ext = path.extname(name).toLowerCase();
    if (!ALLOWED_EXT.has(ext)) continue;
    try {
      const stat = await fs.stat(path.join(INVOICES_DIR, name));
      files.push({
        name,
        size: stat.size,
        mtime: stat.mtime.toISOString(),
        url: `/invoices/files/${encodeURIComponent(name)}`
      });
    } catch (err) {
      // skip files we can't stat
    }
  }
  // sort by mtime desc
  files.sort((a, b) => new Date(b.mtime) - new Date(a.mtime));
  return { files };
}

// Serve a tiny frontend
app.use('/invoices/static', express.static(path.join(__dirname, 'public')));

// Static serve the invoice files
// Security: Express.static provides built-in path traversal protection
// Additional protections: dotfiles denied, no directory listing
if (fsSync.existsSync(INVOICES_DIR)) {
  app.use('/invoices/files', express.static(INVOICES_DIR, {
    index: false,
    dotfiles: 'deny',
    // set Content-Type correctly via mime package
    setHeaders: (res, filePath) => {
      const type = mime.lookup(filePath) || 'application/octet-stream';
      res.setHeader('Content-Type', type);
    }
  }));
} else {
  // Directory not present; route will return 404 for file requests
  console.warn(`Invoice directory does not exist: ${INVOICES_DIR}`);
}

// API: list invoices
app.get('/api/invoices', async (req, res) => {
  const data = await listInvoices();
  if (data.error) return res.status(500).json({ error: data.error });
  res.json(data.files);
});

// Optional simple health route
app.get('/healthz', (req, res) => res.send('ok'));

// Fallback: redirect to small UI
app.get('/', (req, res) => {
  res.redirect('/invoices/static/');
});

app.listen(PORT, () => {
  console.log(`Invoice preview service running on http://0.0.0.0:${PORT}/`);
  console.log(`Serving invoices from: ${INVOICES_DIR}`);
});
