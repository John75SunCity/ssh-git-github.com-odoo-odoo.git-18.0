/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { debounce } from "@web/core/utils/timing";

/**
 * Advanced Portal Inventory Search System
 * Features: Google-like search, autocomplete, debounced RPC, smart filtering
 */

class PortalInventorySearch {
    constructor() {
        this.searchTimeout = null;
        this.lastQuery = '';
        this.searchHistory = JSON.parse(localStorage.getItem('portal_search_history') || '[]');
        this.commonQueries = [
            'active boxes',
            'archived documents',
            'request destruction',
            'pending pickup',
            'expiring soon',
            'destroy document',
            'checkout box',
            'retention expired',
            'available storage',
            'recent activity'
        ];
        this.suggestions = [];
        this.init();
    }

    init() {
        this.setupSearchInput();
        this.setupFilters();
        this.setupAutocomplete();
        this.setupAdvancedSearch();
        this.setupAjaxPagination();  // From Grok suggestion
        this.loadSearchSuggestions();

        console.log('Portal Inventory Search initialized');
    }

    setupSearchInput() {
        const searchInput = document.getElementById('global_search');
        if (!searchInput) return;

        // Debounced search function
        const debouncedSearch = debounce(this.performSearch.bind(this), 300);

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                debouncedSearch(query);
                this.updateAutocomplete(query);
            } else if (query.length === 0) {
                this.clearResults();
            }
        });

        // Handle Enter key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(e.target.value.trim(), true);
                this.addToSearchHistory(e.target.value.trim());
            }
        });

        // Focus event to show suggestions
        searchInput.addEventListener('focus', () => {
            this.showSearchSuggestions();
        });
    }

    setupFilters() {
        // Filter change handlers
        const filterElements = [
            'filter_type',
            'filter_status',
            'filter_location',
            'date_from',
            'date_to'
        ];

        filterElements.forEach(filterId => {
            const element = document.getElementById(filterId);
            if (element) {
                element.addEventListener('change', () => {
                    this.applyFilters();
                });
            }
        });

        // Quick filter buttons
        this.setupQuickFilters();
    }

    setupQuickFilters() {
        const quickFilterButtons = [
            { id: 'quick_active', filter: { state: 'active' }, label: 'Active Only' },
            { id: 'quick_expiring', filter: { retention_expiring: true }, label: 'Expiring Soon' },
            { id: 'quick_pending', filter: { pending_action: true }, label: 'Pending Action' },
            { id: 'quick_recent', filter: { recent: true }, label: 'Recent Activity' }
        ];

        quickFilterButtons.forEach(button => {
            const element = document.getElementById(button.id);
            if (element) {
                element.addEventListener('click', () => {
                    this.applyQuickFilter(button.filter);
                    this.highlightActiveFilter(element);
                });
            }
        });
    }

    setupAutocomplete() {
        const searchInput = document.getElementById('global_search');
        if (!searchInput) return;

        // Create autocomplete dropdown
        const dropdown = document.createElement('div');
        dropdown.id = 'search_autocomplete';
        dropdown.className = 'search-autocomplete-dropdown';
        dropdown.style.display = 'none';
        searchInput.parentNode.appendChild(dropdown);

        // Handle suggestion clicks
        dropdown.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-item')) {
                const suggestion = e.target.textContent;
                searchInput.value = suggestion;
                this.performSearch(suggestion, true);
                this.hideAutocomplete();
                this.addToSearchHistory(suggestion);
            }
        });

        // Hide dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                this.hideAutocomplete();
            }
        });
    }

    setupAdvancedSearch() {
        const advancedToggle = document.getElementById('advanced_search_toggle');
        const advancedPanel = document.getElementById('advanced_search_panel');

        if (advancedToggle && advancedPanel) {
            advancedToggle.addEventListener('click', () => {
                const isVisible = advancedPanel.style.display !== 'none';
                advancedPanel.style.display = isVisible ? 'none' : 'block';
                advancedToggle.innerHTML = isVisible ?
                    '<i class="fa fa-chevron-down"></i> Advanced Search' :
                    '<i class="fa fa-chevron-up"></i> Hide Advanced';
            });
        }

        // Advanced search form submission
        const advancedForm = document.getElementById('advanced_search_form');
        if (advancedForm) {
            advancedForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performAdvancedSearch();
            });
        }
    }

    /**
     * AJAX Pagination Setup (from Grok suggestion)
     * Loads new page content without full page reload
     */
    setupAjaxPagination() {
        document.addEventListener('click', (e) => {
            // Check if clicked element is a pagination link
            if (e.target.closest('.pagination a')) {
                const link = e.target.closest('.pagination a');
                const href = link.getAttribute('href');
                
                // Security: Prevent default only for safe URLs (reject javascript:, data:, vbscript: schemes)
                if (href && href !== '#' && this.isSafeUrl(href)) {
                    e.preventDefault();
                    this.loadPageContent(href);
                }
            }
        });
    }

    /**
     * Security check: Validate URL scheme to prevent code injection
     * Rejects javascript:, data:, and vbscript: schemes per OWASP/CodeQL recommendations
     * @param {string} url - The URL to validate
     * @returns {boolean} - True if URL is safe to use
     */
    isSafeUrl(url) {
        if (!url || typeof url !== 'string') {
            return false;
        }
        
        // Normalize URL for comparison (decode and lowercase)
        const normalizedUrl = decodeURI(url).trim().toLowerCase();
        
        // Reject dangerous URL schemes
        const dangerousSchemes = ['javascript:', 'data:', 'vbscript:'];
        return !dangerousSchemes.some(scheme => normalizedUrl.startsWith(scheme));
    }

    /**
     * Load page content via AJAX (from Grok suggestion)
     * @param {string} url - The URL to load
     */
    async loadPageContent(url) {
        this.showLoadingState();
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'  // Mark as AJAX request
                }
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update table content
            const newTableBody = doc.querySelector('#inventory_table tbody');
            const currentTableBody = document.querySelector('#inventory_table tbody');
            if (newTableBody && currentTableBody) {
                currentTableBody.innerHTML = newTableBody.innerHTML;
            }
            
            // Update pagination
            const newPagination = doc.querySelector('.pagination');
            const currentPagination = document.querySelector('.pagination');
            if (newPagination && currentPagination) {
                currentPagination.innerHTML = newPagination.innerHTML;
            }
            
            // Update result count if present
            const newResultCount = doc.querySelector('#result_count');
            const currentResultCount = document.querySelector('#result_count');
            if (newResultCount && currentResultCount) {
                currentResultCount.innerHTML = newResultCount.innerHTML;
            }
            
            this.hideLoadingState();
            
            // Scroll to top smoothly
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            // Re-initialize tooltips for new content
            this.reinitializeTooltips();
            
        } catch (error) {
            console.error('Page load error:', error);
            this.showErrorState('Failed to load page. Please try again.');
            this.hideLoadingState();
        }
    }

    /**
     * Re-initialize tooltips after AJAX content update
     */
    reinitializeTooltips() {
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle=\"tooltip\"]')
        );
        
        if (window.bootstrap && bootstrap.Tooltip) {
            tooltipTriggerList.forEach(tooltipTriggerEl => {
                // Dispose old tooltip if exists
                const existingTooltip = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
                if (existingTooltip) {
                    existingTooltip.dispose();
                }
                // Create new tooltip
                new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    async performSearch(query, addToHistory = false) {
        if (!query || query === this.lastQuery) return;

        this.lastQuery = query;
        this.showLoadingState();

        try {
            // Parse query for special commands
            const parsedQuery = this.parseSearchQuery(query);

            // Build search domain
            const domain = this.buildSearchDomain(parsedQuery);

            // Perform RPC search
            const results = await rpc('/web/dataset/search_read', {
                model: 'records.container',
                domain: domain,
                fields: [
                    'name', 'barcode', 'description', 'state', 'location_id',
                    'document_count', 'destruction_due_date', 'partner_id', 'create_date'
                ],
                limit: 100,
                sort: 'write_date desc'
            });

            // Also search documents if query suggests it
            let documentResults = [];
            if (this.shouldSearchDocuments(query)) {
                documentResults = await rpc('/web/dataset/search_read', {
                    model: 'records.document',
                    domain: this.buildDocumentSearchDomain(parsedQuery),
                    fields: ['name', 'document_type', 'state', 'box_id', 'create_date'],
                    limit: 50
                });
            }

            // Update UI with results
            this.updateSearchResults(results, documentResults);
            this.hideLoadingState();

            if (addToHistory) {
                this.addToSearchHistory(query);
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showErrorState('Search failed. Please try again.');
            this.hideLoadingState();
        }
    }

    parseSearchQuery(query) {
        const parsed = {
            text: query.toLowerCase(),
            actions: [],
            filters: {},
            exact: false
        };

        // Detect action keywords
        const actionKeywords = {
            'destroy': 'destruction',
            'destruction': 'destruction',
            'pickup': 'pickup',
            'checkout': 'checkout',
            'archive': 'archive',
            'retrieve': 'retrieval'
        };

        Object.keys(actionKeywords).forEach(keyword => {
            if (parsed.text.includes(keyword)) {
                parsed.actions.push(actionKeywords[keyword]);
            }
        });

        // Detect state filters
        if (parsed.text.includes('active')) parsed.filters.state = 'active';
        if (parsed.text.includes('archived')) parsed.filters.state = 'archived';
        if (parsed.text.includes('destroyed')) parsed.filters.state = 'destroyed';
        if (parsed.text.includes('pending')) parsed.filters.pending = true;
        if (parsed.text.includes('expiring')) parsed.filters.expiring = true;

        // Detect exact search (quoted strings)
        const quotedMatch = query.match(/"([^"]*)"/);
        if (quotedMatch) {
            parsed.exact = true;
            parsed.text = quotedMatch[1];
        }

        return parsed;
    }

    buildSearchDomain(parsedQuery) {
        const domain = [];

        if (parsedQuery.exact) {
            // Exact match search
            domain.push('|', '|', '|');
            domain.push(['name', '=', parsedQuery.text]);
            domain.push(['barcode', '=', parsedQuery.text]);
            domain.push(['description', '=', parsedQuery.text]);
            domain.push(['location_id.name', '=', parsedQuery.text]);
        } else {
            // Fuzzy search across multiple fields
            domain.push('|', '|', '|', '|');
            domain.push(['name', 'ilike', parsedQuery.text]);
            domain.push(['barcode', 'ilike', parsedQuery.text]);
            domain.push(['description', 'ilike', parsedQuery.text]);
            domain.push(['location_id.name', 'ilike', parsedQuery.text]);
            domain.push(['partner_id.name', 'ilike', parsedQuery.text]);
        }

        // Apply state filters
        if (parsedQuery.filters.state) {
            domain.push(['state', '=', parsedQuery.filters.state]);
        }

        // Apply special filters
        if (parsedQuery.filters.expiring) {
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + 30);
            domain.push(['destruction_due_date', '<=', futureDate.toISOString().split('T')[0]]);
        }

        // Always filter by current user's access
        domain.push(['partner_id', 'child_of', window.portalPartnerId || 0]);

        return domain;
    }

    buildDocumentSearchDomain(parsedQuery) {
        const domain = [];

        if (parsedQuery.exact) {
            domain.push('|', '|');
            domain.push(['name', '=', parsedQuery.text]);
            domain.push(['document_type.name', '=', parsedQuery.text]);
            domain.push(['description', '=', parsedQuery.text]);
        } else {
            domain.push('|', '|');
            domain.push(['name', 'ilike', parsedQuery.text]);
            domain.push(['document_type.name', 'ilike', parsedQuery.text]);
            domain.push(['description', 'ilike', parsedQuery.text]);
        }

        if (parsedQuery.filters.state) {
            domain.push(['state', '=', parsedQuery.filters.state]);
        }

        return domain;
    }

    shouldSearchDocuments(query) {
        const documentKeywords = ['document', 'file', 'paper', 'record', 'certificate'];
        return documentKeywords.some(keyword =>
            query.toLowerCase().includes(keyword)
        );
    }

    async applyFilters() {
        const filters = {
            type: document.getElementById('filter_type')?.value || '',
            status: document.getElementById('filter_status')?.value || '',
            location: document.getElementById('filter_location')?.value || '',
            date_from: document.getElementById('date_from')?.value || '',
            date_to: document.getElementById('date_to')?.value || ''
        };

        this.showLoadingState();

        try {
            const domain = this.buildFilterDomain(filters);

            const results = await rpc('/web/dataset/search_read', {
                model: 'records.container',
                domain: domain,
                fields: [
                    'name', 'barcode', 'description', 'state', 'location_id',
                    'document_count', 'destruction_due_date', 'partner_id', 'create_date'
                ],
                limit: 100,
                sort: 'write_date desc'
            });

            this.updateSearchResults(results, []);
            this.hideLoadingState();

        } catch (error) {
            console.error('Filter error:', error);
            this.showErrorState('Filter failed. Please try again.');
            this.hideLoadingState();
        }
    }

    buildFilterDomain(filters) {
        const domain = [['partner_id', 'child_of', window.portalPartnerId || 0]];

        if (filters.type) {
            domain.push(['box_type', '=', filters.type]);
        }

        if (filters.status) {
            domain.push(['state', '=', filters.status]);
        }

        if (filters.location) {
            domain.push(['location_id', '=', parseInt(filters.location)]);
        }

        if (filters.date_from) {
            domain.push(['create_date', '>=', filters.date_from]);
        }

        if (filters.date_to) {
            domain.push(['create_date', '<=', filters.date_to]);
        }

        return domain;
    }

    async applyQuickFilter(filter) {
        this.showLoadingState();

        try {
            const domain = this.buildQuickFilterDomain(filter);

            const results = await rpc('/web/dataset/search_read', {
                model: 'records.container',
                domain: domain,
                fields: [
                    'name', 'barcode', 'description', 'state', 'location_id',
                    'document_count', 'destruction_due_date', 'partner_id', 'create_date'
                ],
                limit: 100,
                sort: 'write_date desc'
            });

            this.updateSearchResults(results, []);
            this.hideLoadingState();

        } catch (error) {
            console.error('Quick filter error:', error);
            this.showErrorState('Quick filter failed. Please try again.');
            this.hideLoadingState();
        }
    }

    buildQuickFilterDomain(filter) {
        const domain = [['partner_id', 'child_of', window.portalPartnerId || 0]];

        if (filter.state) {
            domain.push(['state', '=', filter.state]);
        }

        if (filter.retention_expiring) {
            const futureDate = new Date();
            futureDate.setDate(futureDate.getDate() + 30);
            domain.push(['destruction_due_date', '<=', futureDate.toISOString().split('T')[0]]);
            domain.push(['state', '!=', 'destroyed']);
        }

        if (filter.pending_action) {
            domain.push(['state', 'in', ['pending_pickup', 'pending_destruction', 'checkout']]);
        }

        if (filter.recent) {
            const lastWeek = new Date();
            lastWeek.setDate(lastWeek.getDate() - 7);
            domain.push(['write_date', '>=', lastWeek.toISOString()]);
        }

        return domain;
    }

    updateSearchResults(boxResults, documentResults) {
        const tableBody = document.querySelector('#inventory_table tbody');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        // Add boxes
        boxResults.forEach(box => {
            const row = this.createBoxRow(box);
            tableBody.appendChild(row);
        });

        // Add documents if any
        documentResults.forEach(doc => {
            const row = this.createDocumentRow(doc);
            tableBody.appendChild(row);
        });

        // Update result count
        const totalResults = boxResults.length + documentResults.length;
        this.updateResultCount(totalResults);

        // Show "no results" message if needed
        if (totalResults === 0) {
            this.showNoResultsMessage();
        }
    }

    createBoxRow(box) {
        const row = document.createElement('tr');
        row.className = 'search-result-row';
        row.setAttribute('data-type', 'box');
        row.setAttribute('data-id', box.id);

        const statusClass = this.getStatusClass(box.state);
        const retentionWarning = this.checkRetentionWarning(box.destruction_due_date);

        row.innerHTML = `
            <td class="select-cell">
                <input type="checkbox" class="item-select" value="${box.id}" data-type="box">
            </td>
            <td class="item-info">
                <div class="item-name">
                    <strong>${this.escapeHtml(box.name)}</strong>
                    <small class="text-muted d-block">${this.escapeHtml(box.barcode || '')}</small>
                </div>
            </td>
            <td class="item-description">
                ${this.escapeHtml(box.description || '')}
            </td>
            <td class="item-location">
                ${box.location_id ? this.escapeHtml(box.location_id[1]) : 'N/A'}
            </td>
            <td class="item-status">
                <span class="badge badge-${statusClass}">${this.escapeHtml(box.state)}</span>
                ${retentionWarning ? '<i class="fa fa-exclamation-triangle text-warning ml-1" title="Retention expiring soon"></i>' : ''}
            </td>
            <td class="item-count">
                ${box.document_count || 0} docs
            </td>
            <td class="item-actions">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-sm" onclick="viewItem('box', ${box.id})">
                        <i class="fa fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="editItem('box', ${box.id})">
                        <i class="fa fa-edit"></i>
                    </button>
                </div>
            </td>
        `;

        return row;
    }

    createDocumentRow(doc) {
        const row = document.createElement('tr');
        row.className = 'search-result-row document-row';
        row.setAttribute('data-type', 'document');
        row.setAttribute('data-id', doc.id);

        const statusClass = this.getStatusClass(doc.state);

        row.innerHTML = `
            <td class="select-cell">
                <input type="checkbox" class="item-select" value="${doc.id}" data-type="document">
            </td>
            <td class="item-info">
                <div class="item-name">
                    <i class="fa fa-file-text-o text-info mr-1"></i>
                    <strong>${this.escapeHtml(doc.name)}</strong>
                    <small class="text-muted d-block">Document</small>
                </div>
            </td>
            <td class="item-description">
                ${doc.document_type ? this.escapeHtml(doc.document_type[1]) : ''}
            </td>
            <td class="item-location">
                ${doc.box_id ? `Box: ${this.escapeHtml(doc.box_id[1])}` : 'N/A'}
            </td>
            <td class="item-status">
                <span class="badge badge-${statusClass}">${this.escapeHtml(doc.state)}</span>
            </td>
            <td class="item-count">
                -
            </td>
            <td class="item-actions">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-sm" onclick="viewItem('document', ${doc.id})">
                        <i class="fa fa-eye"></i>
                    </button>
                </div>
            </td>
        `;

        return row;
    }

    updateAutocomplete(query) {
        const suggestions = this.generateSuggestions(query);
        this.showAutocomplete(suggestions);
    }

    generateSuggestions(query) {
        const allSuggestions = [
            ...this.commonQueries,
            ...this.searchHistory.slice(-10).reverse()
        ];

        return allSuggestions
            .filter(suggestion =>
                suggestion.toLowerCase().includes(query.toLowerCase()) &&
                suggestion.toLowerCase() !== query.toLowerCase()
            )
            .slice(0, 8);
    }

    showAutocomplete(suggestions) {
        const dropdown = document.getElementById('search_autocomplete');
        if (!dropdown || suggestions.length === 0) {
            this.hideAutocomplete();
            return;
        }

        dropdown.innerHTML = suggestions.map(suggestion =>
            `<div class="suggestion-item">
                <i class="fa fa-search text-muted mr-2"></i>
                ${this.escapeHtml(suggestion)}
            </div>`
        ).join('');

        dropdown.style.display = 'block';
    }

    hideAutocomplete() {
        const dropdown = document.getElementById('search_autocomplete');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    showSearchSuggestions() {
        if (this.searchHistory.length > 0) {
            const recentSearches = this.searchHistory.slice(-5).reverse();
            this.showAutocomplete(recentSearches);
        }
    }

    addToSearchHistory(query) {
        if (!query || query.length < 2) return;

        // Remove existing instance
        const index = this.searchHistory.indexOf(query);
        if (index > -1) {
            this.searchHistory.splice(index, 1);
        }

        // Add to beginning
        this.searchHistory.unshift(query);

        // Limit history size
        if (this.searchHistory.length > 50) {
            this.searchHistory = this.searchHistory.slice(0, 50);
        }

        // Save to localStorage
        localStorage.setItem('portal_search_history', JSON.stringify(this.searchHistory));
    }

    async loadSearchSuggestions() {
        try {
            // Load popular searches from server
            const popularSearches = await rpc('/my/inventory/popular_searches', {});
            if (popularSearches && popularSearches.length > 0) {
                this.commonQueries = [...this.commonQueries, ...popularSearches];
            }
        } catch (error) {
            console.log('Could not load popular searches:', error);
        }
    }

    showLoadingState() {
        const loadingElement = document.getElementById('search_loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }

        const tableBody = document.querySelector('#inventory_table tbody');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center"><i class="fa fa-spinner fa-spin"></i> Searching...</td></tr>';
        }
    }

    hideLoadingState() {
        const loadingElement = document.getElementById('search_loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showErrorState(message) {
        const tableBody = document.querySelector('#inventory_table tbody');
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-danger"><i class="fa fa-exclamation-triangle"></i> ${message}</td></tr>`;
        }
    }

    showNoResultsMessage() {
        const tableBody = document.querySelector('#inventory_table tbody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4">
                        <i class="fa fa-search fa-2x text-muted mb-2"></i>
                        <h5 class="text-muted">No results found</h5>
                        <p class="text-muted">Try adjusting your search terms or filters</p>
                    </td>
                </tr>
            `;
        }
    }

    updateResultCount(count) {
        const countElement = document.getElementById('result_count');
        if (countElement && countElement.textContent !== undefined) {
            countElement.textContent = `${count} item${count !== 1 ? 's' : ''} found`;
        }
    }

    clearResults() {
        const tableBody = document.querySelector('#inventory_table tbody');
        if (tableBody) {
            tableBody.innerHTML = '';
        }
        this.updateResultCount(0);
        this.hideAutocomplete();
    }

    highlightActiveFilter(element) {
        // Remove active class from all quick filters
        document.querySelectorAll('.quick-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked filter
        element.classList.add('active');
    }

    getStatusClass(state) {
        const statusClasses = {
            'active': 'success',
            'archived': 'secondary',
            'destroyed': 'danger',
            'pending_pickup': 'warning',
            'pending_destruction': 'warning',
            'checkout': 'info'
        };
        return statusClasses[state] || 'secondary';
    }

    checkRetentionWarning(retentionDate) {
        if (!retentionDate) return false;

        const retention = new Date(retentionDate);
        const warning = new Date();
        warning.setDate(warning.getDate() + 30);

        return retention <= warning;
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return String(text || '').replace(/[&<>"']/g, m => map[m]);
    }

    async performAdvancedSearch() {
        const formData = new FormData(document.getElementById('advanced_search_form'));
        const searchParams = {};

        for (let [key, value] of formData.entries()) {
            if (value) searchParams[key] = value;
        }

        this.showLoadingState();

        try {
            const results = await rpc('/my/inventory/advanced_search', searchParams);
            this.updateSearchResults(results.boxes || [], results.documents || []);
            this.hideLoadingState();
        } catch (error) {
            console.error('Advanced search error:', error);
            this.showErrorState('Advanced search failed. Please try again.');
            this.hideLoadingState();
        }
    }
}

// Global functions for template access
window.portalSearch = {
    searchInstance: null,

    init() {
        if (!this.searchInstance) {
            this.searchInstance = new PortalInventorySearch();
        }
        return this.searchInstance;
    },

    search(query) {
        if (this.searchInstance) {
            this.searchInstance.performSearch(query, true);
        }
    },

    filter() {
        if (this.searchInstance) {
            this.searchInstance.applyFilters();
        }
    },

    clearSearch() {
        const searchInput = document.getElementById('global_search');
        if (searchInput) {
            searchInput.value = '';
        }
        if (this.searchInstance) {
            this.searchInstance.clearResults();
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.portalSearch.init();
});

// Template helper functions
function searchInventory(query) {
    window.portalSearch.search(query);
}

function filterInventory() {
    window.portalSearch.filter();
}

function clearInventorySearch() {
    window.portalSearch.clearSearch();
}

function viewItem(type, id) {
    window.location.href = `/my/${type}s/${id}`;
}

function editItem(type, id) {
    window.location.href = `/my/${type}s/${id}/edit`;
}

console.log('Portal Inventory Search module loaded successfully');
