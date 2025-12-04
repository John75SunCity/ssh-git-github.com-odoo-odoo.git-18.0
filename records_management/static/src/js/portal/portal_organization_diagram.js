/**
 * Portal Organization Diagram - Frontend Widget (Vanilla JavaScript - Odoo 18 Compatible)
 * 
 * PURPOSE: Customer-facing portal organization chart visualization
 * USE CASE: /my/organization route - shows company hierarchy to portal users
 * 
 * ARCHITECTURE:
 * - Consumes JSON from #diagram-data element (server-rendered in template)
 * - Renders via vis-network library (bundled in web_vis_network module)
 * - Falls back to CDN if web_vis_network not available
 * - Graceful fallback when vis.js not loaded
 * 
 * DATA FLOW:
 * 1. Python controller renders QWeb template with JSON in <script id="diagram-data">
 * 2. This widget parses JSON on page load
 * 3. vis.Network renders interactive diagram
 * 4. User interactions (search, export, layout) handled by widget
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: odoo.define(), publicWidget dependency
 * - Replaced: jQuery with native DOM APIs
 * - Added: IIFE wrapper for module isolation
 * - Uses web_vis_network module's bundled vis.js library
 * - CDN fallback removed - now relies on web_vis_network
 * 
 * FEATURES:
 * ✓ Interactive diagram with drag/zoom
 * ✓ Search with node highlighting
 * ✓ Layout switching (hierarchical/force-directed)
 * ✓ JSON export for data portability
 * ✓ Real-time statistics display
 * ✓ Graceful degradation without vis.js
 * 
 * BROWSER SUPPORT: Modern browsers (ES6+), graceful fallback for older browsers
 */

