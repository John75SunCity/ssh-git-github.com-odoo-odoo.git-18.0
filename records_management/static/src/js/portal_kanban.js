/**
 * Portal Kanban View Toggle
 * Handles switching between kanban and list views in the customer portal
 */

(function() {
    'use strict';

    // Store view preference in localStorage
    const VIEW_STORAGE_KEY = 'portal_view_preference';

    /**
     * Toggle between kanban and list views
     * @param {string} viewMode - 'kanban' or 'list'
     */
    window.togglePortalView = function(viewMode) {
        const kanbanView = document.querySelector('.portal-kanban-view');
        const listView = document.querySelector('.portal-list-view');
        const toggleButtons = document.querySelectorAll('.view-toggle-btn');

        if (!kanbanView || !listView) {
            console.warn('Portal view containers not found');
            return;
        }

        // Toggle visibility
        if (viewMode === 'kanban') {
            kanbanView.classList.remove('d-none');
            listView.classList.add('d-none');
        } else {
            kanbanView.classList.add('d-none');
            listView.classList.remove('d-none');
        }

        // Update button states
        toggleButtons.forEach(btn => {
            btn.classList.remove('active');
            if ((viewMode === 'kanban' && btn.querySelector('.fa-th-large')) ||
                (viewMode === 'list' && btn.querySelector('.fa-list'))) {
                btn.classList.add('active');
            }
        });

        // Store preference
        try {
            localStorage.setItem(VIEW_STORAGE_KEY + '_' + window.location.pathname, viewMode);
        } catch (e) {
            // localStorage not available
        }
    };

    /**
     * Initialize view based on stored preference or default
     */
    function initializeView() {
        let storedView = 'list'; // default
        
        try {
            const stored = localStorage.getItem(VIEW_STORAGE_KEY + '_' + window.location.pathname);
            if (stored) {
                storedView = stored;
            }
        } catch (e) {
            // localStorage not available
        }

        // Check if kanban view exists on this page
        const kanbanView = document.querySelector('.portal-kanban-view');
        if (kanbanView) {
            togglePortalView(storedView);
        }
    }

    /**
     * Handle keyboard shortcuts
     * - Press 'k' for kanban view
     * - Press 'l' for list view
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Don't trigger if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
                return;
            }

            if (e.key === 'k' || e.key === 'K') {
                togglePortalView('kanban');
            } else if (e.key === 'l' || e.key === 'L') {
                togglePortalView('list');
            }
        });
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeView();
            setupKeyboardShortcuts();
        });
    } else {
        initializeView();
        setupKeyboardShortcuts();
    }

})();
