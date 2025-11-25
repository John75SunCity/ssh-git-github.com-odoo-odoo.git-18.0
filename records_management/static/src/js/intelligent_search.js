/** @odoo-module **/
/**
 * Advanced Intelligent Search Widget for Records Management
 * Full-featured inventory lookup tool with real-time search capabilities
 *
 * Features:
 * - Container number auto-complete with customer filtering
 * - File search with content indexing
 * - Real-time suggestions with debouncing
 * - Keyboard navigation support
 * - Advanced filtering and search algorithms
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

console.log("Advanced Intelligent Search module loading...");

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Safely extract partner ID from record data
 */
function safeGetPartnerId(record) {
    try {
        if (!record || !record.data || !record.data.partner_id) {
            return null;
        }
        const partnerRaw = record.data.partner_id;

        // Many2one can be: {data:{id:..}}, number, or [id, "name"]
        if (partnerRaw && partnerRaw.data && partnerRaw.data.id) {
            return partnerRaw.data.id;
        }
        if (typeof partnerRaw === "number") {
            return partnerRaw;
        }
        if (Array.isArray(partnerRaw) && partnerRaw.length) {
            return partnerRaw[0];
        }
    } catch (err) {
        console.warn("[IntelligentSearch] Failed to extract partner id", err);
    }
    return null;
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Highlight matching text in search results
 */
function highlightMatch(text, query) {
    if (!query || !text) return text;
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<strong>$1</strong>');
}

// ============================================================================
// CONTAINER SEARCH WIDGET - Advanced inventory lookup
// ============================================================================

class ContainerSearchWidget extends Component {
    static template = `
        <div class="o_container_search position-relative">
            <div class="input-group">
                <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Search containers by number, customer, or location..."
                    t-att-value="state.query"
                    t-on-input="onSearchInput" 
                    t-on-keydown="onKeyDown"
                    t-on-focus="onFocus"
                    t-on-blur="onBlur"
                />
                <button class="btn btn-outline-secondary" type="button" t-on-click="onAdvancedSearch">
                    <i class="fa fa-search"/>
                </button>
            </div>
            
            <!-- Search Suggestions Dropdown -->
            <div t-if="state.showSuggestions and state.suggestions.length" 
                 class="dropdown-menu show position-absolute w-100" 
                 style="max-height: 300px; overflow-y: auto; z-index: 1050;">
                
                <div t-foreach="state.suggestions" t-as="suggestion" t-key="suggestion.id"
                     class="dropdown-item cursor-pointer d-flex justify-content-between align-items-center"
                     t-att-class="{'active': suggestion_index === state.selectedIndex}"
                     t-on-click="() => this.onSelectSuggestion(suggestion)"
                     t-on-mouseenter="() => this.state.selectedIndex = suggestion_index">
                    
                    <div class="flex-grow-1">
                        <div class="fw-bold" t-esc="suggestion.container_number"/>
                        <small class="text-muted">
                            <span t-esc="suggestion.customer_name"/> • 
                            <span t-esc="suggestion.location_name"/>
                            <span t-if="suggestion.document_count"> • 
                                <span t-esc="suggestion.document_count"/> docs
                            </span>
                        </small>
                    </div>
                    
                    <div class="text-end">
                        <span t-if="suggestion.status" 
                              class="badge"
                              t-att-class="'badge-' + (suggestion.status === 'active' ? 'success' : 'secondary')">
                            <span t-esc="suggestion.status"/>
                        </span>
                    </div>
                </div>
                
                <!-- No results message -->
                <div t-if="state.searchPerformed and !state.suggestions.length" 
                     class="dropdown-item-text text-muted">
                    <i class="fa fa-info-circle"/> No containers found for "<span t-esc="state.query"/>"
                </div>
                
                <!-- Loading indicator -->
                <div t-if="state.loading" class="dropdown-item-text text-center">
                    <i class="fa fa-spinner fa-spin"/> Searching...
                </div>
            </div>
            
            <!-- Advanced Search Panel (expandable) -->
            <div t-if="state.showAdvanced" class="card mt-2 border-light">
                <div class="card-body p-3">
                    <h6 class="card-title mb-3">Advanced Container Search</h6>
                    
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">Customer</label>
                            <select class="form-select form-select-sm" t-model="state.filters.customer_id">
                                <option value="">All Customers</option>
                                <option t-foreach="state.customers" t-as="customer" 
                                        t-key="customer.id" t-att-value="customer.id">
                                    <span t-esc="customer.name"/>
                                </option>
                            </select>
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label">Location</label>
                            <select class="form-select form-select-sm" t-model="state.filters.location_id">
                                <option value="">All Locations</option>
                                <option t-foreach="state.locations" t-as="location" 
                                        t-key="location.id" t-att-value="location.id">
                                    <span t-esc="location.name"/>
                                </option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <label class="form-label">Status</label>
                            <select class="form-select form-select-sm" t-model="state.filters.status">
                                <option value="">All Statuses</option>
                                <option value="active">Active</option>
                                <option value="stored">Stored</option>
                                <option value="archived">Archived</option>
                            </select>
                        </div>
                        
                        <div class="col-md-6">
                            <label class="form-label">Document Type</label>
                            <select class="form-select form-select-sm" t-model="state.filters.document_type">
                                <option value="">All Types</option>
                                <option t-foreach="state.documentTypes" t-as="docType" 
                                        t-key="docType.id" t-att-value="docType.id">
                                    <span t-esc="docType.name"/>
                                </option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mt-3 d-flex gap-2">
                        <button class="btn btn-primary btn-sm" t-on-click="onApplyFilters">
                            <i class="fa fa-search"/> Apply Filters
                        </button>
                        <button class="btn btn-secondary btn-sm" t-on-click="onClearFilters">
                            <i class="fa fa-times"/> Clear
                        </button>
                        <button class="btn btn-outline-secondary btn-sm ms-auto" t-on-click="onToggleAdvanced">
                            <i class="fa fa-times"/> Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            query: this.props.value || "",
            suggestions: [],
            selectedIndex: -1,
            showSuggestions: false,
            showAdvanced: false,
            loading: false,
            searchPerformed: false,
            customers: [],
            locations: [],
            documentTypes: [],
            filters: {
                customer_id: "",
                location_id: "",
                status: "",
                document_type: ""
            }
        });

        this.orm = useService("orm");
        this.debouncedSearch = debounce(this.performSearch.bind(this), 300);
    }

    /**
     * Handle search input with debouncing
     */
    onSearchInput(event) {
        const query = event.target.value;
        this.state.query = query;

        if (query.trim().length >= 2) {
            this.state.loading = true;
            this.state.showSuggestions = true;
            this.debouncedSearch(query.trim());
        } else {
            this.hideSuggestions();
        }
    }

    /**
     * Perform intelligent search with multiple criteria
     */
    async performSearch(query) {
        try {
            const customer_id = safeGetPartnerId(this.props.record);

            const searchParams = {
                query: query,
                limit: 15,
                customer_id: customer_id,
                filters: this.state.filters,
                search_fields: ['container_number', 'barcode', 'description', 'customer_name', 'location_name'],
                include_metadata: true
            };

            // Use ORM service to call model method directly (Odoo 18 pattern)
            const result = await this.orm.call(
                'records.container',
                'search_containers_intelligent',
                [],
                searchParams
            );

            this.state.suggestions = result.suggestions || [];
            this.state.searchPerformed = true;
            this.state.loading = false;
            this.state.selectedIndex = -1;

            // Update filter options if provided
            if (result.filter_options) {
                this.state.customers = result.filter_options.customers || [];
                this.state.locations = result.filter_options.locations || [];
                this.state.documentTypes = result.filter_options.document_types || [];
            }

        } catch (error) {
            console.error("Container search error:", error);
            this.state.loading = false;
            this.state.suggestions = [];
            this.state.searchPerformed = true;
        }
    }

    /**
     * Handle suggestion selection
     */
    onSelectSuggestion(suggestion) {
        if (!suggestion) return;

        this.state.query = suggestion.container_number;
        this.props.update(suggestion.container_number);
        this.hideSuggestions();

        // Trigger additional actions if needed
        if (this.props.onContainerSelected) {
            this.props.onContainerSelected(suggestion);
        }
    }

    /**
     * Keyboard navigation support
     */
    onKeyDown(event) {
        if (!this.state.showSuggestions || !this.state.suggestions.length) {
            return;
        }

        switch (event.keyCode) {
            case 38: // Up arrow
                event.preventDefault();
                this.state.selectedIndex = Math.max(-1, this.state.selectedIndex - 1);
                break;

            case 40: // Down arrow
                event.preventDefault();
                this.state.selectedIndex = Math.min(
                    this.state.suggestions.length - 1,
                    this.state.selectedIndex + 1
                );
                break;

            case 13: // Enter
                event.preventDefault();
                if (this.state.selectedIndex >= 0) {
                    const suggestion = this.state.suggestions[this.state.selectedIndex];
                    this.onSelectSuggestion(suggestion);
                }
                break;

            case 27: // Escape
                this.hideSuggestions();
                break;
        }
    }

    /**
     * Show suggestions on focus
     */
    onFocus() {
        if (this.state.suggestions.length > 0) {
            this.state.showSuggestions = true;
        }
    }

    /**
     * Hide suggestions on blur (with delay)
     */
    onBlur() {
        // Small delay to allow click on suggestions
        setTimeout(() => {
            this.state.showSuggestions = false;
        }, 150);
    }

    /**
     * Toggle advanced search panel
     */
    onAdvancedSearch() {
        this.onToggleAdvanced();
    }

    onToggleAdvanced() {
        this.state.showAdvanced = !this.state.showAdvanced;

        // Load filter options when opening advanced search
        if (this.state.showAdvanced && this.state.customers.length === 0) {
            this.loadFilterOptions();
        }
    }

    /**
     * Load filter options for advanced search
     */
    async loadFilterOptions() {
        try {
            const result = await this.rpc("/records/search/filter-options", {});
            this.state.customers = result.customers || [];
            this.state.locations = result.locations || [];
            this.state.documentTypes = result.document_types || [];
        } catch (error) {
            console.error("Failed to load filter options:", error);
        }
    }

    /**
     * Apply advanced filters
     */
    onApplyFilters() {
        if (this.state.query.trim()) {
            this.performSearch(this.state.query.trim());
        }
    }

    /**
     * Clear all filters
     */
    onClearFilters() {
        this.state.filters = {
            customer_id: "",
            location_id: "",
            status: "",
            document_type: ""
        };
        this.onApplyFilters();
    }

    /**
     * Hide suggestions dropdown
     */
    hideSuggestions() {
        this.state.showSuggestions = false;
        this.state.selectedIndex = -1;
    }
}

// ============================================================================
// FILE SEARCH WIDGET - Document content search
// ============================================================================

class FileSearchWidget extends Component {
    static template = `
        <div class="o_file_search position-relative">
            <div class="input-group">
                <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Search files by name, content, or metadata..."
                    t-att-value="state.query"
                    t-on-input="onSearchInput" 
                    t-on-keydown="onKeyDown"
                />
                <button class="btn btn-outline-secondary" type="button" t-on-click="onFullTextSearch">
                    <i class="fa fa-file-text-o"/>
                </button>
            </div>
            
            <!-- File Search Results -->
            <div t-if="state.showResults and state.results.length" 
                 class="dropdown-menu show position-absolute w-100" 
                 style="max-height: 400px; overflow-y: auto; z-index: 1050;">
                
                <div t-foreach="state.results" t-as="result" t-key="result.id"
                     class="dropdown-item cursor-pointer"
                     t-att-class="{'active': result_index === state.selectedIndex}"
                     t-on-click="() => this.onSelectFile(result)">
                    
                    <div class="d-flex align-items-start">
                        <i class="fa fa-file-o mt-1 me-2" t-att-class="'text-' + result.file_type_color"/>
                        
                        <div class="flex-grow-1">
                            <div class="fw-bold" t-esc="result.filename"/>
                            <small class="text-muted">
                                <span t-esc="result.container_number"/> • 
                                <span t-esc="result.file_size"/> • 
                                <span t-esc="result.modified_date"/>
                            </small>
                            
                            <!-- Content preview -->
                            <div t-if="result.content_preview" class="small text-secondary mt-1">
                                <t t-raw="result.content_preview"/>
                            </div>
                        </div>
                        
                        <div class="text-end">
                            <span t-if="result.relevance_score" class="badge badge-light">
                                <span t-esc="Math.round(result.relevance_score * 100)"/>%
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- No results -->
                <div t-if="state.searchPerformed and !state.results.length" 
                     class="dropdown-item-text text-muted">
                    <i class="fa fa-info-circle"/> No files found matching your search
                </div>
            </div>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.state = useState({
            query: this.props.value || "",
            results: [],
            selectedIndex: -1,
            showResults: false,
            searchPerformed: false,
            loading: false
        });

        this.orm = useService("orm");
        this.debouncedSearch = debounce(this.performFileSearch.bind(this), 500);
    }

    /**
     * Handle file search input
     */
    onSearchInput(event) {
        const query = event.target.value;
        this.state.query = query;

        if (query.trim().length >= 3) {
            this.state.loading = true;
            this.state.showResults = true;
            this.debouncedSearch(query.trim());
        } else {
            this.hideResults();
        }
    }

    /**
     * Perform file search with content indexing
     */
    async performFileSearch(query) {
        try {
            const customer_id = safeGetPartnerId(this.props.record);

            const searchParams = {
                query: query,
                limit: 20,
                customer_id: customer_id,
                search_type: 'files',
                include_content: true,
                file_types: ['pdf', 'doc', 'docx', 'txt', 'image'],
                relevance_threshold: 0.3
            };

            // Use ORM service to call model method directly (Odoo 18 pattern)
            const result = await this.orm.call(
                'records.file.folder',
                'search_files_intelligent',
                [],
                searchParams
            );

            this.state.results = result.files || [];
            this.state.searchPerformed = true;
            this.state.loading = false;
            this.state.selectedIndex = -1;

        } catch (error) {
            console.error("File search error:", error);
            this.state.loading = false;
            this.state.results = [];
            this.state.searchPerformed = true;
        }
    }

    /**
     * Handle file selection
     */
    onSelectFile(file) {
        if (!file) return;

        this.props.update(file.filename);
        this.hideResults();

        // Open file preview or download
        if (this.props.onFileSelected) {
            this.props.onFileSelected(file);
        }
    }

    /**
     * Full-text search mode
     */
    onFullTextSearch() {
        if (this.state.query.trim()) {
            // Switch to full-text search mode
            this.performFileSearch(this.state.query.trim(), 'fulltext');
        }
    }

    /**
     * Keyboard navigation
     */
    onKeyDown(event) {
        if (!this.state.showResults || !this.state.results.length) {
            return;
        }

        switch (event.keyCode) {
            case 38: // Up
                event.preventDefault();
                this.state.selectedIndex = Math.max(-1, this.state.selectedIndex - 1);
                break;
            case 40: // Down
                event.preventDefault();
                this.state.selectedIndex = Math.min(
                    this.state.results.length - 1,
                    this.state.selectedIndex + 1
                );
                break;
            case 13: // Enter
                event.preventDefault();
                if (this.state.selectedIndex >= 0) {
                    const file = this.state.results[this.state.selectedIndex];
                    this.onSelectFile(file);
                }
                break;
            case 27: // Escape
                this.hideResults();
                break;
        }
    }

    /**
     * Hide search results
     */
    hideResults() {
        this.state.showResults = false;
        this.state.selectedIndex = -1;
    }
}

// ============================================================================
// WIDGET REGISTRATION
// ============================================================================

// Register the field widgets with proper Odoo 19 registry pattern
registry.category("fields").add("container_search", {
    component: ContainerSearchWidget,
    displayName: "Container Search",
    supportedTypes: ["many2one", "char"],
});

registry.category("fields").add("file_search", {
    component: FileSearchWidget,
    displayName: "File Search",
    supportedTypes: ["many2one", "char"],
});

console.log("[IntelligentSearch] Advanced widgets registered successfully");

// Global namespace for external access
if (typeof window !== 'undefined') {
    window.records_management_search = {
        ContainerSearchWidget,
        FileSearchWidget,
        version: 'advanced',
        initialized: true
    };
}
