/**
 * Portal Dashboard Bootstrap - Vanilla JavaScript (Odoo 18 Compatible)
 * 
 * PURPOSE: Dynamic dashboard card injection for portal
 * USE CASE: Auto-inject dashboard cards if template customizations removed them
 * 
 * FEATURES:
 * ✓ Dynamic card creation
 * ✓ Stats fetching via AJAX
 * ✓ Responsive grid layout
 * ✓ Icon and color customization
 * 
 * CONVERSION NOTES (Odoo 18):
 * - Removed: @web/core/utils/ajax
 * - Uses native fetch() for data
 * - Pure DOM manipulation
 */

(function() {
    'use strict';

    class PortalDashboardBootstrap {
        constructor(container) {
            this.container = container;
            this.cardsConfig = [];
            this.init();
        }

        init() {
            this._defineCards();
            this._checkAndInject();
            console.log('[PortalDashboardBootstrap] Initialized');
        }

        _defineCards() {
            this.cardsConfig = [
                {
                    id: 'containers',
                    title: 'My Containers',
                    icon: 'fa-archive',
                    color: 'primary',
                    link: '/my/containers',
                    statEndpoint: '/my/containers/count'
                },
                {
                    id: 'documents',
                    title: 'Documents',
                    icon: 'fa-file-text',
                    color: 'success',
                    link: '/my/documents',
                    statEndpoint: '/my/documents/count'
                },
                {
                    id: 'requests',
                    title: 'Service Requests',
                    icon: 'fa-clipboard',
                    color: 'warning',
                    link: '/my/requests',
                    statEndpoint: '/my/requests/count'
                },
                {
                    id: 'certificates',
                    title: 'Certificates',
                    icon: 'fa-certificate',
                    color: 'info',
                    link: '/my/certificates',
                    statEndpoint: '/my/certificates/count'
                },
                {
                    id: 'invoices',
                    title: 'Invoices',
                    icon: 'fa-usd',
                    color: 'secondary',
                    link: '/my/invoices',
                    statEndpoint: '/my/invoices/count'
                },
                {
                    id: 'calendar',
                    title: 'Service Calendar',
                    icon: 'fa-calendar',
                    color: 'danger',
                    link: '/my/calendar',
                    stat: null // No count for calendar
                }
            ];
        }

        _checkAndInject() {
            // Check if dashboard cards already exist
            const existingCards = this.container.querySelectorAll('.o_portal_dashboard_card');
            if (existingCards.length > 0) {
                console.log('[PortalDashboardBootstrap] Cards already present, skipping injection');
                return;
            }

            // Check for the dashboard container
            const dashboardTarget = this.container.querySelector('.o_portal_dashboard_cards, .o_portal_my_home_content');
            if (!dashboardTarget) {
                console.log('[PortalDashboardBootstrap] No dashboard target found');
                return;
            }

            this._renderCards(dashboardTarget);
            this._fetchStats();
        }

        _renderCards(target) {
            const html = `
                <div class="row g-3 mb-4 portal-dashboard-cards-injected">
                    ${this.cardsConfig.map(card => this._createCard(card)).join('')}
                </div>
            `;

            // Insert at the beginning of the target
            target.insertAdjacentHTML('afterbegin', html);
        }

        _createCard(config) {
            const colorClasses = {
                primary: 'text-primary border-primary',
                success: 'text-success border-success',
                warning: 'text-warning border-warning',
                info: 'text-info border-info',
                secondary: 'text-secondary border-secondary',
                danger: 'text-danger border-danger'
            };

            return `
                <div class="col-sm-6 col-md-4 col-lg-3">
                    <a href="${config.link}" class="text-decoration-none">
                        <div class="card h-100 o_portal_dashboard_card border-start border-4 ${colorClasses[config.color] || ''}" 
                             data-card-id="${config.id}">
                            <div class="card-body d-flex align-items-center">
                                <div class="me-3">
                                    <i class="fa ${config.icon} fa-2x ${colorClasses[config.color].split(' ')[0]}"></i>
                                </div>
                                <div>
                                    <h6 class="card-title mb-1 text-dark">${this._escapeHtml(config.title)}</h6>
                                    <div class="card-stat text-muted" data-stat-id="${config.id}">
                                        ${config.stat !== null ? '<span class="spinner-border spinner-border-sm"></span>' : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </a>
                </div>
            `;
        }

        async _fetchStats() {
            for (const card of this.cardsConfig) {
                if (card.statEndpoint) {
                    try {
                        const response = await fetch(card.statEndpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                jsonrpc: '2.0',
                                method: 'call',
                                params: {},
                                id: Math.floor(Math.random() * 1000000)
                            })
                        });
                        const data = await response.json();
                        const count = data.result?.count ?? data.result ?? 0;
                        this._updateCardStat(card.id, count);
                    } catch (err) {
                        console.warn(`[PortalDashboardBootstrap] Failed to fetch stat for ${card.id}`, err);
                        this._updateCardStat(card.id, '-');
                    }
                }
            }
        }

        _updateCardStat(cardId, value) {
            const statEl = this.container.querySelector(`[data-stat-id="${cardId}"]`);
            if (statEl) {
                statEl.innerHTML = typeof value === 'number' 
                    ? `<strong>${value}</strong> items` 
                    : value;
            }
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
    function initDashboard() {
        const containers = document.querySelectorAll('.o_portal_my_home, .o_portal_wrap');
        containers.forEach(container => {
            new PortalDashboardBootstrap(container);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDashboard);
    } else {
        initDashboard();
    }

    // Export globally
    window.PortalDashboardBootstrap = PortalDashboardBootstrap;

})();
