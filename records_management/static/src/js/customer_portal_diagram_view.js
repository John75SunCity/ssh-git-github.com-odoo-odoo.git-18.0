/** @odoo-module **/
/**
 * Customer Portal Diagram View (ESM Conversion)
 * Converted from legacy AMD to modern ESM view registration.
 * NOTE: Still uses global vis.js (provided via asset bundle) until refactored.
 */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AbstractView } from "@web/views/abstract_view";
import { AbstractRenderer } from "@web/views/abstract_renderer";
import { AbstractController } from "@web/views/abstract_controller";

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
        this.layoutType = $(event.target).val();
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
        this.searchQuery = this.$(".o_search_input").val();
        this.renderer.updateSearch(this.searchQuery);
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
          console.error("No diagram data available");
          return;
        }

        try {
          var nodes = JSON.parse(record.node_data.value || "[]");
          var edges = JSON.parse(record.edge_data.value || "[]");

          var container = this.$(".o_diagram_container")[0];
          var data = {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges),
          };

          var options = this._getNetworkOptions();
          this.network = new vis.Network(container, data, options);
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
        if (this.network) {
          var canvas = this.network.getCanvas();
          var dataURL = canvas.toDataURL();
          var link = document.createElement("a");
          link.download = "organization_diagram.png";
          link.href = dataURL;
          link.click();
        }
      },
    });

    /**
     * Customer Portal Diagram View
     */
    var CustomerPortalDiagramView = AbstractView.extend({
      display_name: _t("Portal Organization Diagram"),
      icon: "fa-sitemap",
      config: _.extend({}, AbstractView.prototype.config, {
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

export const CustomerPortalDiagram = {
  CustomerPortalDiagramView,
  CustomerPortalDiagramController,
  CustomerPortalDiagramRenderer,
};