(function() {
    'use strict';

    class OrgDiagramPortal {
        constructor(containerElement) {
            this.container = containerElement;
            this.diagramData = null;
            this.network = null;
            this.init();
        }

        init() {
            this._parseData();
            this._updateStats();
            this._setupEventHandlers();
            
            // Load vis-network library from CDN, then render diagram
            this._loadVisNetwork()
                .then(() => {
                    this._renderDiagram();
                })
                .catch((err) => {
                    console.error('[OrgDiagramPortal] Failed to load vis-network library', err);
                    this._showFallbackMessage();
                });
        }

        _setupEventHandlers() {
            // Refresh button
            const refreshBtn = this.container.querySelector('#refresh-diagram');
            if (refreshBtn) {
                refreshBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._onRefresh();
                });
            }

            // Export button
            const exportBtn = this.container.querySelector('#export-diagram');
            if (exportBtn) {
                exportBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._onExport();
                });
            }

            // Search button
            const searchBtn = this.container.querySelector('#search-button');
            if (searchBtn) {
                searchBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._applySearch();
                });
            }

            // Search input (enter key)
            const searchInput = this.container.querySelector('#search-query');
            if (searchInput) {
                searchInput.addEventListener('keyup', (e) => {
                    if (e.key === 'Enter') {
                        this._applySearch();
                    }
                });
            }

            // Layout selector
            const layoutSelect = this.container.querySelector('#layout-select');
            if (layoutSelect) {
                layoutSelect.addEventListener('change', () => {
                    this._onLayoutChanged();
                });
            }
        }

        _loadVisNetwork() {
            // Check if already loaded (from web_vis_network module or previously)
            if (window.vis && window.vis.Network) {
                console.log('[OrgDiagramPortal] vis.Network already loaded from web_vis_network module');
                return Promise.resolve();
            }
            
            // web_vis_network module should have loaded vis.js already via assets
            // If not available, wait briefly for async asset loading, then try CDN fallback
            return new Promise((resolve, reject) => {
                let attempts = 0;
                const maxAttempts = 5; // Reduced attempts before CDN fallback
                const checkInterval = 100; // ms
                
                const checkVisLoaded = () => {
                    attempts++;
                    if (window.vis && window.vis.Network) {
                        console.log('[OrgDiagramPortal] vis.Network loaded successfully');
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        // Fallback: Load from CDN
                        console.warn('[OrgDiagramPortal] vis.Network not in assets, loading from CDN...');
                        this._loadFromCDN().then(resolve).catch(reject);
                    } else {
                        setTimeout(checkVisLoaded, checkInterval);
                    }
                };
                
                checkVisLoaded();
            });
        }

        _loadFromCDN() {
            return new Promise((resolve, reject) => {
                // Load vis-network CSS
                const cssLink = document.createElement('link');
                cssLink.rel = 'stylesheet';
                cssLink.href = 'https://unpkg.com/vis-network@9.1.9/dist/dist/vis-network.min.css';
                document.head.appendChild(cssLink);

                // Load vis-network JS
                const script = document.createElement('script');
                script.src = 'https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js';
                script.onload = () => {
                    // Check multiple times as vis may take a moment to initialize
                    let checkCount = 0;
                    const checkVis = () => {
                        checkCount++;
                        if (window.vis && window.vis.Network) {
                            console.log('[OrgDiagramPortal] vis.Network loaded from CDN');
                            resolve();
                        } else if (checkCount < 10) {
                            setTimeout(checkVis, 100);
                        } else {
                            reject(new Error('vis.Network not available after CDN load'));
                        }
                    };
                    checkVis();
                };
                script.onerror = () => reject(new Error('Failed to load vis-network from CDN'));
                document.head.appendChild(script);
            });
        }

        _showFallbackMessage() {
            const diagramContainer = this.container.querySelector('#organization-diagram-container');
            if (diagramContainer) {
                diagramContainer.innerHTML = `
                    <div class="p-5 text-center">
                        <i class="fa fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <h5>Diagram Visualization Unavailable</h5>
                        <p class="text-muted">The visualization library could not be loaded.</p>
                        <p class="text-muted">Please check your internet connection and refresh the page.</p>
                    </div>
                `;
            }
        }

        _parseData() {
            try {
                const jsonEl = this.container.querySelector('#diagram-data');
                if (jsonEl) {
                    this.diagramData = JSON.parse(jsonEl.textContent.trim());
                } else {
                    this.diagramData = { nodes: [], edges: [], stats: {}, config: {} };
                }
            } catch (e) {
                console.error('[OrgDiagramPortal] Failed to parse diagram JSON', e);
                this.diagramData = { nodes: [], edges: [], stats: {}, config: {} };
            }
        }

        _renderDiagram() {
            const diagramContainer = this.container.querySelector('#organization-diagram-container');
            if (!diagramContainer) { 
                console.warn('[OrgDiagramPortal] Container #organization-diagram-container not found');
                return; 
            }
            
            // Check if we have vis-network loaded
            if (!window.vis || !window.vis.Network) {
                console.error('[OrgDiagramPortal] vis.Network not available');
                this._showFallbackMessage();
                return;
            }
            
            // Check if we have data
            if (!this.diagramData.nodes || !this.diagramData.nodes.length) {
                diagramContainer.innerHTML = `
                    <div class="p-5 text-center">
                        <i class="fa fa-info-circle fa-3x text-info mb-3"></i>
                        <h5>No Organization Data</h5>
                        <p class="text-muted">Your organization structure is empty.</p>
                        <p class="text-muted">Contact your administrator to set up departments and team members.</p>
                    </div>
                `;
                return;
            }
            
            // Remove loading overlay
            const loadingOverlay = diagramContainer.querySelector('.loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.remove();
            }
            
            // Build vis-network options
            const options = this._buildVisOptions();
            
            // Render the network
            try {
                this.network = new vis.Network(diagramContainer, {
                    nodes: new vis.DataSet(this.diagramData.nodes),
                    edges: new vis.DataSet(this.diagramData.edges),
                }, options);
                
                console.log('[OrgDiagramPortal] Diagram rendered successfully with', this.diagramData.nodes.length, 'nodes');
                
                // Add event listeners
                this.network.on('click', (params) => this._onNodeClick(params));
                
            } catch (e) {
                console.error('[OrgDiagramPortal] vis.Network rendering failed', e);
                this._showFallbackMessage();
            }
        }

        _buildVisOptions() {
            const layoutType = (this.diagramData.config && this.diagramData.config.layout_type) || 'hierarchical';
            const hierarchical = layoutType === 'hierarchical';
            
            const options = {
                layout: hierarchical ? {
                    hierarchical: {
                        direction: 'UD',
                        sortMethod: 'directed',
                        nodeSpacing: 150,
                        levelSeparation: 150,
                    }
                } : {
                    randomSeed: 2
                },
                interaction: {
                    hover: true,
                    navigationButtons: true,
                    keyboard: true,
                },
                physics: hierarchical ? false : {
                    enabled: true,
                    stabilization: {
                        enabled: true,
                        iterations: 100,
                    },
                },
                nodes: {
                    shape: 'box',
                    margin: 10,
                    widthConstraint: {
                        minimum: 100,
                        maximum: 200,
                    },
                    font: {
                        size: 14,
                        face: 'Arial',
                    },
                    borderWidth: 2,
                    shadow: true,
                },
                edges: {
                    arrows: {
                        to: {
                            enabled: true,
                            scaleFactor: 0.5,
                        }
                    },
                    smooth: {
                        type: 'cubicBezier',
                        roundness: 0.5,
                    },
                    width: 2,
                },
            };
            
            return options;
        }

        _onNodeClick(params) {
            if (params.nodes && params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = this.diagramData.nodes.find(n => n.id === nodeId);
                if (node) {
                    this._showNodeDetails(node);
                }
            }
        }

        _showNodeDetails(node) {
            const modal = this.container.querySelector('#node-details-modal');
            const title = this.container.querySelector('#node-modal-title');
            const body = this.container.querySelector('#node-modal-body');
            
            if (!modal || !title || !body) return;
            
            title.textContent = node.name || node.label || 'Unknown';
            
            let html = '<div class="row">';
            html += '<div class="col-md-4 text-center">';
            if (node.image) {
                html += `<img src="${node.image}" class="img-fluid rounded mb-3" alt="${node.name}" style="max-width: 150px;">`;
            }
            html += '</div>';
            html += '<div class="col-md-8">';
            html += '<table class="table table-sm">';
            if (node.type) {
                html += `<tr><th>Type:</th><td><span class="badge badge-primary">${node.type}</span></td></tr>`;
            }
            if (node.email) {
                html += `<tr><th>Email:</th><td><a href="mailto:${node.email}">${node.email}</a></td></tr>`;
            }
            if (node.phone) {
                html += `<tr><th>Phone:</th><td>${node.phone}</td></tr>`;
            }
            if (node.job_title) {
                html += `<tr><th>Job Title:</th><td>${node.job_title}</td></tr>`;
            }
            html += '</table>';
            html += '</div>';
            html += '</div>';
            
            body.innerHTML = html;
            
            // Show modal using Bootstrap 5
            if (window.bootstrap && window.bootstrap.Modal) {
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
            } else {
                // Fallback for older Bootstrap
                modal.classList.add('show');
                modal.style.display = 'block';
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        }

        _updateStats() {
            const stats = this.diagramData.stats || {};
            const mapping = {
                companies: '#companies-count',
                departments: '#departments-count',
                users: '#users-count',
                connections: '#connections-count',
            };
            
            // Batch DOM queries for performance
            const elements = {};
            for (const key in mapping) {
                elements[key] = this.container.querySelector(mapping[key]);
            }
            
            // Batch DOM updates
            for (const key in elements) {
                const el = elements[key];
                if (el) { 
                    el.textContent = stats[key] != null ? stats[key] : '-'; 
                }
            }
        }

        _onRefresh() {
            this._parseData();
            this._renderDiagram();
            this._updateStats();
        }

        _onExport() {
            const blob = new Blob([JSON.stringify(this.diagramData, null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'organization_diagram.json';
            a.click();
        }

        _applySearch() {
            if (!this.network) { return; }
            
            const searchInput = this.container.querySelector('#search-query');
            const query = (searchInput?.value || '').trim().toLowerCase();
            
            if (!query) { 
                // Clear previous selection
                this.network.unselectAll();
                return; 
            }
            
            const matches = this.diagramData.nodes.filter(n => (n.label || '').toLowerCase().includes(query));
            
            if (matches.length) {
                const ids = matches.map(m => m.id);
                this.network.selectNodes(ids, true);
                this.network.focus(ids[0], { 
                    scale: 1.2, 
                    animation: { 
                        duration: 500, 
                        easingFunction: 'easeInOutQuad' 
                    } 
                });
                
                // Accessibility: Announce results
                const resultMsg = matches.length === 1 
                    ? '1 node found' 
                    : matches.length + ' nodes found';
                console.log('[OrgDiagramPortal] Search: ' + resultMsg);
            } else {
                console.log('[OrgDiagramPortal] Search: No matches found for "' + query + '"');
            }
        }

        _onLayoutChanged() {
            if (!this.network) { return; }
            
            const layoutSelect = this.container.querySelector('#layout-select');
            this.diagramData.config = this.diagramData.config || {};
            this.diagramData.config.layout_type = layoutSelect?.value;
            this._renderDiagram();
        }
    }

    // Auto-initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOrgDiagram);
    } else {
        initOrgDiagram();
    }

    function initOrgDiagram() {
        const containers = document.querySelectorAll('.o_portal_organization_diagram');
        containers.forEach(container => {
            new OrgDiagramPortal(container);
        });
    }

    // Expose globally for manual initialization if needed
    window.RecordsManagementOrgDiagram = OrgDiagramPortal;
})();
