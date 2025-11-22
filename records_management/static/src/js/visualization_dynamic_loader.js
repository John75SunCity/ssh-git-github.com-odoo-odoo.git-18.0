/**
 * visualization_dynamic_loader.js
 * Lightweight dynamic loader that fetches visualization libraries (vis-network)
 * from a CDN only when a diagram container is present. Avoids committing large
 * minified vendor bundles into the repository while preserving functionality.
 */
odoo.define('records_management.visualization_dynamic_loader', ['web.public.widget'], function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    // Local (served by Odoo) preferred paths
    const LOCAL_JS = '/records_management/static/src/lib/vis/vis-network.js';
    const LOCAL_CSS = '/records_management/static/src/lib/vis/vis-network.css';

    // CDN fallback (only if local missing / placeholder insufficient)
    const CDN_VERSION = '9.1.6';
    const CDN_JS = `https://unpkg.com/vis-network@${CDN_VERSION}/dist/vis-network.min.js`;
    const CDN_CSS = `https://unpkg.com/vis-network@${CDN_VERSION}/dist/vis-network.min.css`;

    function injectTag(tag, attrs, marker) {
        if (document.querySelector(`[data-vis-network="${marker}"]`)) { return Promise.resolve(); }
        return new Promise((resolve, reject) => {
            const el = document.createElement(tag);
            Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k, v));
            el.setAttribute('data-vis-network', marker);
            if (tag === 'script') {
                el.onload = () => resolve();
                el.onerror = () => reject(new Error(`Failed to load ${attrs.src || 'script'}`));
            }
            if (tag === 'link') {
                el.onload = () => resolve();
                el.onerror = () => reject(new Error(`Failed to load ${attrs.href || 'stylesheet'}`));
            }
            document.head.appendChild(el);
            if (tag === 'link') { resolve(); } // styles load passively
        });
    }

    async function ensureAssets() {
        // Fast path: already loaded
        if (window.vis && window.vis.Network) { return; }

        // 1. Try local assets
        try {
            await injectTag('link', { rel: 'stylesheet', href: LOCAL_CSS }, 'local-css');
            await injectTag('script', { src: LOCAL_JS, async: 'true' }, 'local-js');
            if (window.vis && window.vis.Network) { return; }
            console.warn('[VisualizationDynamicLoader] Local vis-network placeholder detected or incomplete; falling back to CDN.');
        } catch (e) {
            console.warn('[VisualizationDynamicLoader] Local vis-network load failed, fallback to CDN.', e);
        }

        // 2. CDN fallback
        try {
            await injectTag('link', { rel: 'stylesheet', href: CDN_CSS }, 'cdn-css');
            await injectTag('script', { src: CDN_JS, async: 'true' }, 'cdn-js');
        } catch (e) {
            console.warn('[VisualizationDynamicLoader] CDN load failed; diagrams will not render.', e);
        }
    }

    publicWidget.registry.VisualizationDynamicLoader = publicWidget.Widget.extend({
        selector: '.o_portal_organization_diagram, .o_system_flowchart_view',
        start: function () {
            if (this.el) {
                ensureAssets();
            }
            return this._super.apply(this, arguments);
        },
    });

    return publicWidget.registry.VisualizationDynamicLoader;
});
