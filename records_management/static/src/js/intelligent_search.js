/** @odoo-module **/
/**
 * Intelligent Search Widget (Odoo 18 Compatible)
 * Simplified version to prevent asset bundle errors
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import rpc from 'web.rpc';
import AbstractField from 'web.AbstractField';

// Minimal compatible implementation
console.log("Intelligent Search module loaded (simplified version)");

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
  static template = "ContainerSearchWidget";
  static props = {
    ...standardFieldProps,
  };

  setup() {
    this.searchTimeout = null;
    this.suggestions = [];
    this.selectedIndex = -1;
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

      const result = await rpc.query({
        route: "/records/search/containers",
        params: {
          query: query,
          limit: 10,
          customer_id: customer_id,
        },
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
 * File Search Widget with Smart Recommendations (Legacy Widget)
 */
class FileSearchWidget extends AbstractField {
  init() {
    super.init(...arguments);
    this.recommendations = [];
  }

  /**
   * Search for files and get container recommendations
   */
  async onSearchFiles() {
    const searchParams = {
      file_name: this.fileNameInput?.value?.trim() || "",
      service_date: this.serviceDateInput?.value || "",
      content_type: this.contentTypeSelect?.value || "",
    };

    // Get customer_id from context or current record
    const partnerId = safeGetPartnerId(this.record);
    if (partnerId) {
      searchParams.customer_id = partnerId;
    }

    if (!searchParams.file_name && !searchParams.service_date) {
      this.displayNotification({
        title: _t("Search Required"),
        message: _t("Please enter a file name or service date to search."),
        type: "warning",
      });
      return;
    }

    try {
      const result = await rpc.query({
        route: "/records/search/recommend_containers",
        params: searchParams,
      });

      this.recommendations = result.recommendations || [];
      this.showRecommendations(result);
    } catch (error) {
      console.error("File search error:", error);
      this.displayNotification({
        title: _t("Search Error"),
        message: _t("Error occurred while searching for containers."),
        type: "danger",
      });
    }
  }

  /**
   * Show container recommendations
   */
  showRecommendations(result) {
    // Implementation depends on your template structure
    console.log("Showing recommendations:", this.recommendations);
  }

  /**
   * Handle recommendation selection
   */
  onSelectRecommendation(recommendation) {
    if (recommendation) {
      // Set the container value and trigger change
      this.setValue(recommendation.name);

      // Show success message
      this.displayNotification({
        title: _t("Container Selected"),
        message: _t("Selected container: ") + recommendation.name,
        type: "success",
      });
    }
  }

  setValue(value) {
    // Implementation for setting field value
    this.trigger_up("field_changed", {
      dataPointID: this.dataPointID,
      changes: {},
      value: value,
    });
  }
}

// Register the widgets
const fieldRegistry = registry.category("fields");

try {
  fieldRegistry.add("container_search", ContainerSearchWidget);
  fieldRegistry.add("file_search", FileSearchWidget);

  if (window && window.console) {
    console.debug("[IntelligentSearch] Widgets registered (container_search, file_search)");
  }
} catch (err) {
  console.error("[IntelligentSearch] Failed to register widgets", err);
}

export const IntelligentSearchWidgets = {
  ContainerSearchWidget,
  FileSearchWidget,
};
