/** @odoo-module **/
/**
 * Intelligent Search Widget (ESM Conversion)
 * - Converted from legacy AMD (odoo.define) to ESM module standard
 * - Ready for OWL/env migration if needed later
 * - Retains jQuery-based DOM logic for minimal diff risk
 *
 * TODO (future): Convert to OWL Component and leverage useService('rpc')
 */

import { registry } from "@web/core/registry";
import { AbstractField } from "@web/views/fields/abstract_field";
import { _t } from "@web/core/l10n/translation";
import rpc from "@web/core/network/rpc_service";
import { qweb as QWeb } from "@web/core/qweb";

const fieldRegistry = registry.category("fields");

  /**
   * Container Number Auto-Complete Widget
   */
  var ContainerSearchWidget = AbstractField.extend({
    template: "ContainerSearchWidget",
    className: "o_field_container_search",

    events: {
      "input .container-search-input": "_onSearchInput",
      "click .suggestion-item": "_onSelectSuggestion",
      "keydown .container-search-input": "_onKeyDown",
    },

    init: function () {
      this._super.apply(this, arguments);
      this.searchTimeout = null;
      this.suggestions = [];
      this.selectedIndex = -1;
    },

    _render: function () {
      this.$input = this.$(".container-search-input");
      this.$suggestions = this.$(".search-suggestions");

      // Set current value
      if (this.value) {
        this.$input.val(this.value);
      }

      return this._super.apply(this, arguments);
    },

    /**
     * Handle input changes with debouncing
     */
    _onSearchInput: function (event) {
      var self = this;
      var query = event.target.value.trim();

      // Clear previous timeout
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      // Debounce search requests
      this.searchTimeout = setTimeout(function () {
        if (query.length >= 1) {
          self._performSearch(query);
        } else {
          self._hideSuggestions();
        }
      }, 300);
    },

    /**
     * Perform search and show suggestions
     */
    _performSearch: function (query) {
      var self = this;

      // Get customer_id from context or current record
      var customer_id = null;
      if (this.record && this.record.data.partner_id) {
        customer_id = this.record.data.partner_id.data
          ? this.record.data.partner_id.data.id
          : this.record.data.partner_id;
      }

      rpc
        .query({
          route: "/records/search/containers",
          params: {
            query: query,
            limit: 10,
            customer_id: customer_id,
          },
        })
        .then(function (result) {
          self.suggestions = result.suggestions || [];
          self._showSuggestions();
        })
        .catch(function (error) {
          console.error("Search error:", error);
          self._hideSuggestions();
        });
    },

    /**
     * Show suggestions dropdown
     */
    _showSuggestions: function () {
      var self = this;
      this.$suggestions.empty();

      if (this.suggestions.length === 0) {
        this.$suggestions.hide();
        return;
      }

      this.suggestions.forEach(function (suggestion, index) {
        var $item = $(
          QWeb.render("ContainerSuggestionItem", {
            suggestion: suggestion,
            index: index,
          })
        );

        self.$suggestions.append($item);
      });

      this.$suggestions.show();
      this.selectedIndex = -1;
    },

    /**
     * Hide suggestions dropdown
     */
    _hideSuggestions: function () {
      this.$suggestions.hide();
      this.suggestions = [];
      this.selectedIndex = -1;
    },

    /**
     * Handle suggestion selection
     */
    _onSelectSuggestion: function (event) {
      var index = $(event.currentTarget).data("index");
      var suggestion = this.suggestions[index];

      if (suggestion) {
        this.$input.val(suggestion.name);
        this._setValue(suggestion.name);
        this._hideSuggestions();
      }
    },

    /**
     * Handle keyboard navigation
     */
    _onKeyDown: function (event) {
      if (!this.suggestions.length) return;

      switch (event.keyCode) {
        case 38: // Up arrow
          event.preventDefault();
          this.selectedIndex = Math.max(0, this.selectedIndex - 1);
          this._highlightSuggestion();
          break;
        case 40: // Down arrow
          event.preventDefault();
          this.selectedIndex = Math.min(
            this.suggestions.length - 1,
            this.selectedIndex + 1
          );
          this._highlightSuggestion();
          break;
        case 13: // Enter
          event.preventDefault();
          if (this.selectedIndex >= 0) {
            var suggestion = this.suggestions[this.selectedIndex];
            this.$input.val(suggestion.name);
            this._setValue(suggestion.name);
            this._hideSuggestions();
          }
          break;
        case 27: // Escape
          this._hideSuggestions();
          break;
      }
    },

    /**
     * Highlight selected suggestion
     */
    _highlightSuggestion: function () {
      this.$suggestions.find(".suggestion-item").removeClass("selected");
      if (this.selectedIndex >= 0) {
        this.$suggestions
          .find(".suggestion-item")
          .eq(this.selectedIndex)
          .addClass("selected");
      }
    },

    /**
     * Set field value
     */
    _setValue: function (value) {
      this._super(value);
      this.trigger_up("field_changed", {
        dataPointID: this.dataPointID,
        changes: {},
        value: value,
      });
    },
  });

  /**
   * File Search Widget with Smart Recommendations
   */
  var FileSearchWidget = AbstractField.extend({
    template: "FileSearchWidget",
    className: "o_field_file_search",

    events: {
      "click .search-files-btn": "_onSearchFiles",
      "click .recommended-container": "_onSelectRecommendation",
      "input .file-name-input": "_onFileNameChange",
      "input .service-date-input": "_onServiceDateChange",
    },

    init: function () {
      this._super.apply(this, arguments);
      this.recommendations = [];
    },

    _render: function () {
      this.$fileNameInput = this.$(".file-name-input");
      this.$serviceDateInput = this.$(".service-date-input");
      this.$contentTypeSelect = this.$(".content-type-select");
      this.$recommendations = this.$(".search-recommendations");

      return this._super.apply(this, arguments);
    },

    /**
     * Search for files and get container recommendations
     */
    _onSearchFiles: function () {
      var self = this;

      var searchParams = {
        file_name: this.$fileNameInput.val().trim(),
        service_date: this.$serviceDateInput.val(),
        content_type: this.$contentTypeSelect.val(),
      };

      // Get customer_id from context or current record
      if (this.record && this.record.data.partner_id) {
        searchParams.customer_id = this.record.data.partner_id.data
          ? this.record.data.partner_id.data.id
          : this.record.data.partner_id;
      }

      if (!searchParams.file_name && !searchParams.service_date) {
        this.displayNotification({
          title: _t("Search Required"),
          message: _t("Please enter a file name or service date to search."),
          type: "warning",
        });
        return;
      }

      rpc
        .query({
          route: "/records/search/recommend_containers",
          params: searchParams,
        })
        .then(function (result) {
          self.recommendations = result.recommendations || [];
          self._showRecommendations(result);
        })
        .catch(function (error) {
          console.error("File search error:", error);
          self.displayNotification({
            title: _t("Search Error"),
            message: _t("Error occurred while searching for containers."),
            type: "danger",
          });
        });
    },

    /**
     * Show container recommendations
     */
    _showRecommendations: function (result) {
      var self = this;
      this.$recommendations.empty();

      if (this.recommendations.length === 0) {
        this.$recommendations.html(
          '<div class="alert alert-info">No containers found matching your search criteria.</div>'
        );
        return;
      }

      // Add search summary
      var searchSummary = QWeb.render("FileSearchSummary", {
        total: result.total,
        criteria: result.search_criteria,
      });
      this.$recommendations.append(searchSummary);

      // Add recommendations
      this.recommendations.forEach(function (recommendation, index) {
        var $item = $(
          QWeb.render("ContainerRecommendationItem", {
            recommendation: recommendation,
            index: index,
          })
        );

        self.$recommendations.append($item);
      });
    },

    /**
     * Handle recommendation selection
     */
    _onSelectRecommendation: function (event) {
      var index = $(event.currentTarget).data("index");
      var recommendation = this.recommendations[index];

      if (recommendation) {
        // Set the container value and trigger change
        this._setValue(recommendation.name);

        // Show success message
        this.displayNotification({
          title: _t("Container Selected"),
          message: _t("Selected container: ") + recommendation.name,
          type: "success",
        });
      }
    },

    _onFileNameChange: function () {
      // Clear recommendations when search criteria changes
      this.$recommendations.empty();
    },

    _onServiceDateChange: function () {
      // Clear recommendations when search criteria changes
      this.$recommendations.empty();
    },

    _setValue: function (value) {
      this._super(value);
      this.trigger_up("field_changed", {
        dataPointID: this.dataPointID,
        changes: {},
        value: value,
      });
    },
  });

  // Register the widgets
fieldRegistry.add("container_search", ContainerSearchWidget);
fieldRegistry.add("file_search", FileSearchWidget);

export const IntelligentSearchWidgets = {
  ContainerSearchWidget,
  FileSearchWidget,
};
