/**
 * Portal Tour Widget - Vanilla JavaScript (Odoo 18 Compatible)
 * 
 * PURPOSE: Interactive guided tours for portal features
 * USE CASE: First-time user onboarding, feature discovery
 * 
 * FEATURES:
 * ✓ Step-by-step guided tours
 * ✓ Element highlighting
 * ✓ Progress tracking
 * ✓ Skip/restart functionality
 * ✓ LocalStorage for completion tracking
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: @web_tour/tour_manager, @web/core/registry
 * - Built lightweight tour system from scratch
 * - Uses native DOM APIs for highlighting
 */

(function() {
    'use strict';

    class PortalTour {
        constructor(options = {}) {
            this.tours = {};
            this.currentTour = null;
            this.currentStep = 0;
            this.overlay = null;
            this.tooltip = null;
            this.options = Object.assign({
                storageKey: 'portal_tours_completed',
                autoStart: false,
                showProgressBar: true
            }, options);
            
            this._createElements();
            this._registerTours();
            console.log('[PortalTour] Initialized');
        }

        _createElements() {
            // Create overlay
            this.overlay = document.createElement('div');
            this.overlay.className = 'portal-tour-overlay';
            this.overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 9998;
                display: none;
                pointer-events: none;
            `;

            // Create tooltip
            this.tooltip = document.createElement('div');
            this.tooltip.className = 'portal-tour-tooltip';
            this.tooltip.style.cssText = `
                position: fixed;
                z-index: 10000;
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                max-width: 400px;
                display: none;
                padding: 0;
            `;

            document.body.appendChild(this.overlay);
            document.body.appendChild(this.tooltip);

            // Add styles
            this._injectStyles();
        }

        _injectStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .portal-tour-highlight {
                    position: relative;
                    z-index: 9999 !important;
                    box-shadow: 0 0 0 4px #007bff, 0 0 20px rgba(0,123,255,0.5) !important;
                    border-radius: 4px;
                }
                .portal-tour-tooltip-header {
                    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                    color: white;
                    padding: 12px 16px;
                    border-radius: 8px 8px 0 0;
                    font-weight: 600;
                }
                .portal-tour-tooltip-body {
                    padding: 16px;
                }
                .portal-tour-tooltip-footer {
                    padding: 12px 16px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .portal-tour-progress {
                    height: 4px;
                    background: #e9ecef;
                    border-radius: 2px;
                    overflow: hidden;
                }
                .portal-tour-progress-bar {
                    height: 100%;
                    background: #007bff;
                    transition: width 0.3s ease;
                }
                .portal-tour-btn {
                    padding: 8px 16px;
                    border-radius: 4px;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s;
                }
                .portal-tour-btn-primary {
                    background: #007bff;
                    color: white;
                }
                .portal-tour-btn-primary:hover {
                    background: #0056b3;
                }
                .portal-tour-btn-secondary {
                    background: #f8f9fa;
                    color: #6c757d;
                }
                .portal-tour-btn-secondary:hover {
                    background: #e9ecef;
                }
            `;
            document.head.appendChild(style);
        }

        _registerTours() {
            // Portal Overview Tour
            this.register('portal_overview', {
                name: 'Portal Overview',
                steps: [
                    {
                        target: '.o_portal_my_home',
                        title: 'Welcome to Your Portal',
                        content: 'This is your personal dashboard where you can manage all your records, containers, and service requests.',
                        position: 'bottom'
                    },
                    {
                        target: '[data-menu-section="inventory"]',
                        title: 'Inventory Management',
                        content: 'Access your document inventory, search by barcode, and track container locations.',
                        position: 'right'
                    },
                    {
                        target: '[data-menu-section="services"]',
                        title: 'Request Services',
                        content: 'Request document retrievals, schedule pickups, or arrange for secure destruction.',
                        position: 'right'
                    },
                    {
                        target: '[data-menu-section="certificates"]',
                        title: 'Compliance Certificates',
                        content: 'Download NAID-certified destruction certificates for your records.',
                        position: 'right'
                    },
                    {
                        target: '.o_portal_navbar',
                        title: 'Quick Navigation',
                        content: 'Use the top navigation to quickly access any section of your portal.',
                        position: 'bottom'
                    }
                ]
            });

            // Inventory Tour
            this.register('inventory_tour', {
                name: 'Inventory Guide',
                steps: [
                    {
                        target: '.o_portal_inventory_search',
                        title: 'Search Your Inventory',
                        content: 'Search by container name, barcode, document title, or any custom field.',
                        position: 'bottom'
                    },
                    {
                        target: '.o_portal_inventory_filters',
                        title: 'Filter Options',
                        content: 'Filter by location, document type, status, or retention date.',
                        position: 'right'
                    },
                    {
                        target: '.o_portal_inventory_table',
                        title: 'Inventory List',
                        content: 'Click any row to view details, or use checkboxes for bulk operations.',
                        position: 'top'
                    },
                    {
                        target: '[data-action="bulk-retrieve"]',
                        title: 'Bulk Actions',
                        content: 'Select multiple items and request retrieval or other services in one action.',
                        position: 'bottom'
                    }
                ]
            });

            // Document Retrieval Tour
            this.register('retrieval_tour', {
                name: 'Document Retrieval',
                steps: [
                    {
                        target: '#retrieval-form',
                        title: 'Create Retrieval Request',
                        content: 'Fill out this form to request documents from storage.',
                        position: 'top'
                    },
                    {
                        target: '[data-action="add-item"]',
                        title: 'Add Items',
                        content: 'Click here to add multiple containers or documents to your request.',
                        position: 'left'
                    },
                    {
                        target: '#priority',
                        title: 'Priority Selection',
                        content: 'Choose standard (3-5 days), rush (24 hours), or same-day delivery.',
                        position: 'right'
                    },
                    {
                        target: '#pricing-breakdown',
                        title: 'Live Pricing',
                        content: 'See real-time pricing based on your selections.',
                        position: 'top'
                    }
                ]
            });
        }

        register(id, tour) {
            this.tours[id] = tour;
        }

        start(tourId) {
            const tour = this.tours[tourId];
            if (!tour) {
                console.warn(`[PortalTour] Tour "${tourId}" not found`);
                return;
            }

            this.currentTour = tour;
            this.currentStep = 0;
            this._showStep();
        }

        _showStep() {
            if (!this.currentTour || this.currentStep >= this.currentTour.steps.length) {
                this._endTour();
                return;
            }

            const step = this.currentTour.steps[this.currentStep];
            const target = document.querySelector(step.target);

            // Clear previous highlight
            document.querySelectorAll('.portal-tour-highlight').forEach(el => {
                el.classList.remove('portal-tour-highlight');
            });

            if (target) {
                target.classList.add('portal-tour-highlight');
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            this.overlay.style.display = 'block';
            this._renderTooltip(step, target);
        }

        _renderTooltip(step, target) {
            const totalSteps = this.currentTour.steps.length;
            const progress = ((this.currentStep + 1) / totalSteps) * 100;

            this.tooltip.innerHTML = `
                <div class="portal-tour-tooltip-header">
                    ${this._escapeHtml(step.title)}
                </div>
                ${this.options.showProgressBar ? `
                <div class="portal-tour-progress">
                    <div class="portal-tour-progress-bar" style="width: ${progress}%"></div>
                </div>
                ` : ''}
                <div class="portal-tour-tooltip-body">
                    <p>${this._escapeHtml(step.content)}</p>
                </div>
                <div class="portal-tour-tooltip-footer">
                    <span class="text-muted">${this.currentStep + 1} of ${totalSteps}</span>
                    <div>
                        <button class="portal-tour-btn portal-tour-btn-secondary me-2" data-tour-action="skip">
                            Skip Tour
                        </button>
                        ${this.currentStep > 0 ? `
                        <button class="portal-tour-btn portal-tour-btn-secondary me-2" data-tour-action="prev">
                            Back
                        </button>
                        ` : ''}
                        <button class="portal-tour-btn portal-tour-btn-primary" data-tour-action="next">
                            ${this.currentStep === totalSteps - 1 ? 'Finish' : 'Next'}
                        </button>
                    </div>
                </div>
            `;

            // Position tooltip
            this._positionTooltip(step.position, target);
            this.tooltip.style.display = 'block';

            // Add event listeners
            this.tooltip.querySelectorAll('[data-tour-action]').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const action = e.target.dataset.tourAction;
                    if (action === 'next') this._nextStep();
                    else if (action === 'prev') this._prevStep();
                    else if (action === 'skip') this._endTour();
                });
            });
        }

        _positionTooltip(position, target) {
            if (!target) {
                // Center on screen
                this.tooltip.style.top = '50%';
                this.tooltip.style.left = '50%';
                this.tooltip.style.transform = 'translate(-50%, -50%)';
                return;
            }

            const rect = target.getBoundingClientRect();
            const tooltipRect = this.tooltip.getBoundingClientRect();
            const margin = 16;

            let top, left;

            switch (position) {
                case 'top':
                    top = rect.top - tooltipRect.height - margin;
                    left = rect.left + (rect.width - tooltipRect.width) / 2;
                    break;
                case 'bottom':
                    top = rect.bottom + margin;
                    left = rect.left + (rect.width - tooltipRect.width) / 2;
                    break;
                case 'left':
                    top = rect.top + (rect.height - tooltipRect.height) / 2;
                    left = rect.left - tooltipRect.width - margin;
                    break;
                case 'right':
                    top = rect.top + (rect.height - tooltipRect.height) / 2;
                    left = rect.right + margin;
                    break;
                default:
                    top = rect.bottom + margin;
                    left = rect.left;
            }

            // Keep within viewport
            top = Math.max(margin, Math.min(top, window.innerHeight - tooltipRect.height - margin));
            left = Math.max(margin, Math.min(left, window.innerWidth - tooltipRect.width - margin));

            this.tooltip.style.top = `${top}px`;
            this.tooltip.style.left = `${left}px`;
            this.tooltip.style.transform = 'none';
        }

        _nextStep() {
            this.currentStep++;
            this._showStep();
        }

        _prevStep() {
            if (this.currentStep > 0) {
                this.currentStep--;
                this._showStep();
            }
        }

        _endTour() {
            // Mark as completed
            if (this.currentTour) {
                this._markCompleted(Object.keys(this.tours).find(k => this.tours[k] === this.currentTour));
            }

            // Clean up
            document.querySelectorAll('.portal-tour-highlight').forEach(el => {
                el.classList.remove('portal-tour-highlight');
            });

            this.overlay.style.display = 'none';
            this.tooltip.style.display = 'none';
            this.currentTour = null;
            this.currentStep = 0;
        }

        _markCompleted(tourId) {
            if (!tourId) return;
            const completed = this._getCompleted();
            if (!completed.includes(tourId)) {
                completed.push(tourId);
                localStorage.setItem(this.options.storageKey, JSON.stringify(completed));
            }
        }

        _getCompleted() {
            try {
                return JSON.parse(localStorage.getItem(this.options.storageKey) || '[]');
            } catch {
                return [];
            }
        }

        isCompleted(tourId) {
            return this._getCompleted().includes(tourId);
        }

        reset(tourId) {
            const completed = this._getCompleted().filter(id => id !== tourId);
            localStorage.setItem(this.options.storageKey, JSON.stringify(completed));
        }

        resetAll() {
            localStorage.removeItem(this.options.storageKey);
        }

        _escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // ========================================================================
    // Auto-initialization
    // ========================================================================
    function initTours() {
        window.portalTour = new PortalTour();

        // Auto-start tour if specified
        const autoStart = document.querySelector('[data-tour-autostart]');
        if (autoStart) {
            const tourId = autoStart.dataset.tourAutostart;
            if (!window.portalTour.isCompleted(tourId)) {
                setTimeout(() => window.portalTour.start(tourId), 1000);
            }
        }

        // Tour trigger buttons
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-start-tour]');
            if (btn) {
                e.preventDefault();
                window.portalTour.start(btn.dataset.startTour);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTours);
    } else {
        initTours();
    }

    // Export globally
    window.PortalTour = PortalTour;

})();
