/** 
 * Document Center JavaScript
 * Handles filtering, searching, and interactions for the centralized document portal
 */

odoo.define('records_management.portal_docs', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var utils = require('web.utils');

    var _t = core._t;

    publicWidget.registry.PortalDocsCenter = publicWidget.Widget.extend({
        selector: '.o_portal_docs_center',
        events: {
            'click .nav-tabs a': '_onTabChange',
            'change input[data-invoice-id]': '_onPONumberUpdate',
            'click .btn-group button[onclick*="filter"]': '_onFilterClick',
        },

        /**
         * Initialize the document center
         */
        start: function () {
            this._super.apply(this, arguments);
            this._initializeFilters();
            this._loadRecentActivity();
            this._setupRealTimeUpdates();
            return Promise.resolve();
        },

        /**
         * Initialize filter functionality
         */
        _initializeFilters: function () {
            var self = this;
            
            // Store original table data for filtering
            this._storeOriginalData();
            
            // Setup search functionality for each tab
            this._setupTabSearch();
        },

        /**
         * Store original table data for filtering
         */
        _storeOriginalData: function () {
            var self = this;
            
            // Store invoice data
            this.originalInvoices = [];
            this.$('#invoices_table tbody tr').each(function () {
                var $row = $(this);
                self.originalInvoices.push({
                    element: $row.clone(),
                    status: $row.find('.badge').text().toLowerCase().trim(),
                    date: $row.find('td:nth-child(2)').text().trim(),
                    amount: parseFloat($row.find('td:nth-child(3)').text().replace(/[^\d.-]/g, '')) || 0
                });
            });

            // Store other data similarly
            this._storeQuoteData();
            this._storeCertificateData();
            this._storeCommunicationData();
        },

        /**
         * Store quote data for filtering
         */
        _storeQuoteData: function () {
            var self = this;
            this.originalQuotes = [];
            
            this.$('#quotes tbody tr').each(function () {
                var $row = $(this);
                self.originalQuotes.push({
                    element: $row.clone(),
                    status: $row.find('.badge').text().toLowerCase().trim(),
                    serviceType: $row.find('td:nth-child(3) .badge').text().toLowerCase().trim(),
                    validUntil: new Date($row.find('td:nth-child(6)').text().trim())
                });
            });
        },

        /**
         * Store certificate data for filtering
         */
        _storeCertificateData: function () {
            var self = this;
            this.originalCertificates = [];
            
            this.$('#certificates tbody tr').each(function () {
                var $row = $(this);
                self.originalCertificates.push({
                    element: $row.clone(),
                    type: $row.find('td:nth-child(3) .badge').text().toLowerCase().trim(),
                    method: $row.find('td:nth-child(4)').text().toLowerCase().trim(),
                    date: new Date($row.find('td:nth-child(2)').text().trim())
                });
            });
        },

        /**
         * Store communication data for filtering
         */
        _storeCommunicationData: function () {
            var self = this;
            this.originalCommunications = [];
            
            this.$('.communication-item').each(function () {
                var $item = $(this);
                self.originalCommunications.push({
                    element: $item.clone(),
                    type: $item.find('.badge').text().toLowerCase().trim(),
                    date: new Date($item.find('small .fa-clock-o').parent().text().trim()),
                    subject: $item.find('h6').text().toLowerCase().trim()
                });
            });
        },

        /**
         * Setup search functionality for each tab
         */
        _setupTabSearch: function () {
            var self = this;
            
            // Add search boxes to each tab
            this._addSearchBox('invoices', 'Search invoices...');
            this._addSearchBox('quotes', 'Search quotes...');
            this._addSearchBox('certificates', 'Search certificates...');
            this._addSearchBox('communications', 'Search communications...');
        },

        /**
         * Add search box to a specific tab
         */
        _addSearchBox: function (tabId, placeholder) {
            var self = this;
            var $tab = this.$('#' + tabId);
            var $searchContainer = $('<div class="mb-3"><input type="text" class="form-control" placeholder="' + placeholder + '" data-tab="' + tabId + '"></div>');
            
            $tab.find('h5').after($searchContainer);
            
            // Add search event handler
            $searchContainer.find('input').on('input', function () {
                self._performSearch($(this).val(), tabId);
            });
        },

        /**
         * Perform search within a specific tab
         */
        _performSearch: function (query, tabId) {
            var self = this;
            query = query.toLowerCase().trim();
            
            if (tabId === 'invoices') {
                this._searchInvoices(query);
            } else if (tabId === 'quotes') {
                this._searchQuotes(query);
            } else if (tabId === 'certificates') {
                this._searchCertificates(query);
            } else if (tabId === 'communications') {
                this._searchCommunications(query);
            }
        },

        /**
         * Search invoices
         */
        _searchInvoices: function (query) {
            var $tbody = this.$('#invoices_table tbody');
            $tbody.empty();
            
            this.originalInvoices.forEach(function (invoice) {
                var invoiceText = invoice.element.text().toLowerCase();
                if (!query || invoiceText.includes(query)) {
                    $tbody.append(invoice.element);
                }
            });
            
            this._updateResultCount('invoices', $tbody.find('tr').length);
        },

        /**
         * Search quotes
         */
        _searchQuotes: function (query) {
            var $tbody = this.$('#quotes tbody');
            $tbody.empty();
            
            this.originalQuotes.forEach(function (quote) {
                var quoteText = quote.element.text().toLowerCase();
                if (!query || quoteText.includes(query)) {
                    $tbody.append(quote.element);
                }
            });
            
            this._updateResultCount('quotes', $tbody.find('tr').length);
        },

        /**
         * Search certificates
         */
        _searchCertificates: function (query) {
            var $tbody = this.$('#certificates tbody');
            $tbody.empty();
            
            this.originalCertificates.forEach(function (cert) {
                var certText = cert.element.text().toLowerCase();
                if (!query || certText.includes(query)) {
                    $tbody.append(cert.element);
                }
            });
            
            this._updateResultCount('certificates', $tbody.find('tr').length);
        },

        /**
         * Search communications
         */
        _searchCommunications: function (query) {
            var $container = this.$('.communications-list');
            $container.empty();
            
            this.originalCommunications.forEach(function (comm) {
                var commText = comm.element.text().toLowerCase();
                if (!query || commText.includes(query)) {
                    $container.append(comm.element);
                }
            });
            
            this._updateResultCount('communications', $container.find('.communication-item').length);
        },

        /**
         * Update result count display
         */
        _updateResultCount: function (tabId, count) {
            var $tab = this.$('#' + tabId + '-tab');
            var tabText = $tab.text().split('(')[0].trim();
            $tab.text(tabText + ' (' + count + ')');
        },

        /**
         * Handle tab changes
         */
        _onTabChange: function (ev) {
            var $target = $(ev.currentTarget);
            var tabId = $target.attr('href').substring(1);
            
            // Load data for the tab if not already loaded
            this._loadTabData(tabId);
            
            // Update URL without page reload
            if (history.pushState) {
                var newUrl = window.location.pathname + '?tab=' + tabId;
                history.pushState(null, '', newUrl);
            }
        },

        /**
         * Load data for a specific tab
         */
        _loadTabData: function (tabId) {
            var self = this;
            
            if (this.loadedTabs && this.loadedTabs.includes(tabId)) {
                return Promise.resolve();
            }
            
            return rpc.query({
                route: '/my/docs/load_tab_data',
                params: {
                    tab: tabId,
                    csrf_token: core.csrf_token,
                }
            }).then(function (result) {
                if (result.success) {
                    self._updateTabContent(tabId, result.data);
                    self.loadedTabs = self.loadedTabs || [];
                    self.loadedTabs.push(tabId);
                }
            });
        },

        /**
         * Update tab content with new data
         */
        _updateTabContent: function (tabId, data) {
            // Implementation depends on the data structure
            console.log('Updating tab content for:', tabId, data);
        },

        /**
         * Handle PO number updates
         */
        _onPONumberUpdate: function (ev) {
            var $input = $(ev.currentTarget);
            var invoiceId = $input.data('invoice-id');
            var poNumber = $input.val().trim();
            
            this._updatePONumber(invoiceId, poNumber);
        },

        /**
         * Update PO number via RPC
         */
        _updatePONumber: function (invoiceId, poNumber) {
            var self = this;
            
            rpc.query({
                route: '/my/invoices/update_po',
                params: {
                    invoice_id: invoiceId,
                    po_number: poNumber,
                    csrf_token: core.csrf_token,
                }
            }).then(function (result) {
                if (result.success) {
                    self._showNotification('PO number updated successfully', 'success');
                } else {
                    self._showNotification(result.error || 'Failed to update PO number', 'danger');
                }
            }).catch(function (error) {
                self._showNotification('Error updating PO number', 'danger');
                console.error('PO update error:', error);
            });
        },

        /**
         * Handle filter button clicks
         */
        _onFilterClick: function (ev) {
            var $btn = $(ev.currentTarget);
            var filterFunction = $btn.attr('onclick');
            
            // Remove active class from siblings
            $btn.siblings().removeClass('btn-primary').addClass('btn-outline-primary');
            $btn.removeClass('btn-outline-primary').addClass('btn-primary');
            
            // Extract filter type and value
            var match = filterFunction.match(/filter(\w+)\('(\w+)'\)/);
            if (match) {
                var filterType = match[1].toLowerCase();
                var filterValue = match[2];
                this._applyFilter(filterType, filterValue);
            }
        },

        /**
         * Apply filter to the appropriate data set
         */
        _applyFilter: function (filterType, filterValue) {
            if (filterType === 'invoices') {
                this._filterInvoices(filterValue);
            } else if (filterType === 'certificates') {
                this._filterCertificates(filterValue);
            } else if (filterType === 'comms') {
                this._filterCommunications(filterValue);
            }
        },

        /**
         * Filter invoices by status
         */
        _filterInvoices: function (status) {
            var $tbody = this.$('#invoices_table tbody');
            $tbody.empty();
            
            this.originalInvoices.forEach(function (invoice) {
                if (status === 'all' || invoice.status.includes(status)) {
                    $tbody.append(invoice.element);
                }
            });
            
            this._updateResultCount('invoices', $tbody.find('tr').length);
        },

        /**
         * Filter certificates by type
         */
        _filterCertificates: function (type) {
            var $tbody = this.$('#certificates tbody');
            $tbody.empty();
            
            this.originalCertificates.forEach(function (cert) {
                if (type === 'all' || cert.type.includes(type)) {
                    $tbody.append(cert.element);
                }
            });
            
            this._updateResultCount('certificates', $tbody.find('tr').length);
        },

        /**
         * Filter communications by type
         */
        _filterCommunications: function (type) {
            var $container = this.$('.communications-list');
            $container.empty();
            
            this.originalCommunications.forEach(function (comm) {
                if (type === 'all' || comm.type.includes(type)) {
                    $container.append(comm.element);
                }
            });
            
            this._updateResultCount('communications', $container.find('.communication-item').length);
        },

        /**
         * Load recent activity
         */
        _loadRecentActivity: function () {
            var self = this;
            
            rpc.query({
                route: '/my/docs/recent_activity',
                params: {
                    csrf_token: core.csrf_token,
                }
            }).then(function (result) {
                if (result.recent_activities) {
                    self._displayRecentActivity(result.recent_activities);
                }
            });
        },

        /**
         * Display recent activity
         */
        _displayRecentActivity: function (activities) {
            // Could add a recent activity sidebar or notification area
            console.log('Recent activities:', activities);
        },

        /**
         * Setup real-time updates
         */
        _setupRealTimeUpdates: function () {
            var self = this;
            
            // Poll for updates every 5 minutes
            this.updateInterval = setInterval(function () {
                self._checkForUpdates();
            }, 300000); // 5 minutes
        },

        /**
         * Check for updates
         */
        _checkForUpdates: function () {
            var self = this;
            
            rpc.query({
                route: '/my/docs/check_updates',
                params: {
                    last_check: this.lastUpdateCheck || new Date().toISOString(),
                    csrf_token: core.csrf_token,
                }
            }).then(function (result) {
                if (result.has_updates) {
                    self._showUpdateNotification();
                }
                self.lastUpdateCheck = new Date().toISOString();
            });
        },

        /**
         * Show update notification
         */
        _showUpdateNotification: function () {
            var $notification = $('<div class="alert alert-info alert-dismissible fade show position-fixed" style="top: 20px; right: 20px; z-index: 9999;">' +
                '<strong>New updates available!</strong> Refresh the page to see the latest documents.' +
                '<button type="button" class="close" data-dismiss="alert">' +
                '<span>&times;</span>' +
                '</button>' +
                '</div>');
            
            $('body').append($notification);
            
            // Auto-hide after 10 seconds
            setTimeout(function () {
                $notification.alert('close');
            }, 10000);
        },

        /**
         * Show notification message
         */
        _showNotification: function (message, type) {
            var $notification = $('<div class="alert alert-' + type + ' alert-dismissible fade show position-fixed" style="top: 20px; right: 20px; z-index: 9999;">' +
                message +
                '<button type="button" class="close" data-dismiss="alert">' +
                '<span>&times;</span>' +
                '</button>' +
                '</div>');
            
            $('body').append($notification);
            
            // Auto-hide after 5 seconds
            setTimeout(function () {
                $notification.alert('close');
            }, 5000);
        },

        /**
         * Cleanup when widget is destroyed
         */
        destroy: function () {
            if (this.updateInterval) {
                clearInterval(this.updateInterval);
            }
            this._super.apply(this, arguments);
        }
    });

    // Global functions for template onclick handlers
    window.filterInvoices = function (status) {
        console.log('Filtering invoices by:', status);
    };

    window.filterCertificates = function (type) {
        console.log('Filtering certificates by:', type);
    };

    window.filterComms = function (type) {
        console.log('Filtering communications by:', type);
    };

    window.updatePONumber = function (input) {
        var $input = $(input);
        var invoiceId = $input.data('invoice-id');
        var poNumber = $input.val().trim();
        
        // Trigger the widget's update method
        var widget = $input.closest('.o_portal_docs_center').data('widget');
        if (widget) {
            widget._updatePONumber(invoiceId, poNumber);
        }
    };

    window.requestInvoiceChange = function (invoiceId) {
        window.location.href = '/my/invoices/' + invoiceId + '/request_change';
    };

    window.acceptQuote = function (quoteId) {
        if (confirm('Are you sure you want to accept this quote?')) {
            rpc.query({
                route: '/my/quotes/' + quoteId + '/accept',
                params: {
                    csrf_token: core.csrf_token,
                }
            }).then(function (result) {
                if (result.success) {
                    location.reload();
                } else {
                    alert('Error accepting quote: ' + (result.error || 'Unknown error'));
                }
            });
        }
    };

    window.verifyCertificate = function (certId) {
        window.open('/my/certificates/' + certId + '/verify', '_blank');
    };

    window.viewCommunication = function (commId) {
        window.location.href = '/my/communications/' + commId;
    };

    window.exportAllDocs = function () {
        if (confirm('This will generate a comprehensive export of all your documents. Continue?')) {
            window.location.href = '/my/docs/export_all';
        }
    };

    return publicWidget.registry.PortalDocsCenter;
});
