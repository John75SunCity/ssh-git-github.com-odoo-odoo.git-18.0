/**
 * Intelligent Search Widget for Records Management
 *
 * Provides intelligent auto-suggestion and search functionality for:
 * - Container/box number auto-complete
 * - File search with smart container recommendations
 * - Portal and backend integration
 */

odoo.define("records_management.intelligent_search", function (require) {
  "use strict";

  var AbstractField = require("web.AbstractField");
  var core = require("web.core");
  var field_registry = require("web.field_registry");
  var rpc = require("web.rpc");

  var QWeb = core.qweb;
  var _t = core._t;

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
  field_registry.add("container_search", ContainerSearchWidget);
  field_registry.add("file_search", FileSearchWidget);

  return {
    ContainerSearchWidget: ContainerSearchWidget,
    FileSearchWidget: FileSearchWidget,
  };
});

/**
 * Portal Search Integration
 * For customer portal search functionality
 */
odoo.define("records_management.portal_search", function (require) {
  "use strict";

  var publicWidget = require("web.public.widget");
  var rpc = require("web.rpc");

  var PortalSearchWidget = publicWidget.Widget.extend({
    selector: ".portal-search-container",

    events: {
      "input .portal-search-input": "_onSearchInput",
      "click .search-suggestion": "_onSelectSuggestion",
      "submit .portal-search-form": "_onSearchSubmit",
    },

    init: function () {
      this._super.apply(this, arguments);
      this.searchTimeout = null;
    },

    /**
     * Handle search input with debouncing
     */
    _onSearchInput: function (event) {
      var self = this;
      var query = event.target.value.trim();

      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      this.searchTimeout = setTimeout(function () {
        if (query.length >= 2) {
          self._performPortalSearch(query);
        } else {
          self._hideSuggestions();
        }
      }, 300);
    },

    /**
     * Perform portal search
     */
    _performPortalSearch: function (query) {
      var self = this;

      rpc
        .query({
          route: "/my/records/search",
          params: {
            query: query,
          },
        })
        .then(function (result) {
          self._showPortalSuggestions(result);
        })
        .catch(function (error) {
          console.error("Portal search error:", error);
        });
    },

    /**
     * Show portal search suggestions
     */
    _showPortalSuggestions: function (result) {
      var $suggestions = this.$(".search-suggestions");
      $suggestions.empty();

      var suggestions = result.suggestions || result.recommendations || [];

      if (suggestions.length === 0) {
        $suggestions.hide();
        return;
      }

      suggestions.forEach(function (suggestion) {
        var $item = $(
          '<div class="search-suggestion p-2 border-bottom">' +
            "<strong>" +
            suggestion.name +
            "</strong><br>" +
            '<small class="text-muted">' +
            (suggestion.description || "") +
            "</small>" +
            "</div>"
        );
        $item.data("suggestion", suggestion);
        $suggestions.append($item);
      });

      $suggestions.show();
    },

    /**
     * Hide suggestions
     */
    _hideSuggestions: function () {
      this.$(".search-suggestions").hide();
    },

    /**
     * Handle suggestion selection
     */
    _onSelectSuggestion: function (event) {
      var suggestion = $(event.currentTarget).data("suggestion");
      this.$(".portal-search-input").val(suggestion.name);
      this._hideSuggestions();
    },

    /**
     * Handle search form submission
     */
    _onSearchSubmit: function (event) {
      event.preventDefault();
      var query = this.$(".portal-search-input").val().trim();

      if (query) {
        // Redirect to search results page or update current page
        window.location.href =
          "/my/records/search?q=" + encodeURIComponent(query);
      }
    },
  });

  publicWidget.registry.PortalSearchWidget = PortalSearchWidget;

  return PortalSearchWidget;
});
