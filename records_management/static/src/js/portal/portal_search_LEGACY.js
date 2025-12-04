/**
 * Portal Search Integration (Frontend Only)
 * For customer portal search functionality
 */

odoo.define("records_management.portal_search", ['web.public.widget', 'web.rpc'], function (require) {
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
        window.location.href = "/my/records/search?q=" + encodeURIComponent(query);
      }
    },
  });

  publicWidget.registry.PortalSearchWidget = PortalSearchWidget;

  return PortalSearchWidget;
});
