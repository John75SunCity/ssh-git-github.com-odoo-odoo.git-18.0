/** @odoo-module **/
/**
 * Intelligent Search Widget (Odoo 18 Compatible)
 * Simplified version to prevent asset bundle errors
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

// Minimal compatible implementation
console.log("Intelligent Search module loaded (simplified version)");

class IntelligentSearchComponent extends Component {
    static template = `<div class="o_intelligent_search">
        <input type="text" placeholder="Search containers..." class="form-control"/>
    </div>`;
    static props = [...standardFieldProps];
}

// Register the component
registry.category("fields").add("intelligent_search", IntelligentSearchComponent);

// Defensive helpers ---------------------------------------------------------
function safeGetPartnerId(record) {
  try {
    if (!record || !record.data || !record.data.partner_id) {
      return null;
    }
    const partnerRaw = record.data.partner_id;
    // Many2one in the web client can be either an object {data:{id:..}} or the id itself
    if (partnerRaw && partnerRaw.data && partnerRaw.data.id) {
      return partnerRaw.data.id;
    }
    if (typeof partnerRaw === "number") {
      return partnerRaw;
    }
    if (Array.isArray(partnerRaw) && partnerRaw.length) {
      return partnerRaw[0];
    }
  } catch (err) {
    console.warn("[IntelligentSearch] Failed to extract partner id", err);
  }
  return null;
}

function toggleVisible($el, show) {
  if (!$el) return;
  if (show) {
    $el.removeClass("d-none");
  } else {
    $el.addClass("d-none");
  }
}

/**
 * Container Number Auto-Complete Widget (OWL Component)
 */
class ContainerSearchWidget extends Component {
  static template = `<div class="o_container_search">
    <input type="text" placeholder="Search containers..." class="form-control" 
           t-on-input="onSearchInput" t-on-keydown="onKeyDown"/>
    <div class="suggestions" t-if="suggestions.length">
      <div t-foreach="suggestions" t-as="suggestion" t-key="suggestion.id"
           class="suggestion-item" t-on-click="() => onSelectSuggestion(suggestion)">
        <span t-esc="suggestion.name"/>
      </div>
    </div>
  </div>`;
  static props = {
    ...standardFieldProps,
  };

  setup() {
    this.searchTimeout = null;
    this.suggestions = [];
    this.selectedIndex = -1;
    this.rpc = useService("rpc");
  }

  /**
   * Handle input changes with debouncing
   */
  onSearchInput(event) {
    const query = event.target.value.trim();

    // Clear previous timeout
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }

    // Debounce search requests
    this.searchTimeout = setTimeout(() => {
      if (query.length >= 1) {
        this.performSearch(query);
      } else {
        this.hideSuggestions();
      }
    }, 300);
  }

  /**
   * Perform search and show suggestions
   */
  async performSearch(query) {
    try {
      // Defensive partner extraction
      const customer_id = safeGetPartnerId(this.props.record);

      const result = await this.rpc("/records/search/containers", {
        query: query,
        limit: 10,
        customer_id: customer_id,
      });

      this.suggestions = result.suggestions || [];
      this.showSuggestions();
    } catch (error) {
      console.error("Search error:", error);
      this.hideSuggestions();
    }
  }

  /**
   * Show suggestions dropdown
   */
  showSuggestions() {
    // Implementation would depend on your template structure
    // This is a simplified version
    console.log("Showing suggestions:", this.suggestions);
  }

  /**
   * Hide suggestions dropdown
   */
  hideSuggestions() {
    this.suggestions = [];
    this.selectedIndex = -1;
  }

  /**
   * Handle suggestion selection
   */
  onSelectSuggestion(suggestion) {
    if (suggestion) {
      this.props.update(suggestion.name);
      this.hideSuggestions();
    }
  }

  /**
   * Handle keyboard navigation
   */
  onKeyDown(event) {
    if (!this.suggestions.length) return;

    switch (event.keyCode) {
      case 38: // Up arrow
        event.preventDefault();
        this.selectedIndex = Math.max(0, this.selectedIndex - 1);
        this.highlightSuggestion();
        break;
      case 40: // Down arrow
        event.preventDefault();
        this.selectedIndex = Math.min(
          this.suggestions.length - 1,
          this.selectedIndex + 1
        );
        this.highlightSuggestion();
        break;
      case 13: // Enter
        event.preventDefault();
        if (this.selectedIndex >= 0) {
          const suggestion = this.suggestions[this.selectedIndex];
          this.onSelectSuggestion(suggestion);
        }
        break;
      case 27: // Escape
        this.hideSuggestions();
        break;
    }
  }

  /**
   * Highlight selected suggestion
   */
  highlightSuggestion() {
    // Implementation depends on template structure
    console.log("Highlighting suggestion:", this.selectedIndex);
  }
}

/**
 * File Search Widget (Simplified OWL Component)
 */
class FileSearchWidget extends Component {
  static template = `<div class="o_file_search">
    <input type="text" placeholder="Search files..." class="form-control"/>
    <p class="text-muted mt-2">File search functionality simplified for compatibility</p>
  </div>`;
  static props = {
    ...standardFieldProps,
  };

  setup() {
    this.rpc = useService("rpc");
  }
}

// Register the widgets
const fieldRegistry = registry.category("fields");

try {
  fieldRegistry.add("container_search", ContainerSearchWidget);
  fieldRegistry.add("file_search", FileSearchWidget);

  console.log("[IntelligentSearch] Widgets registered successfully");
} catch (err) {
  console.error("[IntelligentSearch] Failed to register widgets", err);
}
