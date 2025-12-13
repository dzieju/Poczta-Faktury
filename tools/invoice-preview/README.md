# Invoice Preview Microservice

Simple Express-based microservice for listing and previewing invoice files (PDF, images, text).

## Features

- 📋 List all invoice files from a configured directory
- 👁️ Preview invoices in browser (PDF, PNG, JPG, GIF, TXT)
- 🚀 Simple REST API
- 🎨 Clean, responsive UI
- 🔒 Secure file serving with path traversal protection

## Installation

```bash
cd tools/invoice-preview
npm install
```

## Usage

### Start the service

```bash
npm start
```

The service will run on `http://localhost:3000` by default.

### Configuration

Configure via environment variables:

- `PORT` - Server port (default: 3000)
- `INVOICES_DIR` - Path to invoices directory (default: `../../invoices` relative to this directory)

Example with custom configuration:

```bash
PORT=8080 INVOICES_DIR=/path/to/invoices npm start
```

### Development mode

```bash
npm run dev
```

## API Endpoints

### `GET /api/invoices`

Returns a JSON array of invoice files with metadata:

```json
[
  {
    "name": "invoice_001.pdf",
    "size": 45632,
    "mtime": "2025-12-13T10:30:00.000Z",
    "url": "/invoices/files/invoice_001.pdf"
  }
]
```

### `GET /invoices/files/:filename`

Serves the invoice file with appropriate Content-Type header.

### `GET /invoices/static/`

Serves the web UI for browsing and previewing invoices.

### `GET /healthz`

Health check endpoint. Returns `ok`.

## Supported File Types

- PDF (`.pdf`)
- Images: PNG (`.png`), JPEG (`.jpg`, `.jpeg`), GIF (`.gif`)
- Text files (`.txt`)

## Architecture

- **Backend**: Express.js web server
- **Frontend**: Vanilla JavaScript (no frameworks)
- **Security**: 
  - Path traversal protection via `path.basename()`
  - Dotfiles denied
  - Allowlist of file extensions
  - Static file serving with Express built-in security

## Integration with Poczta-Faktury

This microservice is designed to work alongside the main Poczta-Faktury application:

1. The main application saves invoices to the `invoices/` directory
2. This microservice reads and displays those files
3. No database required - files are read directly from the filesystem

## License

Part of the Poczta-Faktury project.
