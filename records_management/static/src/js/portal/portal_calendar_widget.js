/**
 * Portal Calendar Widget - Customer Service Schedule (Vanilla JavaScript - Odoo 18 Compatible)
 * 
 * PURPOSE: Customer-facing portal calendar showing scheduled services
 * USE CASE: /my/calendar route - shows pickups, retrievals, shredding, FSM tasks
 * 
 * ARCHITECTURE:
 * - Uses FullCalendar library (loaded via CDN in template)
 * - Fetches events from /my/calendar/events JSON endpoint
 * - No Odoo dependencies (vanilla JS only)
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: odoo.define(), publicWidget dependency
 * - Replaced: jQuery with native DOM APIs
 * - Added: IIFE wrapper for module isolation
 * - Uses fetch() for AJAX instead of web.ajax
 * 
 * FEATURES:
 * ✓ Monthly/Weekly/List views
 * ✓ Event click details modal
 * ✓ Tooltips on events
 * ✓ Color-coded by service type
 * ✓ Links to request details
 * 
 * BROWSER SUPPORT: Modern browsers (ES6+)
 */

(function() {
    'use strict';

    class PortalCalendarWidget {
        constructor(containerElement) {
            this.container = containerElement;
            this.calendar = null;
            this.init();
        }

        init() {
            // Wait for FullCalendar to be available
            this._waitForFullCalendar()
                .then(() => {
                    this._initCalendar();
                })
                .catch((err) => {
                    console.error('[PortalCalendar] Failed to load FullCalendar:', err);
                    this._showError('Calendar library failed to load. Please refresh the page.');
                });
        }

        _waitForFullCalendar() {
            return new Promise((resolve, reject) => {
                let attempts = 0;
                const maxAttempts = 50; // 5 seconds max wait
                const checkInterval = 100; // ms

                const check = () => {
                    attempts++;
                    if (typeof FullCalendar !== 'undefined') {
                        console.log('[PortalCalendar] FullCalendar library loaded');
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        reject(new Error('FullCalendar not loaded after timeout'));
                    } else {
                        setTimeout(check, checkInterval);
                    }
                };

                check();
            });
        }

        _initCalendar() {
            const calendarEl = document.getElementById('portal-calendar');
            const loadingEl = document.getElementById('calendar-loading');

            if (!calendarEl) {
                console.error('[PortalCalendar] Calendar element #portal-calendar not found');
                return;
            }

            const self = this;

            this.calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                },
                buttonText: {
                    today: 'Today',
                    month: 'Month',
                    week: 'Week',
                    list: 'List'
                },
                height: 'auto',
                navLinks: true,
                editable: false,
                dayMaxEvents: true, // Show "more" link when too many events

                events: function(info, successCallback, failureCallback) {
                    self._fetchEvents(info.startStr, info.endStr)
                        .then(function(events) {
                            // Hide loading, show calendar
                            if (loadingEl) loadingEl.style.display = 'none';
                            calendarEl.style.display = 'block';
                            successCallback(events);
                        })
                        .catch(function(error) {
                            console.error('[PortalCalendar] Error fetching events:', error);
                            self._showError('Failed to load calendar events. Please try again later.');
                            failureCallback(error);
                        });
                },

                eventClick: function(info) {
                    info.jsEvent.preventDefault();
                    self._showEventDetails(info.event);
                },

                eventDidMount: function(info) {
                    self._addTooltip(info.el, info.event.title);
                }
            });

            this.calendar.render();
            console.log('[PortalCalendar] Calendar initialized successfully');
        }

        _fetchEvents(start, end) {
            return fetch('/my/calendar/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        start: start,
                        end: end
                    },
                    id: Math.floor(Math.random() * 1000000)
                })
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function(data) {
                if (data.error) {
                    throw new Error(data.error.message || 'Server error');
                }
                // Return the result array (or empty array if null)
                return data.result || [];
            });
        }

        _showEventDetails(event) {
            const props = event.extendedProps || {};

            // Build modal content
            let modalBody = '<dl class="row mb-0">';
            modalBody += '<dt class="col-sm-4">Title:</dt><dd class="col-sm-8">' + this._escapeHtml(event.title) + '</dd>';
            
            if (event.start) {
                const startDate = event.start.toLocaleDateString();
                const startTime = event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const showTime = startTime !== '12:00 AM' && startTime !== '00:00';
                modalBody += '<dt class="col-sm-4">Date:</dt><dd class="col-sm-8">' + startDate;
                if (showTime) {
                    modalBody += ' at ' + startTime;
                }
                modalBody += '</dd>';
            }

            if (event.end) {
                const endDate = event.end.toLocaleDateString();
                const endTime = event.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                modalBody += '<dt class="col-sm-4">End:</dt><dd class="col-sm-8">' + endDate + ' ' + endTime + '</dd>';
            }

            // Type-specific details
            if (props.type === 'shredding') {
                if (props.frequency) {
                    modalBody += '<dt class="col-sm-4">Frequency:</dt><dd class="col-sm-8">' + 
                        this._capitalize(props.frequency) + '</dd>';
                }
                if (props.location) {
                    modalBody += '<dt class="col-sm-4">Location:</dt><dd class="col-sm-8">' + 
                        this._escapeHtml(props.location) + '</dd>';
                }
            } else if (props.type === 'service') {
                if (props.work_order_type) {
                    modalBody += '<dt class="col-sm-4">Service Type:</dt><dd class="col-sm-8">' + 
                        this._capitalize(props.work_order_type.replace('_', ' ')) + '</dd>';
                }
                if (props.stage) {
                    modalBody += '<dt class="col-sm-4">Stage:</dt><dd class="col-sm-8">' + 
                        this._escapeHtml(props.stage) + '</dd>';
                }
            } else if (props.type === 'request') {
                if (props.request_type) {
                    modalBody += '<dt class="col-sm-4">Request Type:</dt><dd class="col-sm-8">' + 
                        this._capitalize(props.request_type) + '</dd>';
                }
                if (props.state) {
                    modalBody += '<dt class="col-sm-4">Status:</dt><dd class="col-sm-8">' + 
                        this._escapeHtml(props.state) + '</dd>';
                }
            }

            modalBody += '</dl>';

            // Update modal elements
            const modalTitle = document.getElementById('eventModalTitle');
            const modalBodyEl = document.getElementById('eventModalBody');
            const viewBtn = document.getElementById('eventViewDetailsBtn');

            if (modalTitle) modalTitle.textContent = event.title;
            if (modalBodyEl) modalBodyEl.innerHTML = modalBody;

            // Show/hide "View Details" button
            if (viewBtn) {
                if (event.url) {
                    viewBtn.setAttribute('href', event.url);
                    viewBtn.style.display = 'inline-block';
                } else {
                    viewBtn.style.display = 'none';
                }
            }

            // Show modal (Bootstrap 5)
            const modalEl = document.getElementById('eventDetailsModal');
            if (modalEl) {
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                } else if (typeof $ !== 'undefined' && $.fn.modal) {
                    // Fallback to jQuery/Bootstrap 4
                    $(modalEl).modal('show');
                }
            }
        }

        _addTooltip(element, title) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(element, {
                    title: title,
                    placement: 'top',
                    trigger: 'hover'
                });
            } else if (typeof $ !== 'undefined' && $.fn.tooltip) {
                $(element).tooltip({
                    title: title,
                    placement: 'top',
                    trigger: 'hover',
                    container: 'body'
                });
            }
        }

        _showError(message) {
            const loadingEl = document.getElementById('calendar-loading');
            if (loadingEl) {
                loadingEl.innerHTML = '<div class="alert alert-danger">' +
                    '<i class="fa fa-exclamation-triangle"></i> ' + 
                    this._escapeHtml(message) + '</div>';
            }
        }

        _escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        _capitalize(str) {
            if (!str) return 'N/A';
            return str.charAt(0).toUpperCase() + str.slice(1);
        }
    }

    // ========================================================================
    // Auto-initialization
    // ========================================================================
    function initPortalCalendar() {
        const calendarEl = document.getElementById('portal-calendar');
        if (calendarEl) {
            new PortalCalendarWidget(document.body);
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPortalCalendar);
    } else {
        initPortalCalendar();
    }

    // Expose globally for manual initialization if needed
    window.RecordsManagementPortalCalendar = PortalCalendarWidget;

})();
