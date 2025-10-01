/** @odoo-module **/
/**
 * Modern Owl Portal Document Center Component
 * Provides interactive document management with real-time filtering and search
 */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PortalDocumentCenter extends Component {
    static template = "records_management.PortalDocumentCenter";
    static props = {
        partnerId: { type: Number, optional: true },
        initialTab: { type: String, optional: true },
        pageSize: { type: Number, optional: true },
    };

    setup() {
        this.searchTimeout = null;
        this.refreshInterval = null;
        
        this.state = useState({
            activeTab: this.props.initialTab || 'all',
            viewMode: 'grid', // 'grid' or 'list'
            searchQuery: '',
            filters: {
                status: '',
                dateRange: '',
            },
            sortBy: 'date_desc',
            currentPage: 1,
            pageSize: this.props.pageSize || 12,
            totalPages: 1,
            isLoading: false,
            documents: [],
            filteredDocuments: [],
            stats: {
                total: 0,
                invoices: 0,
                quotes: 0,
                certificates: 0,
                communications: 0,
            },
        });

        onMounted(async () => {
            await this.loadDocuments();
            this.setupAutoRefresh();
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
        });
    }

    /**
     * Load documents from backend
     */
    async loadDocuments() {
        try {
            this.state.isLoading = true;

            const result = await rpc("/my/docs/load_documents", {
                tab: this.state.activeTab,
                search: this.state.searchQuery,
                filters: this.state.filters,
                sort_by: this.state.sortBy,
                page: this.state.currentPage,
                page_size: this.state.pageSize,
                partner_id: this.props.partnerId,
            });

            if (result.success) {
                this.state.documents = result.documents || [];
                this.state.stats = result.stats || this.state.stats;
                this.state.totalPages = Math.ceil((result.total_count || 0) / this.state.pageSize);
                this.applyClientSideFiltering();
            }
        } catch (error) {
            console.error("Error loading documents:", error);
            this.showNotification("Error loading documents", "error");
        } finally {
            this.state.isLoading = false;
        }
    }

    /**
     * Apply client-side filtering and search
     */
    applyClientSideFiltering() {
        let filtered = [...this.state.documents];

        // Apply tab filter
        if (this.state.activeTab !== 'all') {
            filtered = filtered.filter(doc => doc.type === this.state.activeTab);
        }

        // Apply search filter
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            filtered = filtered.filter(doc => 
                doc.name.toLowerCase().includes(query) ||
                (doc.description && doc.description.toLowerCase().includes(query))
            );
        }

        // Apply status filter
        if (this.state.filters.status) {
            filtered = filtered.filter(doc => doc.status === this.state.filters.status);
        }

        // Apply date range filter
        if (this.state.filters.dateRange) {
            const now = new Date();
            const filterDate = new Date();
            
            switch (this.state.filters.dateRange) {
                case 'week':
                    filterDate.setDate(now.getDate() - 7);
                    break;
                case 'month':
                    filterDate.setMonth(now.getMonth() - 1);
                    break;
                case 'quarter':
                    filterDate.setMonth(now.getMonth() - 3);
                    break;
                case 'year':
                    filterDate.setFullYear(now.getFullYear() - 1);
                    break;
            }
            
            filtered = filtered.filter(doc => new Date(doc.date) >= filterDate);
        }

        // Apply sorting
        filtered.sort((a, b) => {
            switch (this.state.sortBy) {
                case 'date_desc':
                    return new Date(b.date) - new Date(a.date);
                case 'date_asc':
                    return new Date(a.date) - new Date(b.date);
                case 'name_asc':
                    return a.name.localeCompare(b.name);
                case 'name_desc':
                    return b.name.localeCompare(a.name);
                default:
                    return 0;
            }
        });

        this.state.filteredDocuments = filtered;
    }

    /**
     * Set active tab
     */
    async setActiveTab(tab) {
        this.state.activeTab = tab;
        this.state.currentPage = 1;
        await this.loadDocuments();
    }

    /**
     * Set view mode
     */
    setViewMode(mode) {
        this.state.viewMode = mode;
        // Save preference to localStorage
        localStorage.setItem('portal_doc_view_mode', mode);
    }

    /**
     * Handle search input with debouncing
     */
    onSearchInput(event) {
        const query = event.target.value;
        this.state.searchQuery = query;

        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        this.searchTimeout = setTimeout(() => {
            this.applyClientSideFiltering();
        }, 300);
    }

    /**
     * Perform search
     */
    async performSearch() {
        this.state.currentPage = 1;
        await this.loadDocuments();
    }

    /**
     * Clear all filters
     */
    async clearFilters() {
        this.state.searchQuery = '';
        this.state.filters = {
            status: '',
            dateRange: '',
        };
        this.state.currentPage = 1;
        await this.loadDocuments();
    }

    /**
     * Go to specific page
     */
    async goToPage(page) {
        if (page >= 1 && page <= this.state.totalPages) {
            this.state.currentPage = page;
            await this.loadDocuments();
        }
    }

    /**
     * View document
     */
    async viewDocument(doc) {
        if (doc.url) {
            window.open(doc.url, '_blank');
        } else {
            this.showNotification("Document URL not available", "warning");
        }
    }

    /**
     * Download document
     */
    async downloadDocument(doc) {
        try {
            const result = await rpc("/my/docs/download", {
                doc_id: doc.id,
                doc_type: doc.type,
            });

            if (result.success && result.download_url) {
                window.open(result.download_url, '_blank');
            } else {
                this.showNotification(result.error || "Download failed", "error");
            }
        } catch (error) {
            console.error("Download error:", error);
            this.showNotification("Error downloading document", "error");
        }
    }

    /**
     * Share document
     */
    async shareDocument(doc) {
        try {
            const result = await rpc("/my/docs/share", {
                doc_id: doc.id,
                doc_type: doc.type,
            });

            if (result.success && result.share_url) {
                // Copy to clipboard
                await navigator.clipboard.writeText(result.share_url);
                this.showNotification("Share link copied to clipboard", "success");
            } else {
                this.showNotification(result.error || "Share failed", "error");
            }
        } catch (error) {
            console.error("Share error:", error);
            this.showNotification("Error sharing document", "error");
        }
    }

    /**
     * Export all documents
     */
    async exportAllDocs() {
        if (!confirm('This will generate a comprehensive export of all your documents. Continue?')) {
            return;
        }

        try {
            const result = await rpc("/my/docs/export_all", {
                filters: this.state.filters,
                format: 'pdf', // or 'zip'
            });

            if (result.success && result.export_url) {
                window.open(result.export_url, '_blank');
                this.showNotification("Export started. Download will begin shortly.", "success");
            } else {
                this.showNotification(result.error || "Export failed", "error");
            }
        } catch (error) {
            console.error("Export error:", error);
            this.showNotification("Error exporting documents", "error");
        }
    }

    /**
     * Setup auto-refresh for real-time updates
     */
    setupAutoRefresh() {
        this.refreshInterval = setInterval(async () => {
            await this.checkForUpdates();
        }, 60000); // Check every minute
    }

    /**
     * Check for document updates
     */
    async checkForUpdates() {
        try {
            const result = await rpc("/my/docs/check_updates", {
                last_update: this.lastUpdateTime || new Date().toISOString(),
            });

            if (result.has_updates) {
                // Reload documents in background
                await this.loadDocuments();
                this.showNotification("Documents updated", "info");
            }

            this.lastUpdateTime = new Date().toISOString();
        } catch (error) {
            // Silent fail for background updates
            console.log("Background update check failed:", error);
        }
    }

    /**
     * Show notification message
     */
    showNotification(message, type = "info") {
        // Create and show notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;

        document.body.appendChild(notification);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Register in public_components registry for portal/website usage
registry.category("public_components").add("records_management.PortalDocumentCenter", PortalDocumentCenter);
