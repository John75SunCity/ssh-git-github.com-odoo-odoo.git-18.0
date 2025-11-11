/** @odoo-module **/
/**
 * Portal / Inventory Tours
 *
 * This file previously mixed ESM (`@odoo-module`) + legacy AMD (`odoo.define`).
 * The mixed pattern was triggering asset bundling instability in test mode
 * (web.assets_web.bundle.xml failure) when `web_tour.tour` wasn't resolvable
 * early enough. We now:
 *   - Keep a pure ESM implementation
 *   - Provide a defensive lazy resolver for the legacy `web_tour.tour` API
 *     only if available (for backwards compatibility)
 *   - Always register tours through the modern registry so Owl test harness
 *     can discover them even if legacy loader is skipped.
 */

import { registry } from "@web/core/registry";
import { tourManager } from "@web_tour/tour_manager";

const $ = window.jQuery;
const hasJQuery = Boolean($);
const withJQuery = (callback) => {
    if (hasJQuery) {
        callback($);
    }
};

// Attempt to access legacy tour API if present (older compatibility layers)
let legacyTourApi;
try {
    // `require` may not exist in strict ESM contexts; guard it.
    // eslint-disable-next-line no-undef
    if (typeof require === 'function') {
        // eslint-disable-next-line no-undef
        legacyTourApi = require('web_tour.tour');
    }
} catch (err) {
    // Silently ignore – modern registry path will still function.
    console.debug('[portal_tour] Legacy tour API not available:', err.message);
}
// Traditional Portal App Tour (legacy style definition retained as data only)
const legacyPortalAppTour = {
    test: true,
    url: '/my/overview',
    rainbowMan: true,
    fadeout: 'slow',
    steps: [
            {
                trigger: '.hero-section h1',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-rocket text-primary"></i> Welcome to Your Portal!</h4><p>This guided tour will showcase all the powerful features of your enterprise-grade Records Management Portal.</p></div>',
                position: 'bottom',
                run: function () {
                    // Add entrance animation
                    withJQuery(() => {
                        $('.hero-section').addClass('animate__animated animate__fadeIn');
                    });
                },
            },
            {
                trigger: '.stats-dashboard',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-chart-bar text-success"></i> Real-Time Statistics</h4><p>Monitor your storage boxes, documents, pending requests, and certificates at a glance. These numbers update in real-time!</p></div>',
                position: 'bottom',
                run: function () {
                    // Trigger counter animation
                    window.portalFunctions && window.portalFunctions.animateCounters && window.portalFunctions.animateCounters();
                },
            },
            {
                trigger: '.feature-card:has(.fa-search)',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-search text-primary"></i> Advanced Inventory Management</h4><p>Search through thousands of documents with Google-like precision. Use bulk operations, advanced filters, and export capabilities.</p><ul class="mt-2"><li>Smart search with autocomplete</li><li>Bulk selection and actions</li><li>Advanced filtering system</li><li>Export in multiple formats</li></ul></div>',
                position: 'right',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-card');
                    });
                },
            },
            {
                trigger: '.feature-card:has(.fa-calculator)',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-calculator text-success"></i> Self-Service Quotes & Billing</h4><p>Generate instant PDF quotes and manage your billing transparently. No more waiting for quotes!</p><ul class="mt-2"><li>Instant PDF generation</li><li>PO number management</li><li>Billing change requests</li><li>Complete transparency</li></ul></div>',
                position: 'left',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-card');
                    });
                },
            },
            {
                trigger: '.feature-card:has(.fa-cogs)',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-cogs text-warning"></i> Service Requests & Tracking</h4><p>Submit destruction and service requests with electronic signatures. Track everything in real-time with FSM integration.</p><ul class="mt-2"><li>Electronic signature integration</li><li>Real-time FSM tracking</li><li>Automated certificates</li><li>SMS notifications</li></ul></div>',
                position: 'right',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-card');
                    });
                },
            },
            {
                trigger: '.feature-card:has(.fa-users)',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-users text-info"></i> Enterprise User Management</h4><p>Import users in bulk via CSV, assign granular access levels, and track all activity with comprehensive audit trails.</p><ul class="mt-2"><li>CSV bulk import</li><li>Role-based access control</li><li>Department management</li><li>Activity tracking</li></ul></div>',
                position: 'left',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-card');
                    });
                },
            },
            {
                trigger: '.feature-card:has(.fa-shield)',
                content: '<div class="tour-step-compliance"><h4><i class="fa fa-shield text-danger"></i> NAID AAA Compliance & Security</h4><p class="text-emphasis"><strong>This is our compliance cornerstone!</strong></p><div class="compliance-highlights mt-3"><div class="row"><div class="col-6"><h6><i class="fa fa-certificate text-warning"></i> NAID AAA Certified</h6><p class="small">Industry-leading data destruction standards</p></div><div class="col-6"><h6><i class="fa fa-file-text text-info"></i> Complete Audit Trails</h6><p class="small">Every action logged and timestamped</p></div><div class="col-6"><h6><i class="fa fa-link text-success"></i> Chain of Custody</h6><p class="small">Unbroken documentation trail</p></div><div class="col-6"><h6><i class="fa fa-chart-line text-primary"></i> Compliance Reports</h6><p class="small">Regulatory reporting made easy</p></div></div></div></div>',
                position: 'right',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-compliance');
                        // Show compliance badges animation
                        $('.compliance-badges .badge').addClass('animate__animated animate__pulse');
                    });
                },
            },
            {
                trigger: '.feature-card:has(.fa-brain)',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-brain text-dark"></i> AI-Powered Insights (Coming Soon)</h4><p>Future AI features will provide smart recommendations and predictive analytics based on your usage patterns.</p><ul class="mt-2"><li>Smart recommendations</li><li>Predictive analytics</li><li>Usage pattern analysis</li><li>Intelligent alerts</li></ul><div class="alert alert-info mt-2"><i class="fa fa-lightbulb"></i> <strong>Innovation Preview:</strong> This feature represents our commitment to cutting-edge technology!</div></div>',
                position: 'left',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-future');
                    });
                },
            },
            {
                trigger: '.activity-section',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-clock-o text-primary"></i> Activity & Smart Suggestions</h4><p>Stay informed with recent activity feeds and receive intelligent suggestions to optimize your workflow.</p></div>',
                position: 'top',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('tour-highlight-section');
                    });
                },
            },
            {
                trigger: '.compliance-badges',
                content: '<div class="tour-step-compliance"><h4><i class="fa fa-award text-warning"></i> Trust & Compliance Badges</h4><p><strong>Your data security is guaranteed by industry certifications:</strong></p><div class="mt-3"><div class="badge badge-success badge-lg mr-2 mb-2"><i class="fa fa-certificate"></i> NAID AAA Certified</div><div class="badge badge-info badge-lg mr-2 mb-2"><i class="fa fa-lock"></i> SOC 2 Compliant</div><div class="badge badge-warning badge-lg mb-2"><i class="fa fa-shield"></i> HIPAA Secure</div></div><p class="mt-2 text-muted">These certifications ensure the highest standards of data protection and destruction.</p></div>',
                position: 'bottom',
                run: function () {
                    withJQuery(() => {
                        $('.compliance-badges .badge').addClass('animate__animated animate__bounceIn');
                    });
                },
            },
            {
                trigger: '#start_portal_tour',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-play-circle text-success"></i> Interactive Tour Available</h4><p>You can restart this tour anytime by clicking this button. There are also feature-specific tours available throughout the portal.</p></div>',
                position: 'top',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).addClass('animate__animated animate__pulse animate__infinite');
                    });
                },
            },
            {
                trigger: '#watch_video_tour',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-video-camera text-info"></i> Video Tutorials</h4><p>Prefer video learning? Click here to access comprehensive video tutorials that walk you through each feature in detail.</p></div>',
                position: 'top',
            },
            {
                trigger: 'body',
                content: '<div class="tour-completion"><h3><i class="fa fa-trophy text-warning"></i> Congratulations!</h3><p class="lead">You\'ve completed the portal tour and are now ready to experience the full power of enterprise-grade records management!</p><div class="mt-4"><h5>Quick Start Options:</h5><a href="/my/inventory" class="btn btn-primary mr-2"><i class="fa fa-search"></i> Explore Inventory</a><a href="/my/requests" class="btn btn-success mr-2"><i class="fa fa-plus"></i> Create Request</a><a href="/my/quotes" class="btn btn-info"><i class="fa fa-calculator"></i> Generate Quote</a></div><div class="alert alert-success mt-3"><i class="fa fa-shield"></i> <strong>Security Note:</strong> All your activities are protected by NAID AAA compliance standards.</div></div>',
                position: 'screen',
                run: function () {
                    // Cleanup tour highlights
                    withJQuery(() => {
                        $('.tour-highlight-card, .tour-highlight-compliance, .tour-highlight-future, .tour-highlight-section').removeClass('tour-highlight-card tour-highlight-compliance tour-highlight-future tour-highlight-section');
                    });
                    
                    // Show completion celebration
                    setTimeout(() => {
                        if (typeof confetti !== 'undefined') {
                            confetti({
                                particleCount: 100,
                                spread: 70,
                                origin: { y: 0.6 }
                            });
                        }
                    }, 500);
                },
            },
    ]
};

