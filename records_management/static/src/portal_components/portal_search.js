/** @odoo-module **/
/**
 * Modern Owl Portal Search Component
 * Following Odoo 19 best practices for portal/website Owl components
 */

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PortalSearchComponent extends Component {
    static template = "records_management.PortalSearchComponent";
    static props = {
        placeholder: { type: String, optional: true },
        maxSuggestions: { type: Number, optional: true },
        showAdvanced: { type: Boolean, optional: true },
    };

    setup() {
        this.searchRef = useRef("searchInput");
        this.searchTimeout = null;
        
        this.state = useState({
            searchQuery: "",
            suggestions: [],
            showAdvanced: this.props.showAdvanced || false,
            filters: {
                documentType: "",
                dateRange: "",
                status: "",
            },
            recentSearches: this.getRecentSearches(),
            isLoading: false,
        });

        onMounted(() => {
            // Focus search input on mount
            if (this.searchRef.el) {
                this.searchRef.el.focus();
            }
        });
    }

    /**
     * Handle search input with debouncing
     */
    async onSearchInput(event) {
        const query = event.target.value.trim();
        this.state.searchQuery = query;

        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Hide suggestions if query is too short
        if (query.length < 2) {
            this.state.suggestions = [];
            return;
        }

        // Debounce search requests
        this.searchTimeout = setTimeout(async () => {
            await this.fetchSuggestions(query);
        }, 300);
    }

    /**
     * Fetch search suggestions from backend
     */
    async fetchSuggestions(query) {
        try {
            this.state.isLoading = true;
            
            const result = await rpc("/my/records/search/suggestions", {
                query: query,
                filters: this.state.filters,
                max_results: this.props.maxSuggestions || 8,
            });

            this.state.suggestions = result.suggestions || [];
        } catch (error) {
            console.error("Error fetching search suggestions:", error);
            this.state.suggestions = [];
        } finally {
            this.state.isLoading = false;
        }
    }

    /**
     * Perform main search
     */
    async performSearch() {
        const query = this.state.searchQuery.trim();
        if (!query) return;

        // Save to recent searches
        this.saveRecentSearch(query);

        // Navigate to search results
        const params = new URLSearchParams({
            q: query,
            ...this.state.filters,
        });

        window.location.href = `/my/records/search?${params.toString()}`;
    }

    /**
     * Select a suggestion
     */
    selectSuggestion(event, suggestion) {
        event.preventDefault();
        
        this.state.searchQuery = suggestion.name;
        this.state.suggestions = [];

        // Navigate directly to the suggestion if it has a URL
        if (suggestion.url) {
            window.location.href = suggestion.url;
        } else {
            this.performSearch();
        }
    }

    /**
     * Toggle advanced search panel
     */
    toggleAdvanced() {
        this.state.showAdvanced = !this.state.showAdvanced;
    }

    /**
     * Apply advanced search filters
     */
    async applyFilters() {
        if (this.state.searchQuery.trim()) {
            await this.fetchSuggestions(this.state.searchQuery);
        }
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        this.state.filters = {
            documentType: "",
            dateRange: "",
            status: "",
        };
        
        if (this.state.searchQuery.trim()) {
            this.fetchSuggestions(this.state.searchQuery);
        }
    }

    /**
     * Use a recent search
     */
    useRecentSearch(search) {
        this.state.searchQuery = search;
        this.performSearch();
    }

    /**
     * Get recent searches from localStorage
     */
    getRecentSearches() {
        try {
            const stored = localStorage.getItem("portal_recent_searches");
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            return [];
        }
    }

    /**
     * Save search to recent searches
     */
    saveRecentSearch(query) {
        try {
            let recent = this.getRecentSearches();
            
            // Remove if already exists
            recent = recent.filter(item => item !== query);
            
            // Add to beginning
            recent.unshift(query);
            
            // Keep only last 5 searches
            recent = recent.slice(0, 5);
            
            localStorage.setItem("portal_recent_searches", JSON.stringify(recent));
            this.state.recentSearches = recent;
        } catch (error) {
            console.error("Error saving recent search:", error);
        }
    }
}

// Register in public_components registry for portal/website usage
registry.category("public_components").add("records_management.PortalSearchComponent", PortalSearchComponent);
