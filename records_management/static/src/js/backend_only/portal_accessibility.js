/** @odoo-module **/
(() => {
    "use strict";

    const normalizeLanguage = () => {
        const odooNamespace = window.odoo || {};
        const sessionInfo = odooNamespace.session_info || odooNamespace._session_info || {};
        const context = sessionInfo.user_context || {};
        const rawLang = context.lang || sessionInfo.lang || (window.navigator && window.navigator.language) || "en";
        return String(rawLang).replace(/_/g, "-");
    };

    const sanitizeViewportMeta = (meta) => {
        const content = meta.getAttribute("content") || "";
        const parts = content
            .split(",")
            .map((part) => part.trim())
            .filter((part) => part && !/^user\s*-\s*scalable\s*=\s*/i.test(part));

        if (!parts.length) {
            parts.push("width=device-width", "initial-scale=1");
        } else {
            if (!parts.some((part) => /^width\s*=/.test(part))) {
                parts.unshift("width=device-width");
            }
            if (!parts.some((part) => /^initial\s*-\s*scale\s*=/.test(part))) {
                parts.push("initial-scale=1");
            }
        }

        meta.setAttribute("content", parts.join(", "));
    };

    const ensureIframeTitles = () => {
        const applyTitle = (selector, title) => {
            document.querySelectorAll(selector).forEach((iframe) => {
                if (!iframe.getAttribute("title")) {
                    iframe.setAttribute("title", title);
                }
            });
        };

        applyTitle("iframe.o_ignore_in_tour", "Portal preview fallback frame");
        applyTitle("iframe.o_iframe", "Website preview frame");
    };

    const adjustSystray = () => {
        document.querySelectorAll(".o_menu_systray").forEach((systray) => {
            systray.setAttribute("role", "navigation");
            if (!systray.getAttribute("aria-label")) {
                systray.setAttribute("aria-label", "Portal utility navigation");
            }
            systray.querySelectorAll("button:not([type])").forEach((button) => {
                button.setAttribute("type", "button");
            });
        });
    };

    const applyAccessibilityFixes = () => {
        try {
            const html = document.documentElement;
            if (html && !html.getAttribute("lang")) {
                const normalizedLang = normalizeLanguage();
                html.setAttribute("lang", normalizedLang);
                html.setAttribute("xml:lang", normalizedLang);
            }
        } catch (error) {
            // Silent fallback: do not interrupt page rendering on failure.
        }

        const viewportMeta = document.querySelector('meta[name="viewport"]');
        if (viewportMeta) {
            sanitizeViewportMeta(viewportMeta);
        }

        ensureIframeTitles();
        adjustSystray();
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyAccessibilityFixes, { once: true });
    } else {
        applyAccessibilityFixes();
    }
})();
