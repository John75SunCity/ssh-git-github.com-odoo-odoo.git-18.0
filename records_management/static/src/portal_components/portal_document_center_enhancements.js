/** @odoo-module **/
/**
 * Supplemental behavior for legacy fallback inside Document Center page.
 * Modern Owl component covers primary UX; this keeps graceful degradation.
 */
import { onMounted } from "@odoo/owl";

function initLegacyDocumentCenter() {
    const tabsView = document.getElementById('tabsViewContainer');
    const accordionView = document.getElementById('accordionViewContainer');
    if (!tabsView || !accordionView) {
        return; // Legacy block hidden or removed
    }
    function toggleView(viewType) {
        const toggleButtons = document.querySelectorAll('.view-toggle .btn');
        toggleButtons.forEach(btn => btn.classList.remove('active'));
        if (viewType === 'accordion') {
            tabsView.style.display = 'none';
            accordionView.style.display = 'block';
            const btn = document.querySelector('[data-docs-view="accordion"]');
            if (btn) btn.classList.add('active');
            setTimeout(() => {
                document.querySelectorAll('.accordion .card').forEach((card, index) => {
                    card.style.opacity = '0';
                    card.style.transform = 'translateY(20px)';
                    setTimeout(() => {
                        card.style.transition = 'all 0.5s ease';
                        card.style.opacity = '1';
                        card.style.transform = 'translateY(0)';
                    }, index * 100);
                });
            }, 50);
        } else {
            tabsView.style.display = 'block';
            accordionView.style.display = 'none';
            const btn = document.querySelector('[data-docs-view="tabs"]');
            if (btn) btn.classList.add('active');
        }
        localStorage.setItem('docsCenterView', viewType);
    }

    function toggleTimelineView() {
        const timelineView = document.getElementById('timelineView');
        const listView = document.getElementById('listView');
        const toggleBtn = document.getElementById('timelineToggle');
        if (!timelineView || !listView || !toggleBtn) return;
        const showingTimeline = timelineView.style.display !== 'none';
        if (showingTimeline) {
            timelineView.style.display = 'none';
            listView.style.display = 'block';
            toggleBtn.innerHTML = '<i class="fa fa-clock-o"></i> Timeline View';
            toggleBtn.classList.remove('btn-info');
            toggleBtn.classList.add('btn-outline-info');
        } else {
            timelineView.style.display = 'block';
            listView.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fa fa-list"></i> List View';
            toggleBtn.classList.remove('btn-outline-info');
            toggleBtn.classList.add('btn-info');
        }
    }

    function exportAllDocs(ev) {
        const btn = ev?.currentTarget;
        const exportData = { invoices: [], quotes: [], certificates: [], communications: [] };
        if (btn) {
            const original = btn.innerHTML;
            btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Preparing Export...';
            btn.disabled = true;
            setTimeout(() => {
                btn.innerHTML = original;
                btn.disabled = false;
                const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'documents_export_' + new Date().toISOString().split('T')[0] + '.json';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 1500);
        }
    }

    // Wire buttons (using data attributes to avoid inline JS)
    document.querySelectorAll('[data-docs-view]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            toggleView(btn.getAttribute('data-docs-view'));
        });
    });
    const timelineToggle = document.getElementById('timelineToggle');
    if (timelineToggle) timelineToggle.addEventListener('click', (e) => { e.preventDefault(); toggleTimelineView(); });
    document.querySelectorAll('[data-export-docs]')
        .forEach(b => b.addEventListener('click', exportAllDocs));

    // Smooth scroll for accordion button-links
    document.querySelectorAll('.accordion .btn-link').forEach(btn => {
        btn.addEventListener('click', function() {
            setTimeout(() => {
                this.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 350);
        });
    });

    // Initialize view
    const initialView = localStorage.getItem('docsCenterView') || 'tabs';
    toggleView(initialView);
}

// If Owl already bootstrapped, run when DOM ready as a side-effect module.
document.addEventListener('DOMContentLoaded', () => initLegacyDocumentCenter());

// Export for potential unit testing
export { initLegacyDocumentCenter };