// Inventory feature tour (legacy style data)
const legacyInventoryFeatureTour = {
    test: true,
    url: '/my/inventory',
    steps: [
            {
                trigger: '#global_search',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-search text-primary"></i> Google-Like Search</h4><p>Type anything to search across all your inventory. Try commands like "active boxes" or "destroy document".</p></div>',
                position: 'bottom',
                run: function () {
                    withJQuery(() => {
                        $(this.trigger).focus().attr('placeholder', 'Try typing "active boxes"...');
                    });
                },
            },
            {
                trigger: '.search-container .filter-section',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-filter text-info"></i> Advanced Filters</h4><p>Use these filters to narrow down your search by type, status, location, and date ranges.</p></div>',
                position: 'bottom',
            },
            {
                trigger: '.bulk-actions-bar',
                content: '<div class="tour-step-enhanced"><h4><i class="fa fa-tasks text-warning"></i> Bulk Operations</h4><p>Select multiple items and perform batch operations like destruction requests, pickup scheduling, or archiving.</p></div>',
                position: 'top',
            },
    ]
};

// If legacy API exists, register there too (harmless duplicate for modern env)
if (legacyTourApi?.register) {
    try {
        legacyTourApi.register('portal_app_tour', legacyPortalAppTour, legacyPortalAppTour.steps);
        legacyTourApi.register('inventory_feature_tour', legacyInventoryFeatureTour, legacyInventoryFeatureTour.steps);
    } catch (err) {
        console.warn('[portal_tour] Legacy tour registration failed:', err.message);
    }
}

