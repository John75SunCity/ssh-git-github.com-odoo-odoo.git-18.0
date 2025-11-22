/**
 * Records Management Portal dashboard bootstrapper.
 *
 * Injects portal dashboard cards if the server-rendered template was
 * superseded by a Website Builder override. This script mirrors the
 * data provided via the controller when the dashboard renders normally.
 */
odoo.define('records_management.portal_dashboard_bootstrap', ['@web/core/utils/ajax'], function (require) {
    'use strict';

    const ajax = require('@web/core/utils/ajax');

    /**
     * Render a single dashboard card into a DOM node.
     * @param {Object} card - Card payload from the controller endpoint.
     * @returns {HTMLElement}
     */
    function createCard(card) {
        const column = document.createElement('div');
        column.className = 'col-12 col-md-6 col-xl-4';

        const cardWrapper = document.createElement('div');
        const highlight = card.key === 'help' ? ' border-info border-2' : '';
        cardWrapper.className = `card h-100 shadow-sm border-0${highlight}`;

        const body = document.createElement('div');
        body.className = 'card-body d-flex flex-column';

        const header = document.createElement('div');
        header.className = 'd-flex align-items-start mb-2';

        if (card.icon_class) {
            const iconWrapper = document.createElement('span');
            iconWrapper.className = 'me-2';
            const icon = document.createElement('i');
            icon.className = card.icon_class;
            iconWrapper.appendChild(icon);
            header.appendChild(iconWrapper);
        }

        const title = document.createElement('h5');
        title.className = 'card-title mb-0';
        if (card.title && title.textContent !== undefined) {
            title.textContent = card.title;
        }
        header.appendChild(title);
        body.appendChild(header);

        const description = document.createElement('p');
        description.className = 'card-text text-muted small flex-grow-1';
        if (description.textContent !== undefined) {
            description.textContent = card.description || '';
        }
        body.appendChild(description);

        if (card.type === 'summary') {
            const footerRow = document.createElement('div');
            footerRow.className = 'd-flex justify-content-between align-items-center mt-2';

            const badge = card.badge || {};
            if (badge.value) {
                const badgeEl = document.createElement('span');
                badgeEl.className = 'badge bg-info text-white';
                if (badgeEl.textContent !== undefined) {
                    badgeEl.textContent = `${badge.value} ${badge.label || ''}`.trim();
                }
                footerRow.appendChild(badgeEl);
            } else if (badge.empty_label) {
                const emptyBadge = document.createElement('span');
                emptyBadge.className = 'badge bg-secondary';
                if (emptyBadge.textContent !== undefined) {
                    emptyBadge.textContent = badge.empty_label;
                }
                footerRow.appendChild(emptyBadge);
            }

            const primaryButton = (card.buttons || [])[0];
            if (primaryButton) {
                const button = document.createElement('a');
                button.href = primaryButton.url;
                button.className = primaryButton.classes || 'btn btn-sm btn-primary';
                if (primaryButton.icon_class) {
                    const btnIcon = document.createElement('i');
                    btnIcon.className = primaryButton.icon_class;
                    button.appendChild(btnIcon);
                    button.appendChild(document.createTextNode(' '));
                }
                button.appendChild(document.createTextNode(primaryButton.label));
                footerRow.appendChild(button);
            }

            body.appendChild(footerRow);
        } else if (card.type === 'button_group') {
            const btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group-vertical w-100 mt-3 gap-2';
            (card.buttons || []).forEach((buttonInfo) => {
                const button = document.createElement('a');
                button.href = buttonInfo.url;
                button.className = buttonInfo.classes || 'btn btn-sm btn-primary';
                if (buttonInfo.icon_class) {
                    const btnIcon = document.createElement('i');
                    btnIcon.className = buttonInfo.icon_class;
                    button.appendChild(btnIcon);
                    button.appendChild(document.createTextNode(' '));
                }
                button.appendChild(document.createTextNode(buttonInfo.label));
                btnGroup.appendChild(button);
            });
            body.appendChild(btnGroup);
        }

        cardWrapper.appendChild(body);
        column.appendChild(cardWrapper);
        return column;
    }

    /**
     * Inject the cards into the dashboard container.
     * @param {Array<Object>} cards
     */
    function renderCards(cards) {
        const existingContainer = document.querySelector('.o_rm_portal_cards');
        if (existingContainer && existingContainer.children.length) {
            return;
        }

        let container = existingContainer;
        if (!container) {
            const docsNode = document.querySelector('.o_portal_docs');
            if (!docsNode || !docsNode.parentNode) {
                return;
            }
            container = document.createElement('div');
            container.className = 'row o_rm_portal_cards g-3 mb-4';
            docsNode.parentNode.insertBefore(container, docsNode);
        }

        cards.forEach((card) => {
            container.appendChild(createCard(card));
        });
    }

    function bootstrapDashboard() {
        ajax.jsonRpc('/records_management/portal/dashboard_cards', 'call', {})
            .then((payload) => {
                if (!payload || !payload.cards || !payload.cards.length) {
                    return;
                }
                renderCards(payload.cards);
            })
            .catch(() => {
                // Silently ignore failures; the server-rendered fallback remains.
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrapDashboard);
    } else {
        bootstrapDashboard();
    }
});
