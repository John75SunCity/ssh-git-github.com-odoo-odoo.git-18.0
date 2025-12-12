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
            
            // Message User button
            const messageBtn = this.container.querySelector('#message-user-btn');
            if (messageBtn) {
                messageBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._sendMessage();
                });
            }
            
            // Email User button
            const emailBtn = this.container.querySelector('#email-user-btn');
            if (emailBtn) {
                emailBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._sendEmail();
                });
            }
            
            // Live Chat button
            const liveChatBtn = this.container.querySelector('#livechat-user-btn');
            if (liveChatBtn) {
                liveChatBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._startLiveChat();
                });
            }
            
            // Filter buttons
            const filterButtons = this.container.querySelectorAll('.filter-btn');
            filterButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._onFilterClick(btn);
                });
            });
            
            // Reset filters button
            const resetBtn = this.container.querySelector('#reset-filters');
            if (resetBtn) {
                resetBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this._resetFilters();
                });
            }
            
            // Initialize active filters (all types visible by default)
            this.activeFilters = new Set(['company', 'department', 'internal', 'portal', 'current_user']);
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
            console.log('Node clicked:', params);
            if (params.nodes && params.nodes.length > 0) {
                console.log('Selected node ID:', params.nodes[0]);
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
            const messageBtn = this.container.querySelector('#message-user-btn');
            const emailBtn = this.container.querySelector('#email-user-btn');
            
            if (!modal || !title || !body) return;
            
            // Store current node for messaging
            this.currentNode = node;
            
            title.textContent = node.name || node.label || 'Unknown';
            
            let html = '<div class="row">';
            html += '<div class="col-md-4 text-center">';
            if (node.image && node.image.trim() !== '') {
                html += `<img src="${node.image}" class="img-fluid rounded mb-3" alt="${node.name}" style="max-width: 150px;" onerror="this.style.display='none'">`;
            }
            // Show node type icon
            const iconMap = { company: 'fa-building', department: 'fa-sitemap', person: 'fa-user' };
            const colorMap = { company: '#f39c12', department: '#27ae60', person: node.color || '#3498db' };
            html += `<div class="mt-2"><i class="fa ${iconMap[node.type] || 'fa-circle'} fa-2x" style="color: ${colorMap[node.type]}"></i></div>`;
            html += '</div>';
            html += '<div class="col-md-8">';
            html += '<table class="table table-sm">';
            if (node.type) {
                const typeLabels = { company: 'Company', department: 'Department', person: 'Person' };
                html += `<tr><th>Type:</th><td><span class="badge" style="background-color: ${colorMap[node.type]}; color: white;">${typeLabels[node.type] || node.type}</span></td></tr>`;
            }
            if (node.job_title) {
                html += `<tr><th>Role:</th><td>${node.job_title}</td></tr>`;
            }
            if (node.email) {
                html += `<tr><th>Email:</th><td><a href="mailto:${node.email}"><i class="fa fa-envelope"></i> ${node.email}</a></td></tr>`;
            }
            if (node.phone) {
                html += `<tr><th>Phone:</th><td><a href="tel:${node.phone}"><i class="fa fa-phone"></i> ${node.phone}</a></td></tr>`;
            }
            // Show department stats if available
            if (node.type === 'department') {
                if (node.container_count !== undefined) {
                    html += `<tr><th>Containers:</th><td><i class="fa fa-archive"></i> ${node.container_count}</td></tr>`;
                }
                if (node.file_count !== undefined) {
                    html += `<tr><th>Files:</th><td><i class="fa fa-file"></i> ${node.file_count}</td></tr>`;
                }
            }
            // Show access level for users
            if (node.role) {
                html += `<tr><th>Access:</th><td>${node.role} (${node.access_level || 'standard'})</td></tr>`;
            }
            if (node.is_current_user) {
                html += `<tr><td colspan="2" class="text-center"><span class="badge badge-danger bg-danger">This is you!</span></td></tr>`;
            }
            html += '</table>';
            html += '</div>';
            html += '</div>';
            
            body.innerHTML = html;
            
            // Show/hide action buttons based on node type
            if (messageBtn) {
                // Show message button only for persons (not current user) with email
                if (node.type === 'person' && !node.is_current_user && node.email) {
                    messageBtn.classList.remove('d-none');
                } else {
                    messageBtn.classList.add('d-none');
                }
            }
            if (emailBtn) {
                // Show email button for any node with email
                if (node.email && !node.is_current_user) {
                    emailBtn.classList.remove('d-none');
                } else {
                    emailBtn.classList.add('d-none');
                }
            }
            
            // Show modal using Bootstrap 5 (preferred)
            this._showModal(modal);
        }
        
        _showModal(modal) {
            console.log('Showing modal using ' + (window.bootstrap ? 'Bootstrap' : 'fallback'));
            // Clean up any existing backdrop first
            this._cleanupModal();
            
            if (window.bootstrap && window.bootstrap.Modal) {
                // Bootstrap 5 - use native modal
                const existingInstance = bootstrap.Modal.getInstance(modal);
                if (existingInstance) {
                    existingInstance.dispose();
                }
                this.modalInstance = new bootstrap.Modal(modal, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
                this.modalInstance.show();
            } else {
                // Fallback: Open modal manually
                this._cleanupModal();
                modal.classList.remove('fade');
                modal.classList.add('show');
                modal.style.display = 'block';
                modal.style.opacity = '1';
                modal.style.zIndex = '1050';
                modal.setAttribute('aria-modal', 'true');
                modal.removeAttribute('aria-hidden');
                document.body.classList.add('modal-open');
                
                // Create backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'org-diagram-backdrop';
                backdrop.style.zIndex = '1040';
                document.body.appendChild(backdrop);
                
                // Close handlers
                const closeModal = () => this._hideModal(modal);
                
                // Close on backdrop click
                backdrop.addEventListener('click', closeModal);
                
                // Close on X button and Close button
                modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach(btn => {
                    btn.addEventListener('click', closeModal);
                });
                
                // Close on Escape key
                this._escHandler = (e) => {
                    if (e.key === 'Escape') closeModal();
                };
                document.addEventListener('keydown', this._escHandler);
            }
        }
        
        _hideModal(modal) {
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            modal.removeAttribute('aria-modal');
            document.body.classList.remove('modal-open');
            this._cleanupModal();
        }
        
        _cleanupModal() {
            // Remove any existing backdrops
            document.querySelectorAll('.modal-backdrop, #org-diagram-backdrop').forEach(el => el.remove());
            
            // Remove escape handler if exists
            if (this._escHandler) {
                document.removeEventListener('keydown', this._escHandler);
                this._escHandler = null;
            }
        }
        
        _sendMessage() {
            if (!this.currentNode || !this.currentNode.email) {
                console.warn('[OrgDiagramPortal] No node selected or no email available');
                return;
            }
            
            // Try to open Odoo's mail compose if available, otherwise open mailto
            const partnerId = this.currentNode.id.replace('user_', '').replace('company_', '').replace('dept_', '');
            
            // Check if we're in Odoo context with mail composer available
            if (window.odoo && window.odoo.define) {
                // Try Odoo's internal messaging
                this._openOdooComposer(partnerId);
            } else {
                // Fallback: Open mailto with pre-filled subject
                const subject = encodeURIComponent('Message from Organization Portal');
                const body = encodeURIComponent(`Hi ${this.currentNode.name},\n\n`);
                window.location.href = `mailto:${this.currentNode.email}?subject=${subject}&body=${body}`;
            }
            
            // Close the modal
            const modal = this.container.querySelector('#node-details-modal');
            if (modal && this.modalInstance) {
                this.modalInstance.hide();
            } else if (modal) {
                this._hideModal(modal);
            }
        }
        
        _sendEmail() {
            if (!this.currentNode || !this.currentNode.email) {
                console.warn('[OrgDiagramPortal] No node selected or no email available');
                return;
            }
            
            // Open mailto directly
            const subject = encodeURIComponent(`Regarding: ${this.currentNode.name}`);
            const body = encodeURIComponent(`Hi ${this.currentNode.name},\n\n`);
            window.open(`mailto:${this.currentNode.email}?subject=${subject}&body=${body}`, '_blank');
        }
        
        _openOdooComposer(partnerId) {
            // Try to use Odoo's discuss/chat functionality
            // This opens the chat with the user if available
            const chatUrl = `/mail/chat/${partnerId}`;
            
            // Check if LiveChat or Discuss is available
            if (window.odoo && window.odoo.session_info) {
                // Try to open chat panel
                window.location.href = chatUrl;
            } else {
                // Fallback to email
                this._sendEmail();
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
            // Export as Excel-compatible CSV format
            const nodes = this.diagramData.nodes || [];
            const edges = this.diagramData.edges || [];
            
            // Build CSV content with BOM for Excel UTF-8 compatibility
            const BOM = '\uFEFF';
            let csv = BOM;
            
            // Sheet 1: Organization Members
            csv += 'ORGANIZATION DIRECTORY\n';
            csv += 'Generated:,' + new Date().toLocaleDateString() + '\n\n';
            
            // Headers for nodes
            csv += 'Name,Type,Email,Phone,Role,Department/Company,Access Level,Containers,Files\n';
            
            // Sort nodes: companies first, then departments, then people
            const sortOrder = { company: 0, department: 1, person: 2 };
            const sortedNodes = [...nodes].sort((a, b) => 
                (sortOrder[a.type] || 99) - (sortOrder[b.type] || 99)
            );
            
            // Data rows
            sortedNodes.forEach(node => {
                const name = this._escapeCSV(node.name || node.label || '');
                const type = this._escapeCSV(node.type || '');
                const email = this._escapeCSV(node.email || '');
                const phone = this._escapeCSV(node.phone || '');
                const jobTitle = this._escapeCSV(node.job_title || '');
                const accessLevel = this._escapeCSV(node.access_level || '');
                const containers = node.container_count !== undefined ? node.container_count : '';
                const files = node.file_count !== undefined ? node.file_count : '';
                
                csv += `${name},${type},${email},${phone},${jobTitle},${accessLevel},${containers},${files}\n`;
            });
            
            // Add summary section
            csv += '\n\nSUMMARY\n';
            csv += 'Metric,Count\n';
            const stats = this.diagramData.stats || {};
            csv += `Companies,${stats.companies || 0}\n`;
            csv += `Departments,${stats.departments || 0}\n`;
            csv += `People,${stats.users || 0}\n`;
            csv += `Connections,${stats.connections || 0}\n`;
            
            // Add relationships section
            csv += '\n\nRELATIONSHIPS\n';
            csv += 'From,To,Type\n';
            edges.forEach(edge => {
                const fromNode = nodes.find(n => n.id === edge.from);
                const toNode = nodes.find(n => n.id === edge.to);
                const fromName = this._escapeCSV(fromNode?.name || fromNode?.label || edge.from);
                const toName = this._escapeCSV(toNode?.name || toNode?.label || edge.to);
                const relType = edge.dashes ? 'Unassigned' : 'Reports To';
                csv += `${fromName},${toName},${relType}\n`;
            });
            
            // Create and download file
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'organization_directory_' + new Date().toISOString().split('T')[0] + '.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
            
            console.log('[OrgDiagramPortal] Exported organization directory to Excel (CSV)');
        }
        
        _escapeCSV(str) {
            // Escape CSV field: wrap in quotes if contains comma, quote, or newline
            if (!str) return '';
            str = String(str);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
                return '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        }
        
        _startLiveChat() {
            if (!this.currentNode) {
                console.warn('[OrgDiagramPortal] No node selected for live chat');
                return;
            }
            
            // Try to open Odoo's LiveChat or Discuss
            const userId = this.currentNode.id.replace('user_', '');
            
            // Method 1: Try Odoo Discuss direct channel
            if (window.odoo) {
                // Open discuss with this partner
                const discussUrl = `/web#action=mail.action_discuss&active_id=mail.channel_${userId}`;
                window.open(discussUrl, '_blank');
            } else {
                // Fallback: Show message that live chat requires login
                alert('Live Chat requires logging into the main application. Click OK to open email instead.');
                this._sendEmail();
            }
            
            // Close modal
            const modal = this.container.querySelector('#node-details-modal');
            if (modal && this.modalInstance) {
                this.modalInstance.hide();
            } else if (modal) {
                this._hideModal(modal);
            }
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

        _onFilterClick(button) {
            const filterType = button.getAttribute('data-filter');
            if (!filterType) return;
            
            // Toggle active state
            button.classList.toggle('active');
            
            // Update active filters set
            if (button.classList.contains('active')) {
                this.activeFilters.add(filterType);
                // Solid button style when active
                button.classList.remove('btn-outline-warning', 'btn-outline-success', 'btn-outline-info', 'btn-outline-danger');
                const colorMap = {
                    'company': 'btn-warning',
                    'department': 'btn-success',
                    'internal': 'btn-info',
                    'portal': 'btn-pink',
                    'current_user': 'btn-danger'
                };
                if (filterType === 'portal') {
                    button.style.backgroundColor = '#e91e63';
                    button.style.borderColor = '#e91e63';
                    button.style.color = '#fff';
                } else {
                    button.classList.add(colorMap[filterType] || 'btn-secondary');
                }
            } else {
                this.activeFilters.delete(filterType);
                // Outline button style when inactive
                button.classList.remove('btn-warning', 'btn-success', 'btn-info', 'btn-danger', 'btn-pink');
                const outlineMap = {
                    'company': 'btn-outline-warning',
                    'department': 'btn-outline-success',
                    'internal': 'btn-outline-info',
                    'portal': 'btn-outline-pink',
                    'current_user': 'btn-outline-danger'
                };
                if (filterType === 'portal') {
                    button.style.backgroundColor = 'transparent';
                    button.style.borderColor = '#e91e63';
                    button.style.color = '#e91e63';
                } else {
                    button.classList.add(outlineMap[filterType] || 'btn-outline-secondary');
                }
            }
            
            // Apply filters to diagram
            this._applyFilters();
        }

        _resetFilters() {
            // Reset all filter buttons to active state
            const filterButtons = this.container.querySelectorAll('.filter-btn');
            this.activeFilters = new Set(['company', 'department', 'internal', 'portal', 'current_user']);
            
            filterButtons.forEach(btn => {
                const filterType = btn.getAttribute('data-filter');
                btn.classList.add('active');
                
                // Apply solid button styles
                btn.classList.remove('btn-outline-warning', 'btn-outline-success', 'btn-outline-info', 'btn-outline-danger');
                const colorMap = {
                    'company': 'btn-warning',
                    'department': 'btn-success',
                    'internal': 'btn-info',
                    'portal': 'btn-pink',
                    'current_user': 'btn-danger'
                };
                if (filterType === 'portal') {
                    btn.style.backgroundColor = '#e91e63';
                    btn.style.borderColor = '#e91e63';
                    btn.style.color = '#fff';
                } else {
                    btn.classList.add(colorMap[filterType] || 'btn-secondary');
                }
            });
            
            // Re-render diagram with all nodes visible
            this._applyFilters();
        }

        _applyFilters() {
            if (!this.network || !this.diagramData.nodes) return;
            
            // Determine which node types should be visible
            const visibleTypes = this.activeFilters;
            
            // Create filtered node set
            const filteredNodes = this.diagramData.nodes.map(node => {
                // Map node type to filter type
                let nodeFilterType = node.type;
                
                // Handle person nodes - check if internal or portal
                if (node.type === 'person') {
                    // Check node properties to determine user type
                    if (node.is_current_user) {
                        nodeFilterType = 'current_user';
                    } else if (node.is_portal) {
                        nodeFilterType = 'portal';
                    } else {
                        nodeFilterType = 'internal';
                    }
                }
                
                // Check visibility
                const isVisible = visibleTypes.has(nodeFilterType) || 
                                 (node.is_current_user && visibleTypes.has('current_user'));
                
                return {
                    ...node,
                    hidden: !isVisible
                };
            });
            
            // Update the network with filtered nodes
            if (this.network) {
                const nodesDataSet = new vis.DataSet(filteredNodes);
                this.network.setData({
                    nodes: nodesDataSet,
                    edges: new vis.DataSet(this.diagramData.edges)
                });
            }
            
            console.log('[OrgDiagramPortal] Filters applied: ' + Array.from(visibleTypes).join(', '));
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
