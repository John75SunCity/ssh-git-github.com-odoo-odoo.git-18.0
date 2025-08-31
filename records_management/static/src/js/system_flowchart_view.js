/**
 * Interactive System Flowchart View for Records Management
 *
 * This module provides a custom Odoo view type that displays an interactive
 * flowchart showing the complete Records Management System architecture,
 * including models, users, access rights, and relationships.
 *
 * Features:
 * - Interactive network diagram using vis.js
 * - Real-time search and filtering
 * - Color-coded access rights (green/red)
 * - Hierarchical layout with different node types
 * - Click interactions for detailed information
 * - Export capabilities
 *
 * @author Records Management System
 * @version 18.0.6.0.0
 */

odoo.define("records_management.system_flowchart_view", function (require) {
  "use strict";

  var AbstractView = require("web.AbstractView");
  var AbstractRenderer = require("web.AbstractRenderer");
  var AbstractController = require("web.AbstractController");
  var viewRegistry = require("web.view_registry");
  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var rpc = require("web.rpc");

  var _t = core._t;
  var QWeb = core.qweb;

  /**
   * System Flowchart Controller
   * Handles user interactions and data updates
   */
  var SystemFlowchartController = AbstractController.extend({
    events: {
      "click .o_search_button": "_onSearchClick",
      "keyup .o_search_input": "_onSearchKeyup",
      "change .o_search_type_select": "_onSearchTypeChange",
      "click .o_refresh_button": "_onRefreshClick",
      "click .o_export_button": "_onExportClick",
      "change .o_show_access_checkbox": "_onShowAccessChange",
    },

    /**
     * Initialize the controller
     */
    init: function (parent, model, renderer, params) {
      this._super.apply(this, arguments);
      this.searchQuery = "";
      this.searchType = "user";
      this.showAccessOnly = false;
    },

    /**
     * Handle search button click
     */
    _onSearchClick: function (event) {
      event.preventDefault();
      this._performSearch();
    },

    /**
     * Handle search input keyup
     */
    _onSearchKeyup: function (event) {
      if (event.which === 13) {
        // Enter key
        this._performSearch();
      }
    },

    /**
     * Handle search type change
     */
    _onSearchTypeChange: function (event) {
      this.searchType = $(event.target).val();
      this._performSearch();
    },

    /**
     * Handle refresh button click
     */
    _onRefreshClick: function (event) {
      event.preventDefault();
      this._refreshData();
    },

    /**
     * Handle export button click
     */
    _onExportClick: function (event) {
      event.preventDefault();
      this._exportDiagram();
    },

    /**
     * Handle show access only checkbox change
     */
    _onShowAccessChange: function (event) {
      this.showAccessOnly = $(event.target).is(":checked");
      this._performSearch();
    },

    /**
     * Perform search with current parameters
     */
    _performSearch: function () {
      this.searchQuery = this.$(".o_search_input").val() || "";

      var searchData = {
        search_query: this.searchQuery,
        search_type: this.searchType,
        show_access_only: this.showAccessOnly,
      };

      this.renderer.updateSearch(searchData);
    },

    /**
     * Refresh diagram data
     */
    _refreshData: function () {
      var self = this;
      this.renderer.showLoading();

      rpc
        .query({
          model: "system.diagram.data",
          method: "create",
          args: [{}],
        })
        .then(function (result) {
          self.renderer.refreshDiagram();
          self.renderer.hideLoading();
        });
    },

    /**
     * Export diagram data
     */
    _exportDiagram: function () {
      this.renderer.exportDiagram();
    },
  });

  /**
   * System Flowchart Renderer
   * Handles the visual representation of the diagram
   */
  var SystemFlowchartRenderer = AbstractRenderer.extend({
    template: "SystemFlowchartTemplate",

    /**
     * Initialize the renderer
     */
    init: function (parent, state, params) {
      this._super.apply(this, arguments);
      this.state = state;
      this.network = null;
      this.searchData = {};
    },

    /**
     * Start the renderer
     */
    start: function () {
      var self = this;
      return this._super().then(function () {
        self._initializeDiagram();
        self._setupEventListeners();
      });
    },

    /**
     * Initialize the vis.js network diagram
     */
    _initializeDiagram: function () {
      try {
        var container = this.$(".o_flowchart_container")[0];
        var data = this._prepareDiagramData();
        var options = this._getDiagramOptions();

        // Initialize vis.js network
        this.network = new vis.Network(container, data, options);

        // Setup network event listeners
        this._setupNetworkEvents();
      } catch (error) {
        console.error("Error initializing diagram:", error);
        this._showError(
          _t("Failed to initialize diagram. Please refresh the page.")
        );
      }
    },

    /**
     * Prepare diagram data from state
     */
    _prepareDiagramData: function () {
      var nodes = [];
      var edges = [];

      try {
        if (this.state.data && this.state.data.nodes_data) {
          nodes = JSON.parse(this.state.data.nodes_data.value || "[]");
        }
        if (this.state.data && this.state.data.edges_data) {
          edges = JSON.parse(this.state.data.edges_data.value || "[]");
        }
      } catch (error) {
        console.error("Error parsing diagram data:", error);
      }

      return {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
      };
    },

    /**
     * Get diagram configuration options
     */
    _getDiagramOptions: function () {
      var defaultOptions = {
          layout: {
              hierarchical: {
                  enabled: true,
                  direction: "UD",
                  sortMethod: "directed",
                  levelSeparation: 150,
                  nodeSpacing: 200,
              },
          },
          physics: {
              enabled: true,
              stabilization: { iterations: 100 },
              barnesHut: {
                  gravitationalConstant: -8000,
                  centralGravity: 0.3,
                  springLength: 95,
                  springConstant: 0.04,
                  damping: 0.09,
              },
          },
          interaction: {
              hover: true,
              multiselect: true,
              selectConnectedEdges: false,
              tooltipDelay: 300,
          },
          nodes: {
              font: {
                  size: 14,
                  color: "#000000",
                  face: "Arial",
              },
              borderWidth: 2,
              shadow: {
                  enabled: true,
                  color: "rgba(0,0,0,0.5)",
                  size: 5,
                  x: 2,
                  y: 2,
              },
              margin: 10,
          },
          edges: {
              arrows: {
                  to: {
                      enabled: true,
                      scaleFactor: 0.5,
                  },
              },
              font: { size: 12 },
              smooth: {
                  type: "dynamic",
                  roundness: 0.5,
              },
              width: 2,
          },
          groups: {
              system: {
                  color: { background: "#2E86AB", border: "#1B4B73" },
                  font: { color: "white", size: 16 },
              },
              interface: {
                  color: { background: "#A23B72", border: "#6B1E47" },
                  font: { color: "white" },
              },
              model: {
                  color: { background: "#4CAF50", border: "#2E7D32" },
                  shape: "box",
              },
              user: {
                  shape: "circle",
                  size: 30,
              },
              // Permission Level Groups
              admin_user: {
                  shape: "circle",
                  size: 35,
                  color: { background: "#D32F2F", border: "#B71C1C" },
                  font: { color: "white", size: 12 },
              },
              manager_user: {
                  shape: "circle",
                  size: 32,
                  color: { background: "#F57C00", border: "#E65100" },
                  font: { color: "white", size: 12 },
              },
              regular_user: {
                  shape: "circle",
                  size: 30,
                  color: { background: "#1976D2", border: "#0D47A1" },
                  font: { color: "white", size: 12 },
              },
              readonly_user: {
                  shape: "circle",
                  size: 28,
                  color: { background: "#757575", border: "#424242" },
                  font: { color: "white", size: 12 },
              },
              security_group: {
                  color: { background: "#8BC34A", border: "#4CAF50" },
                  shape: "ellipse",
              },
              company: {
                  color: { background: "#3F51B5", border: "#1A237E" },
                  shape: "box",
                  font: { color: "white" },
              },
              department: {
                  color: { background: "#673AB7", border: "#4527A0" },
                  shape: "ellipse",
                  font: { color: "white" },
              },
              // Cross-Department Sharing Groups
              sharing_request: {
                  color: { background: "#FF6F00", border: "#E65100" },
                  shape: "diamond",
                  font: { color: "white", size: 11 },
              },
              sharing_approved: {
                  color: { background: "#388E3C", border: "#1B5E20" },
                  shape: "diamond",
                  font: { color: "white", size: 11 },
              },
              sharing_pending: {
                  color: { background: "#FBC02D", border: "#F57F17" },
                  shape: "diamond",
                  font: { color: "white", size: 11 },
              },
              sharing_rejected: {
                  color: { background: "#D32F2F", border: "#B71C1C" },
                  shape: "diamond",
                  font: { color: "white", size: 11 },
              },
          },
      };

      try {
        if (this.state.data && this.state.data.diagram_config) {
          var customOptions = JSON.parse(
            this.state.data.diagram_config.value || "{}"
          );
          return _.extend(defaultOptions, customOptions);
        }
      } catch (error) {
        console.warn("Error parsing diagram config, using defaults:", error);
      }

      return defaultOptions;
    },

    /**
     * Setup network event listeners
     */
    _setupNetworkEvents: function () {
      var self = this;

      // Node click event
      this.network.on("click", function (params) {
        if (params.nodes.length > 0) {
          self._onNodeClick(params.nodes[0], params);
        }
      });

      // Node hover events
      this.network.on("hoverNode", function (params) {
        self._onNodeHover(params.node);
      });

      this.network.on("blurNode", function (params) {
        self._onNodeBlur(params.node);
      });

      // Stabilization events
      this.network.on("stabilizationProgress", function (params) {
        self._updateProgress(params.iterations, params.total);
      });

      this.network.on("stabilized", function () {
        self._hideProgress();
      });
    },

    /**
     * Handle node click
     */
    _onNodeClick: function (nodeId, params) {
      var node = this.network.body.data.nodes.get(nodeId);
      if (!node) return;

      this._showNodeDetails(node);
    },

    /**
     * Handle node hover
     */
    _onNodeHover: function (nodeId) {
      var node = this.network.body.data.nodes.get(nodeId);
      if (!node) return;

      // Show tooltip with additional information
      this._showTooltip(node);
    },

    /**
     * Handle node blur
     */
    _onNodeBlur: function (nodeId) {
      this._hideTooltip();
    },

    /**
     * Show node details in a dialog
     */
    _showNodeDetails: function (node) {
      var content = QWeb.render("NodeDetailsTemplate", { node: node });

      var dialog = new Dialog(this, {
        title: _t("Node Details: ") + node.label,
        size: "medium",
        $content: $(content),
        buttons: [
          {
            text: _t("Close"),
            close: true,
          },
        ],
      });

      dialog.open();
    },

    /**
     * Show tooltip
     */
    _showTooltip: function (node) {
      var tooltip = this.$(".o_tooltip");
      if (tooltip.length === 0) {
        tooltip = $('<div class="o_tooltip"></div>').appendTo(this.$el);
      }

      var content = this._getTooltipContent(node);
      tooltip.html(content).show();
    },

    /**
     * Hide tooltip
     */
    _hideTooltip: function () {
      this.$(".o_tooltip").hide();
    },

    /**
     * Get tooltip content for a node
     */
    _getTooltipContent: function (node) {
      var content = "<strong>" + node.label + "</strong><br>";

      if (node.group) {
        content += "Type: " + node.group + "<br>";
      }

      if (node.title) {
        content += node.title;
      }

      return content;
    },

    /**
     * Update search with new parameters
     */
    updateSearch: function (searchData) {
      this.searchData = searchData;
      this._filterDiagram();
    },

    /**
     * Filter diagram based on search parameters
     */
    _filterDiagram: function () {
      if (!this.network) return;

      try {
        var data = this._prepareDiagramData();
        var filteredData = this._applySearchFilter(data);

        this.network.setData(filteredData);
        this.network.fit();
      } catch (error) {
        console.error("Error filtering diagram:", error);
      }
    },

    /**
     * Apply search filter to data
     */
    _applySearchFilter: function (data) {
      if (!this.searchData.search_query) {
        return data;
      }

      var query = this.searchData.search_query.toLowerCase();
      var filteredNodes = [];
      var filteredEdges = [];

      // Filter nodes
      data.nodes.forEach(function (node) {
        var label = (node.label || "").toLowerCase();
        if (label.includes(query)) {
          filteredNodes.push(node);
        }
      });

      // Filter edges to only show connections between filtered nodes
      var nodeIds = filteredNodes.map(function (node) {
        return node.id;
      });
      data.edges.forEach(function (edge) {
        if (nodeIds.includes(edge.from) || nodeIds.includes(edge.to)) {
          filteredEdges.push(edge);
        }
      });

      return {
        nodes: new vis.DataSet(filteredNodes),
        edges: new vis.DataSet(filteredEdges),
      };
    },

    /**
     * Refresh diagram
     */
    refreshDiagram: function () {
      if (this.network) {
        this.network.destroy();
      }
      this._initializeDiagram();
    },

    /**
     * Export diagram
     */
    exportDiagram: function () {
      if (!this.network) return;

      var canvas = this.network.canvas;
      var dataURL = canvas.frame.canvas.toDataURL();

      // Create download link
      var link = document.createElement("a");
      link.download = "records_management_system_diagram.png";
      link.href = dataURL;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    /**
     * Show loading indicator
     */
    showLoading: function () {
      this.$(".o_loading").show();
    },

    /**
     * Hide loading indicator
     */
    hideLoading: function () {
      this.$(".o_loading").hide();
    },

    /**
     * Update progress indicator
     */
    _updateProgress: function (current, total) {
      var progress = Math.round((current / total) * 100);
      this.$(".o_progress_bar").css("width", progress + "%");
      this.$(".o_progress_text").text(progress + "%");
    },

    /**
     * Hide progress indicator
     */
    _hideProgress: function () {
      this.$(".o_progress").hide();
    },

    /**
     * Show error message
     */
    _showError: function (message) {
      this.$(".o_flowchart_container").html(
        '<div class="alert alert-danger">' + message + "</div>"
      );
    },

    /**
     * Setup additional event listeners
     */
    _setupEventListeners: function () {
      var self = this;

      // Window resize
      $(window).on("resize.flowchart", function () {
        if (self.network) {
          self.network.redraw();
          self.network.fit();
        }
      });
    },

    /**
     * Destroy the renderer
     */
    destroy: function () {
      $(window).off("resize.flowchart");
      if (this.network) {
        this.network.destroy();
      }
      this._super();
    },
  });

  /**
   * System Flowchart View
   * Main view component that orchestrates controller and renderer
   */
  var SystemFlowchartView = AbstractView.extend({
    display_name: _t("System Flowchart"),
    icon: "fa-sitemap",
    config: _.extend({}, AbstractView.prototype.config, {
      Controller: SystemFlowchartController,
      Renderer: SystemFlowchartRenderer,
    }),
    viewType: "system_flowchart",
    groupable: false,
    searchable: true,

    /**
     * Initialize the view
     */
    init: function (viewInfo, params) {
      this._super.apply(this, arguments);
    },
  });

  // Register the view
  viewRegistry.add("system_flowchart", SystemFlowchartView);

  return {
    SystemFlowchartView: SystemFlowchartView,
    SystemFlowchartController: SystemFlowchartController,
    SystemFlowchartRenderer: SystemFlowchartRenderer,
  };
});
