/** @odoo-module **/
/**
 * Customer Portal Diagram View - Backend View Registration (Odoo 18)
 *
 * PURPOSE: Registers custom view type for Odoo backend (form/tree/kanban-like)
 * USE CASE: When viewing customer.portal.diagram model records in backend
 *
 * ARCHITECTURE (3-File System):
 * 1. THIS FILE (customer_portal_diagram_view.js) - Backend view registration
 * 2. customer_portal_diagram.js - Simplified Odoo 19 component placeholder
 * 3. portal_organization_diagram.js - Frontend portal widget (actual portal usage)
 *
 * DEPENDENCIES:
 * - vis.js library (loaded via asset bundle)
 * - AbstractView, AbstractController, AbstractRenderer (Odoo 18 patterns)
 *
 * PERFORMANCE OPTIMIZATIONS:
 * - Batch DOM updates for statistics
 * - Optimized canvas export with cleanup
 * - Graceful fallbacks for missing data/libraries
 * - Better error handling with detailed logging
 *
 * NOTE: Uses legacy .extend() pattern for Odoo 18 compatibility
 * (OWL Component conversion blocked due to vis.js global dependency)
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { AbstractController } from "@web/mvc/controller/abstract_controller";
import { AbstractRenderer } from "@web/mvc/renderer/abstract_renderer";
import { AbstractView } from "@web/mvc/view/abstract_view";

const viewRegistry = registry.category("views");

    /**
     * Customer Portal Diagram Controller
     */
    var CustomerPortalDiagramController = AbstractController.extend({
      events: {
        "click .o_refresh_diagram": "_onRefreshClick",
        "click .o_export_diagram": "_onExportClick",
        "change .o_layout_select": "_onLayoutChange",
        "click .o_search_button": "_onSearchClick",
        "keyup .o_search_input": "_onSearchKeyup",
      },

      init: function (parent, model, renderer, params) {
        this._super.apply(this, arguments);
        this.searchQuery = "";
        this.layoutType = "hierarchical";
      },

      _onRefreshClick: function (event) {
        event.preventDefault();
        this.renderer.refreshDiagram();
      },

      _onExportClick: function (event) {
        event.preventDefault();
        this.renderer.exportDiagram();
      },

      _onLayoutChange: function (event) {
        this.layoutType = event.target.value;
        this.renderer.updateLayout(this.layoutType);
      },

      _onSearchClick: function (event) {
        event.preventDefault();
        this._performSearch();
      },

      _onSearchKeyup: function (event) {
        if (event.keyCode === 13) {
          this._performSearch();
        }
      },

      _performSearch: function () {
        const searchInput = this.el.querySelector(".o_search_input");
        this.searchQuery = searchInput ? searchInput.value.trim() : "";
        if (this.renderer && typeof this.renderer.updateSearch === 'function') {
          this.renderer.updateSearch(this.searchQuery);
        }
      },
    });

    /**
     * Customer Portal Diagram Renderer
     */
    var CustomerPortalDiagramRenderer = AbstractRenderer.extend({
      template: "CustomerPortalDiagramTemplate",

      init: function (parent, state, params) {
        this._super.apply(this, arguments);
        this.network = null;
      },

      start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
          self._initializeDiagram();
        });
      },

      _initializeDiagram: function () {
        var self = this;

        // Get data from the model
        var record = this.state.data;
        if (!record || !record.node_data || !record.edge_data) {
          console.warn("[DiagramView] No diagram data available - fields may not be loaded");
          return;
        }

        try {
          // Parse JSON with validation
          var nodesStr = record.node_data.value || "[]";
          var edgesStr = record.edge_data.value || "[]";
          var nodes = JSON.parse(nodesStr);
          var edges = JSON.parse(edgesStr);

          if (!Array.isArray(nodes) || !Array.isArray(edges)) {
            throw new Error("Invalid data format: expected arrays");
          }

          var container = this.el.querySelector(".o_diagram_container");
          // Check if vis.js is available
          if (typeof window.vis === 'undefined') {
            console.error("vis.js library is not loaded");
            return;
          }

          var data = {
            nodes: new window.vis.DataSet(nodes),
            edges: new window.vis.DataSet(edges),
          };

          var options = this._getNetworkOptions();
          this.network = new window.vis.Network(container, data, options);
          this._setupNetworkEvents();
        } catch (error) {
          console.error("Error initializing portal diagram:", error);
        }
      },

      _getNetworkOptions: function () {
        return {
          layout: {
            hierarchical: {
              direction: "UD",
              sortMethod: "directed",
              nodeSpacing: 150,
              levelSeparation: 200,
            },
          },
          physics: {
            enabled: false,
          },
          interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
          },
          nodes: {
            borderWidth: 2,
            shadow: true,
            font: { size: 14 },
          },
          edges: {
            arrows: { to: { enabled: true } },
            smooth: { enabled: true },
          },
        };
      },

      _setupNetworkEvents: function () {
        var self = this;

        this.network.on("click", function (params) {
          if (params.nodes.length > 0) {
            self._onNodeClick(params.nodes[0]);
          }
        });
      },

      _onNodeClick: function (nodeId) {
        console.log("Portal diagram node clicked:", nodeId);
        // Handle node click - could open details or messaging
      },

      refreshDiagram: function () {
        if (this.network) {
          this.network.redraw();
        }
      },

      updateLayout: function (layoutType) {
        if (!this.network) return;

        var options = {
          layout: {
            hierarchical:
              layoutType === "hierarchical"
                ? {
                    direction: "UD",
                    sortMethod: "directed",
                  }
                : false,
          },
          physics: {
            enabled: layoutType !== "hierarchical",
          },
        };

        this.network.setOptions(options);
      },

      updateSearch: function (searchQuery) {
        console.log("Portal diagram search:", searchQuery);
        // Implement search filtering
      },

      exportDiagram: function () {
        if (!this.network) {
          console.warn("[DiagramView] Cannot export: network not initialized");
          return;
        }

        try {
          var canvas = this.network.canvas.getContext("2d").canvas;
          var dataURL = canvas.toDataURL("image/png");
          var link = document.createElement("a");
          link.download = "organization_diagram_" + Date.now() + ".png";
          link.href = dataURL;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        } catch (error) {
          console.error("[DiagramView] Export failed:", error);
        }
      },
    });

    /**
     * Customer Portal Diagram View
     */
    var CustomerPortalDiagramView = AbstractView.extend({
      display_name: _t("Portal Organization Diagram"),
      icon: "fa-sitemap",
      config: Object.assign({}, AbstractView.prototype.config, {
        Controller: CustomerPortalDiagramController,
        Renderer: CustomerPortalDiagramRenderer,
      }),
      viewType: "customer_portal_diagram",

      init: function (viewInfo, params) {
        this._super.apply(this, arguments);
      },
    });

// Register the view
viewRegistry.add("customer_portal_diagram", CustomerPortalDiagramView);

// Export for potential reuse
export {
  CustomerPortalDiagramView,
  CustomerPortalDiagramController,
  CustomerPortalDiagramRenderer,
};
