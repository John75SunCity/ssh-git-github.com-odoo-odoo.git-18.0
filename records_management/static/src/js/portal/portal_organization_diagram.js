/**
 * Portal Organization Diagram Interaction Logic
 * Consumes JSON from #diagram-data and renders via vis-network (if optional bundle loaded) or
 * provides graceful fallback.
 */
odoo.define('records_management.portal_organization_diagram', function(require) {
    'use strict';

    // Frontend-compatible implementation
    const publicWidget = { Widget: { extend: function(obj) { return obj; } } };

    const OrgDiagramPortal = publicWidget.Widget.extend({
        selector: '.o_portal_organization_diagram',
        events: {
            'click #refresh-diagram': '_onRefresh',
            'click #export-diagram': '_onExport',
            'click #search-button': '_onSearch',
            'keyup #search-query': '_onSearchKey',
            'change #layout-select': '_onLayoutChanged',
        },
        start() {
            this._parseData();
            this._renderDiagram();
            this._updateStats();
            return this._super.apply(this, arguments);
        },
        _parseData() {
            try {
                const jsonEl = this.el.querySelector('#diagram-data');
                if (jsonEl) {
                    this.diagramData = JSON.parse(jsonEl.textContent.trim());
                } else {
                    this.diagramData = { nodes: [], edges: [], stats: {}, config: {} };
                }
            } catch (e) {
                console.error('[OrgDiagramPortal] Failed to parse diagram JSON', e);
                this.diagramData = { nodes: [], edges: [], stats: {}, config: {} };
            }
        },
        _renderDiagram() {
            const container = this.el.querySelector('#organization-diagram-container');
            if (!container) { return; }
            // If vis is present (optional bundle), render network
            if (window.vis && this.diagramData.nodes && this.diagramData.edges) {
                const options = this._buildVisOptions();
                try {
                    this.network = new vis.Network(container, {
                        nodes: new vis.DataSet(this.diagramData.nodes),
                        edges: new vis.DataSet(this.diagramData.edges),
                    }, options);
                    container.querySelector('.loading-overlay')?.remove();
                } catch (e) {
                    console.error('[OrgDiagramPortal] vis rendering failed', e);
                }
            } else {
                // Fallback
                container.innerHTML = '<div class="p-5 text-center text-muted">Diagram library not loaded. Please enable visualization bundle.</div>';
            }
        },
        _buildVisOptions() {
            const layoutType = (this.diagramData.config && this.diagramData.config.layout_type) || 'hierarchical';
            const hierarchical = layoutType === 'hierarchical';
            return {
                layout: hierarchical ? { hierarchical: { direction: 'UD', sortMethod: 'hubsize' } } : {},
                interaction: { hover: true },
                physics: hierarchical ? false : { stabilization: true },
                nodes: { shape: 'dot', size: 18, font: { size: 12 } },
                edges: { arrows: { to: { enabled: false } }, smooth: { type: 'dynamic' } },
            };
        },
        _updateStats() {
            const stats = this.diagramData.stats || {};
            const mapping = {
                companies: '#companies-count',
                departments: '#departments-count',
                users: '#users-count',
                connections: '#connections-count',
            };
            for (const key in mapping) {
                const el = this.el.querySelector(mapping[key]);
                if (el && el.textContent !== undefined) { 
                    el.textContent = stats[key] != null ? stats[key] : '-'; 
                }
            }
        },
        _onRefresh(ev) {
            ev.preventDefault();
            this._parseData();
            this._renderDiagram();
            this._updateStats();
        },
        _onExport(ev) {
            ev.preventDefault();
            const blob = new Blob([JSON.stringify(this.diagramData, null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'organization_diagram.json';
            a.click();
        },
        _onSearch(ev) {
            ev.preventDefault();
            this._applySearch();
        },
        _onSearchKey(ev) {
            if (ev.key === 'Enter') {
                this._applySearch();
            }
        },
        _onLayoutChanged() {
            if (!this.network) { return; }
            this.diagramData.config = this.diagramData.config || {};
            this.diagramData.config.layout_type = this.el.querySelector('#layout-select')?.value;
            this._renderDiagram();
        },
        _applySearch() {
            if (!this.network) { return; }
            const query = (this.el.querySelector('#search-query')?.value || '').toLowerCase();
            if (!query) { return; }
            const matches = this.diagramData.nodes.filter(n => (n.label || '').toLowerCase().includes(query));
            if (matches.length) {
                const ids = matches.map(m => m.id);
                this.network.focus(ids[0], { scale: 1.2, animation: true });
                this.network.selectNodes(ids, false);
            }
        },
    });

    publicWidget.registry.OrgDiagramPortal = OrgDiagramPortal;
    return OrgDiagramPortal;
});
