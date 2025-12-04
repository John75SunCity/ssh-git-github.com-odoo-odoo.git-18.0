/**
 * Portal Search Integration - Modernized Vanilla JS (Odoo 18+)
 * Customer portal search functionality with autocomplete suggestions
 * 
 * MODERNIZED: Converted from jQuery/AMD to vanilla JS IIFE
 * NO DEPENDENCIES: Pure vanilla JavaScript
 */
(function () {
    'use strict';

    /**
     * Debounce function for rate-limiting
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * JSON RPC call (for Odoo endpoints)
     */
    function rpcQuery(route, params) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', route, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            
            const csrfToken = document.querySelector('input[name="csrf_token"]');
            if (csrfToken) {
                xhr.setRequestHeader('X-CSRFToken', csrfToken.value);
            }
            
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        try {
                            const response = JSON.parse(xhr.responseText);
                            if (response.result) {
                                resolve(response.result);
                            } else if (response.error) {
                                reject(response.error);
                            } else {
                                resolve(response);
                            }
                        } catch (e) {
                            reject(e);
                        }
                    } else {
                        reject(new Error(xhr.statusText));
                    }
                }
            };
            
            xhr.send(JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: Math.floor(Math.random() * 1000000)
            }));
        });
    }

    // ============================================================================
    // PORTAL SEARCH WIDGET
    // ============================================================================

    const PortalSearchWidget = {
        init: function () {
            const container = document.querySelector('.portal-search-container');
            if (!container) return;

            this.container = container;
            this.searchInput = container.querySelector('.portal-search-input');
            this.suggestionsBox = container.querySelector('.search-suggestions');
            this.searchForm = container.querySelector('.portal-search-form');

            if (!this.searchInput) return;

            this._bindEvents();
        },

        _bindEvents: function () {
            // Search input with debouncing
            this.searchInput.addEventListener('input', debounce(this._onSearchInput.bind(this), 300));

            // Suggestion clicks (using event delegation)
            if (this.suggestionsBox) {
                this.suggestionsBox.addEventListener('click', this._onSelectSuggestion.bind(this));
            }

            // Form submission
            if (this.searchForm) {
                this.searchForm.addEventListener('submit', this._onSearchSubmit.bind(this));
            }

            // Hide suggestions when clicking outside
            document.addEventListener('click', (ev) => {
                if (!this.container.contains(ev.target)) {
                    this._hideSuggestions();
                }
            });
        },

        _onSearchInput: function (ev) {
            const query = ev.target.value.trim();

            if (query.length >= 2) {
                this._performPortalSearch(query);
            } else {
                this._hideSuggestions();
            }
        },

        _performPortalSearch: function (query) {
            rpcQuery('/my/records/search', { query: query })
                .then(result => {
                    this._showPortalSuggestions(result);
                })
                .catch(error => {
                    console.error('Portal search error:', error);
                    this._hideSuggestions();
                });
        },

        _showPortalSuggestions: function (result) {
            if (!this.suggestionsBox) return;

            this.suggestionsBox.innerHTML = '';

            const suggestions = result.suggestions || result.recommendations || [];

            if (suggestions.length === 0) {
                this._hideSuggestions();
                return;
            }

            suggestions.forEach(suggestion => {
                const item = document.createElement('div');
                item.className = 'search-suggestion p-2 border-bottom';
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <strong>${this._escapeHtml(suggestion.name)}</strong><br>
                    <small class="text-muted">${this._escapeHtml(suggestion.description || '')}</small>
                `;
                item.dataset.suggestionName = suggestion.name;
                item.dataset.suggestionUrl = suggestion.url || '';
                this.suggestionsBox.appendChild(item);
            });

            this.suggestionsBox.style.display = 'block';
        },

        _hideSuggestions: function () {
            if (this.suggestionsBox) {
                this.suggestionsBox.style.display = 'none';
            }
        },

        _onSelectSuggestion: function (ev) {
            const suggestionItem = ev.target.closest('.search-suggestion');
            if (!suggestionItem) return;

            const name = suggestionItem.dataset.suggestionName;
            const url = suggestionItem.dataset.suggestionUrl;

            if (this.searchInput) {
                this.searchInput.value = name;
            }

            this._hideSuggestions();

            // If suggestion has a URL, navigate to it
            if (url) {
                window.location.href = url;
            }
        },

        _onSearchSubmit: function (ev) {
            ev.preventDefault();
            const query = this.searchInput ? this.searchInput.value.trim() : '';

            if (query) {
                window.location.href = '/my/records/search?q=' + encodeURIComponent(query);
            }
        },

        _escapeHtml: function (text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // ============================================================================
    // INITIALIZATION
    // ============================================================================

    function initPortalSearch() {
        PortalSearchWidget.init();
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPortalSearch);
    } else {
        initPortalSearch();
    }

    // Export for global access if needed
    window.PortalSearchWidget = PortalSearchWidget;

})();
