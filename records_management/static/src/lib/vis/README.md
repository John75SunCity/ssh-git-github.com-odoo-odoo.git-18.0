# Local Visualization Library (vis-network)

This directory hosts a locally served copy (or placeholder) of the visualization library used by
portal/system diagrams. For production, you should place an UNMINIFIED or multi-line formatted build
of `vis-network` here to avoid repository validation issues (oversized single-line minified files).

## Recommended Version

Pinned (tested) version: 9.1.6

## Files to Add (replace placeholders)

- `vis-network.js` (preferred unminified build)
- `vis-network.css`

Optional (if you need minified builds for performance, keep them multi-line formatted):
- `vis-network.min.js`
- `vis-network.min.css`

## Policy

1. Keep a readable (non single giant line) source to satisfy code scanners.
2. Commit a matching LICENSE excerpt if upstream license requires redistribution notice.
3. The dynamic loader will attempt local files first, then fallback to CDN if local missing.
4. Update version references in `visualization_dynamic_loader.js` when upgrading.

## Fallback Behavior

If the local assets are absent, the loader logs a warning and switches to CDN fetch, preserving functionality.

## Upgrading

1. Download new version: https://unpkg.com/browse/vis-network@
2. Replace JS/CSS here (remove old versions).
3. Update loader constants to reflect version.
4. Test diagrams in portal/system flowchart views.