// Global (legacy) helpers – retained, but now delegate to modern tourManager when possible
window.startPortalTour = function() {
    if (tourManager?.startTour) {
        tourManager.startTour('portal_overview_tour', { mode: 'manual' });
    } else if (legacyTourApi?.run) {
        legacyTourApi.run('portal_app_tour');
    }
};

window.startInventoryTour = function() {
    if (tourManager?.startTour) {
        tourManager.startTour('portal_inventory_tour', { mode: 'manual' });
    } else if (legacyTourApi?.run) {
        legacyTourApi.run('inventory_feature_tour');
    }
};

    // Enhanced tour with skip option
    window.startEnhancedTour = function() {
        if (!hasJQuery) {
            console.warn('[portal_tour] jQuery not available; falling back to direct tour start.');
            window.portalFunctions.startPortalTour();
            return;
        }

        const tourModal = $(`
            <div class="modal fade" id="tourModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h4 class="modal-title"><i class="fa fa-play-circle"></i> Portal Tour Options</h4>
                            <button type="button" class="close text-white" data-dismiss="modal">&times;</button>
                        </div>
                        <div class="modal-body">
                            <p>Choose your preferred tour experience:</p>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card border-primary">
                                        <div class="card-body text-center">
                                            <i class="fa fa-rocket fa-2x text-primary mb-2"></i>
                                            <h5>Full Tour</h5>
                                            <p class="small">Complete walkthrough of all features</p>
                                            <button class="btn btn-primary" onclick="startPortalTour(); $('#tourModal').modal('hide');">Start Full Tour</button>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-info">
                                        <div class="card-body text-center">
                                            <i class="fa fa-search fa-2x text-info mb-2"></i>
                                            <h5>Inventory Focus</h5>
                                            <p class="small">Focus on inventory management features</p>
                                            <button class="btn btn-info" onclick="startInventoryTour(); $('#tourModal').modal('hide');">Inventory Tour</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="text-center mt-3">
                                <button class="btn btn-outline-secondary" data-dismiss="modal">
                                    <i class="fa fa-times"></i> Skip Tour
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        $('body').append(tourModal);
        tourModal.modal('show');
        
        // Remove modal after hiding
        tourModal.on('hidden.bs.modal', function() {
            $(this).remove();
        });
    };

// Modern Web Tour Implementation (Odoo 16+ / 18 Hardened)
const portalOverviewTour = {
    url: '/my/overview',
    test: true,
    fadeout: 'slow',
    rainbowManMessage: "Congratulations! You're now ready to manage your records like a pro!",
    steps: () => [
        {
            content: "Welcome to your Records Management Portal! This tour will guide you through all the amazing features.",
            trigger: '.o_portal_overview',
            position: 'bottom',
            run: function () {
                console.log('Tour started - Modern implementation');
            },
        },
        {
            content: "Here you can see your account statistics at a glance - boxes, documents, requests, and certificates.",
            trigger: '.stats-dashboard',
            position: 'bottom',
            run: function () {
                // Trigger counter animation if available
                const event = new CustomEvent('animateCounters');
                document.dispatchEvent(event);
            },
        },
        {
            content: "The Inventory Management feature lets you search and manage all your stored documents and boxes with advanced filtering.",
            trigger: '.feature-card:has(.fa-search)',
            position: 'right',
        },
        {
            content: "Generate instant quotes and manage billing with complete transparency. Update PO numbers and request changes easily.",
            trigger: '.feature-card:has(.fa-calculator)',
            position: 'left',
        },
        {
            content: "Submit service requests with electronic signatures and track them in real-time with our FSM integration.",
            trigger: '.feature-card:has(.fa-cogs)',
            position: 'right',
        },
        {
            content: "Manage users by importing CSV files, assigning access levels, and tracking all activity.",
            trigger: '.feature-card:has(.fa-users)',
            position: 'left',
        },
        {
            content: "Everything is NAID AAA certified with complete audit trails and compliance reporting.",
            trigger: '.feature-card:has(.fa-shield)',
            position: 'right',
            run: function () {
                // Highlight compliance badges
                document.querySelectorAll('.compliance-badges .badge').forEach(badge => {
                    badge.style.animation = 'pulse 1s infinite';
                });
            },
        },
        {
            content: "Future AI features will provide smart recommendations and predictive analytics based on your usage patterns.",
            trigger: '.feature-card:has(.fa-brain)',
            position: 'left',
        },
        {
            content: "Check your recent activity and smart suggestions for optimizing your records management workflow.",
            trigger: '.activity-section',
            position: 'top',
        },
        {
            content: "That's it! You're ready to explore your secure, enterprise-grade records management portal. Click anywhere to start using the system.",
            trigger: '.o_portal_overview',
            position: 'bottom',
        }
    ],
};

// Register the modern tour
try {
    registry.category("web_tour.tours").add("portal_overview_tour", portalOverviewTour);
} catch (err) {
    console.error('[portal_tour] Failed to register portal_overview_tour:', err.message);
}

// Portal Inventory Tour
const portalInventoryTour = {
    url: '/my/inventory',
    test: true,
    steps: () => [
        {
            content: "Welcome to Inventory Management! Use the Google-like search to find any document or box instantly.",
            trigger: '#global_search',
            position: 'bottom',
        },
        {
            content: "Apply advanced filters to narrow down your search results by type, status, location, and dates.",
            trigger: '.search-container .filter-section',
            position: 'bottom',
        },
        {
            content: "Select multiple items using checkboxes to perform bulk actions like destruction, pickup, or archiving.",
            trigger: '#select_all',
            position: 'right',
        },
        {
            content: "Use bulk actions to efficiently manage multiple items at once - a real time-saver!",
            trigger: '.bulk-actions-bar',
            position: 'top',
        },
        {
            content: "Click on any column header to sort your inventory by that field.",
            trigger: '.table th[data-sort]',
            position: 'bottom',
        },
        {
            content: "Export your filtered results to various formats for reporting and analysis.",
            trigger: '.export-dropdown',
            position: 'left',
        },
        {
            content: "Each item shows its current status with color-coded badges for quick visual identification.",
            trigger: '.status-badge',
            position: 'top',
        }
    ],
};

try {
    registry.category("web_tour.tours").add("portal_inventory_tour", portalInventoryTour);
} catch (err) {
    console.error('[portal_tour] Failed to register portal_inventory_tour:', err.message);
}

// Portal Functions for Overview Page
window.portalFunctions = {
    // Start the interactive tour
    startPortalTour: function() {
        console.log('Starting portal tour...');
        tourManager.startTour("portal_overview_tour", {
            mode: "manual"
        });
    },

    // Show video tutorial modal
    showVideoTour: function() {
        if (!hasJQuery) {
            console.warn('[portal_tour] jQuery not available; cannot display video tour modal.');
            return;
        }
        $('#videoTourModal').modal('show');
    },

    // Navigate to specific sections
    navigateToInventory: function() {
        window.location.href = '/my/inventory';
    },

    navigateToQuotes: function() {
        window.location.href = '/my/quotes';
    },

    navigateToRequests: function() {
        window.location.href = '/my/requests';
    },

    navigateToUsers: function() {
        window.location.href = '/my/users';
    },

    navigateToCompliance: function() {
        window.location.href = '/my/compliance';
    },

    // Start feature-specific tours
    startInventoryTour: function() {
        window.location.href = '/my/inventory?start_tour=1';
    },

    // Handle suggestion actions
    executeSuggestion: function(suggestionId) {
        console.log('Executing suggestion:', suggestionId);
        // This would be connected to actual suggestion logic
        switch(suggestionId) {
            case 'optimize_storage':
                this.navigateToInventory();
                break;
            case 'pending_requests':
                this.navigateToRequests();
                break;
            case 'update_billing':
                this.navigateToQuotes();
                break;
            default:
                console.log('Unknown suggestion:', suggestionId);
        }
    }
};

// Initialize tour triggers when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Bind tour button
    const tourButton = document.getElementById('start_portal_tour');
    if (tourButton) {
        tourButton.addEventListener('click', function() {
            window.portalFunctions.startPortalTour();
        });
    }

    // Bind video tutorial button
    const videoButton = document.getElementById('watch_video_tour');
    if (videoButton) {
        videoButton.addEventListener('click', function() {
            window.portalFunctions.showVideoTour();
        });
    }

    // Auto-start tour if URL parameter is present
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('start_tour') === '1') {
        setTimeout(() => {
            window.portalFunctions.startPortalTour();
        }, 1000);
    }

    // Animate stats counters
    const animateCounters = function() {
        const counters = document.querySelectorAll('.stat-card h3');
        counters.forEach(counter => {
            // Add null check to prevent textContent errors
            if (!counter || !counter.textContent) {
                return;
            }
            
            const target = parseInt(counter.textContent) || 0;
            const increment = target / 50;
            let current = 0;
            
            const timer = setInterval(() => {
                // Check if counter still exists before setting textContent
                if (!counter || !document.contains(counter)) {
                    clearInterval(timer);
                    return;
                }
                
                current += increment;
                if (current >= target) {
                    counter.textContent = target;
                    clearInterval(timer);
                } else {
                    counter.textContent = Math.ceil(current);
                }
            }, 20);
        });
    };

    // Start counter animation when stats are visible
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                statsObserver.unobserve(entry.target);
            }
        });
    });

    const statsSection = document.querySelector('.stats-dashboard');
    if (statsSection) {
        statsObserver.observe(statsSection);
    }

    // Add smooth scrolling to feature cards
    const featureCards = document.querySelectorAll('.feature-card a[href^="/my/"]');
    featureCards.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add a subtle loading animation
            this.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Loading...';
        });
    });

    // Make animateCounters available globally
    window.portalFunctions.animateCounters = animateCounters;
});

// Export for global access
window.startPortalTour = function() {
    window.portalFunctions.startPortalTour();
};

window.showVideoTour = function() {
    window.portalFunctions.showVideoTour();
};

console.log('Portal Tour module loaded successfully');
