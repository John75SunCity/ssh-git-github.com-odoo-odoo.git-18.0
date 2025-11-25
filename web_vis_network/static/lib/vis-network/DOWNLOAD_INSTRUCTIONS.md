# Download vis.js Network Library

To complete this module installation, download the vis.js network library:

## Download Instructions

1. Go to: https://github.com/visjs/vis-network/releases
2. Download the latest release (e.g., `vis-network-9.1.9.zip`)
3. Extract the archive
4. Copy these files to this directory:
   - `vis-network.min.js` → `web_vis_network/static/lib/vis-network/vis-network.min.js`
   - `vis-network.min.css` → `web_vis_network/static/lib/vis-network/vis-network.min.css`

## Alternative: CDN Download

You can also download directly from CDN:

```bash
cd web_vis_network/static/lib/vis-network/

# Download JavaScript
curl -o vis-network.min.js https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js

# Download CSS
curl -o vis-network.min.css https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/dist/vis-network.min.css
```

## Verify Installation

After downloading, you should have:
- `vis-network.min.js` (approx. 500KB)
- `vis-network.min.css` (approx. 10KB)

Then restart Odoo and update the module:

```bash
./odoo-bin -u web_vis_network -d your_database
```

## Current Status

⚠️ **Library files not yet downloaded** - Module will not function until files are added.
