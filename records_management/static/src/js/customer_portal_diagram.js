/**
 * Customer Portal Interactive Organization Diagram
 *
 * This JavaScript module handles the interactive organization diagram
 * for customer portal users. It provides a simplified, customer-facing
 * interface compared to the admin system flowchart.
 *
 * Key Features:
 * - Interactive organizational chart visualization
 * - Direct messaging capabilities between users
 * - Real-time search and filtering
 * - Mobile-responsive design
 * - Portal-specific security and permissions
 *
 * @author Records Management System
 * @version 18.0.0.1
 */

odoo.define(
  "records_management.portal_organization_diagram",
  function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    var core = require("web.core");
    var ajax = require("web.ajax");
    var Dialog = require("web.Dialog");

    var _t = core._t;
    var qweb = core.qweb;

    /**
     * Portal Organization Diagram Widget
     */
    var PortalOrganizationDiagram = publicWidget.Widget.extend({
      selector: ".o_portal_organization_diagram",
      events: {
        "click #search-button": "_onSearchClick",
        "keyup #search-query": "_onSearchKeyup",
        "change #layout-select": "_onLayoutChange",
        "click #refresh-diagram": "_onRefreshClick",
        "click #export-diagram": "_onExportClick",
        "change #enable-messaging": "_onMessagingToggle",
        "click #message-user-btn": "_onMessageUserClick",
      },

      /**
       * Widget initialization
       */
      init: function (parent, options) {
        this._super.apply(this, arguments);
        this.network = null;
        this.nodes = null;
        this.edges = null;
        this.selectedNode = null;
        this.diagramData = null;
        this.config = null;
      },

      /**
       * Widget startup - called when DOM is ready
       */
      start: function () {
        var self = this;
        this._super.apply(this, arguments).then(function () {
          self._loadInitialData();
          self._initializeDiagram();
        });
      },

      /**
       * Load initial diagram data from the page
       */
      _loadInitialData: function () {
        try {
          var dataScript = this.$("#diagram-data");
          if (dataScript.length) {
            this.diagramData = JSON.parse(dataScript.text());
            this.config = this.diagramData.config || {};
            console.log(
              "Portal Organization Diagram loaded:",
              this.diagramData
            );
          } else {
            console.error("No diagram data found");
            this._showError("Failed to load diagram data");
          }
        } catch (error) {
          console.error("Error parsing diagram data:", error);
          this._showError("Failed to parse diagram data");
        }
      },

      /**
       * Initialize the vis.js network diagram
       */
      _initializeDiagram: function () {
        var self = this;

        // Check if vis.js is available
        if (typeof vis === "undefined") {
          console.error("vis.js library not found");
          this._showError(
            "Visualization library not loaded. Please contact support."
          );
          return;
        }

        try {
          // Prepare data
          this.nodes = new vis.DataSet(this.diagramData.nodes || []);
          this.edges = new vis.DataSet(this.diagramData.edges || []);

          var container = this.$("#organization-diagram-container")[0];
          var data = {
            nodes: this.nodes,
            edges: this.edges,
          };

          var options = this._getNetworkOptions();

          // Create network
          this.network = new vis.Network(container, data, options);
          this._setupNetworkEvents();
          this._updateStatistics();
          this._hideLoading();

          console.log("Organization diagram initialized successfully");
        } catch (error) {
          console.error("Error initializing diagram:", error);
          this._showError("Failed to initialize diagram");
        }
      },

      /**
       * Get network visualization options
       */
      _getNetworkOptions: function () {
        var layoutType = this.config.layout_type || "hierarchical";

        var options = {
          layout: {
            hierarchical:
              layoutType === "hierarchical"
                ? {
                    direction: "UD",
                    sortMethod: "directed",
                    nodeSpacing: 100,
                    levelSeparation: 150,
                    treeSpacing: 200,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true,
                  }
                : false,
          },
          physics: {
            enabled: layoutType !== "hierarchical",
            stabilization: {
              enabled: true,
              iterations: 100,
              updateInterval: 25,
            },
          },
          interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            selectConnectedEdges: true,
            hover: true,
            tooltipDelay: 200,
            hideEdgesOnDrag: false,
            hideNodesOnDrag: false,
          },
          nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
            shadow: {
              enabled: true,
              color: "rgba(0,0,0,0.2)",
              size: 10,
              x: 3,
              y: 3,
            },
            font: {
              size: 14,
              strokeWidth: 2,
              strokeColor: "#ffffff",
            },
            chosen: {
              node: function (values, id, selected, hovering) {
                values.shadow = true;
                values.shadowColor = "rgba(0,0,0,0.3)";
                values.shadowSize = 15;
              },
            },
          },
          edges: {
            width: 2,
            shadow: {
              enabled: true,
              color: "rgba(0,0,0,0.1)",
              size: 5,
              x: 2,
              y: 2,
            },
            smooth: {
              enabled: true,
              type: "dynamic",
              roundness: 0.5,
            },
            arrows: {
              to: {
                enabled: true,
                scaleFactor: 1.2,
              },
            },
            font: {
              size: 10,
              strokeWidth: 2,
              strokeColor: "#ffffff",
            },
          },
        };

        return options;
      },

      /**
       * Setup network event listeners
       */
      _setupNetworkEvents: function () {
        var self = this;

        // Node selection event
        this.network.on("click", function (params) {
          if (params.nodes.length > 0) {
            self._onNodeClick(params.nodes[0], params);
          }
        });

        // Node double-click for messaging
        this.network.on("doubleClick", function (params) {
          if (params.nodes.length > 0) {
            var nodeId = params.nodes[0];
            if (nodeId.startsWith("user_") && self.config.show_messaging) {
              self._openMessageDialog(nodeId);
            }
          }
        });

        // Hover events for tooltips
        this.network.on("hoverNode", function (params) {
          self._showNodeTooltip(params.node, params);
        });

        this.network.on("blurNode", function (params) {
          self._hideNodeTooltip();
        });

        // Stabilization events
        this.network.on("stabilizationProgress", function (params) {
          var progress = Math.round((params.iterations / params.total) * 100);
          self._updateLoadingProgress(progress);
        });

        this.network.on("stabilizationIterationsDone", function () {
          self._hideLoading();
        });
      },

      /**
       * Handle node click events
       */
      _onNodeClick: function (nodeId, params) {
        console.log("Node clicked:", nodeId);

        var nodeData = this.nodes.get(nodeId);
        if (!nodeData) return;

        this.selectedNode = nodeData;
        this._showNodeDetails(nodeData);
      },

      /**
       * Show node details in modal
       */
      _showNodeDetails: function (nodeData) {
        var $modal = this.$("#node-details-modal");
        var $title = this.$("#node-modal-title");
        var $body = this.$("#node-modal-body");
        var $messageBtn = this.$("#message-user-btn");

        // Set modal title
        $title.text(nodeData.label || "Node Details");

        // Build modal content based on node type
        var content = "";
        if (nodeData.group === "user") {
          content = this._buildUserNodeContent(nodeData);
          if (
            this.config.show_messaging &&
            nodeData.id !== "user_" + this.config.user_id
          ) {
            $messageBtn.removeClass("d-none");
          } else {
            $messageBtn.addClass("d-none");
          }
        } else if (nodeData.group === "company") {
          content = this._buildCompanyNodeContent(nodeData);
          $messageBtn.addClass("d-none");
        } else if (nodeData.group === "department") {
          content = this._buildDepartmentNodeContent(nodeData);
          $messageBtn.addClass("d-none");
        } else {
          content = this._buildGenericNodeContent(nodeData);
          $messageBtn.addClass("d-none");
        }

        $body.html(content);
        $modal.modal("show");
      },

      /**
       * Build user node content for modal
       */
      _buildUserNodeContent: function (nodeData) {
        return `
                <div class="row">
                    <div class="col-md-12">
                        <h6><i class="fa fa-user"></i> User Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Name:</strong></td>
                                <td>${nodeData.label}</td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>${nodeData.title || "User"}</td>
                            </tr>
                            <tr>
                                <td><strong>Status:</strong></td>
                                <td>
                                    <span class="badge badge-success">Online</span>
                                </td>
                            </tr>
                        </table>
                        
                        ${
                          this.config.show_messaging
                            ? `
                        <div class="alert alert-info">
                            <i class="fa fa-info-circle"></i> 
                            <strong>Tip:</strong> Double-click on user nodes or use the message button to send direct messages.
                        </div>`
                            : ""
                        }
                    </div>
                </div>
            `;
      },

      /**
       * Build company node content for modal
       */
      _buildCompanyNodeContent: function (nodeData) {
        return `
                <div class="row">
                    <div class="col-md-12">
                        <h6><i class="fa fa-building"></i> Company Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Name:</strong></td>
                                <td>${nodeData.label}</td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>Company</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
      },

      /**
       * Build department node content for modal
       */
      _buildDepartmentNodeContent: function (nodeData) {
        return `
                <div class="row">
                    <div class="col-md-12">
                        <h6><i class="fa fa-sitemap"></i> Department Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Name:</strong></td>
                                <td>${nodeData.label}</td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>Department</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
      },

      /**
       * Build generic node content for modal
       */
      _buildGenericNodeContent: function (nodeData) {
        return `
                <div class="row">
                    <div class="col-md-12">
                        <h6><i class="fa fa-info-circle"></i> Node Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <td><strong>Label:</strong></td>
                                <td>${nodeData.label}</td>
                            </tr>
                            <tr>
                                <td><strong>Type:</strong></td>
                                <td>${nodeData.group || "Unknown"}</td>
                            </tr>
                            <tr>
                                <td><strong>Title:</strong></td>
                                <td>${
                                  nodeData.title || "No description available"
                                }</td>
                            </tr>
                        </table>
                    </div>
                </div>
            `;
      },

      /**
       * Update diagram statistics display
       */
      _updateStatistics: function () {
        if (!this.diagramData.stats) return;

        var stats = this.diagramData.stats;
        this.$("#companies-count").text(stats.companies || 0);
        this.$("#departments-count").text(stats.departments || 0);
        this.$("#users-count").text(stats.users || 0);
        this.$("#connections-count").text(stats.total_edges || 0);
      },

      /**
       * Search functionality
       */
      _onSearchClick: function (event) {
        event.preventDefault();
        this._performSearch();
      },

      _onSearchKeyup: function (event) {
        if (event.keyCode === 13) {
          // Enter key
          this._performSearch();
        }
      },

      _performSearch: function () {
        var searchQuery = this.$("#search-query").val().trim();
        console.log("Performing search:", searchQuery);

        this._showLoading();
        this._updateDiagramData({
          search_query: searchQuery,
        });
      },

      /**
       * Layout change functionality
       */
      _onLayoutChange: function (event) {
        var layoutType = $(event.target).val();
        console.log("Layout changed to:", layoutType);

        this._showLoading();
        this._updateDiagramData({
          layout_type: layoutType,
        });
      },

      /**
       * Refresh diagram
       */
      _onRefreshClick: function (event) {
        event.preventDefault();
        console.log("Refreshing diagram");

        this._showLoading();
        this._updateDiagramData({});
      },

      /**
       * Export diagram
       */
      _onExportClick: function (event) {
        event.preventDefault();
        window.location.href = "/my/organization/export";
      },

      /**
       * Toggle messaging functionality
       */
      _onMessagingToggle: function (event) {
        this.config.show_messaging = $(event.target).is(":checked");
        console.log("Messaging toggled:", this.config.show_messaging);
      },

      /**
       * Handle message user button click
       */
      _onMessageUserClick: function (event) {
        event.preventDefault();
        if (this.selectedNode && this.selectedNode.id.startsWith("user_")) {
          this._openMessageDialog(this.selectedNode.id);
        }
      },

      /**
       * Open messaging dialog for a user
       */
      _openMessageDialog: function (nodeId) {
        var userId = nodeId.replace("user_", "");
        console.log("Opening message dialog for user:", userId);

        var self = this;
        ajax
          .jsonRpc("/my/organization/message", "call", {
            target_user_id: parseInt(userId),
          })
          .then(function (result) {
            if (result.error) {
              self._showError(result.error);
            } else {
              // Close details modal if open
              self.$("#node-details-modal").modal("hide");

              // Show success message
              self._showSuccess("Opening message composer...");

              // The backend will handle opening the message composer
              // In a real implementation, you might want to open a custom modal here
            }
          })
          .catch(function (error) {
            console.error("Error opening message dialog:", error);
            self._showError("Failed to open message composer");
          });
      },

      /**
       * Update diagram data via AJAX
       */
      _updateDiagramData: function (params) {
        var self = this;

        ajax
          .jsonRpc("/my/organization/data", "call", {
            diagram_id: this.config.diagram_id,
            ...params,
          })
          .then(function (result) {
            if (result.error) {
              self._showError(result.error);
              self._hideLoading();
            } else {
              // Update local data
              self.diagramData.nodes = result.nodes;
              self.diagramData.edges = result.edges;
              self.diagramData.stats = result.stats;
              self.config = { ...self.config, ...result.config };

              // Update diagram
              self._updateDiagram();
            }
          })
          .catch(function (error) {
            console.error("Error updating diagram data:", error);
            self._showError("Failed to update diagram");
            self._hideLoading();
          });
      },

      /**
       * Update the diagram with new data
       */
      _updateDiagram: function () {
        if (!this.network) return;

        try {
          // Update nodes and edges
          this.nodes.update(this.diagramData.nodes);
          this.edges.update(this.diagramData.edges);

          // Update network options if layout changed
          var options = this._getNetworkOptions();
          this.network.setOptions(options);

          // Update statistics
          this._updateStatistics();

          // Hide loading
          this._hideLoading();

          console.log("Diagram updated successfully");
        } catch (error) {
          console.error("Error updating diagram:", error);
          this._showError("Failed to update diagram visualization");
          this._hideLoading();
        }
      },

      /**
       * Utility methods
       */
      _showLoading: function () {
        this.$(".loading-overlay").show();
      },

      _hideLoading: function () {
        this.$(".loading-overlay").hide();
      },

      _updateLoadingProgress: function (progress) {
        this.$(".loading-overlay p").text(
          `Loading organization diagram... ${progress}%`
        );
      },

      _showError: function (message) {
        this.displayNotification({
          message: message,
          type: "danger",
          sticky: true,
        });
      },

      _showSuccess: function (message) {
        this.displayNotification({
          message: message,
          type: "success",
          sticky: false,
        });
      },

      _showNodeTooltip: function (nodeId, params) {
        // Could implement custom tooltip here
      },

      _hideNodeTooltip: function () {
        // Could implement custom tooltip hiding here
      },
    });

    // Register the widget
    publicWidget.registry.PortalOrganizationDiagram = PortalOrganizationDiagram;

    return PortalOrganizationDiagram;
  }
);

/**
 * Initialize the widget when the page loads
 */
$(document).ready(function () {
  if ($(".o_portal_organization_diagram").length) {
    console.log("Initializing Portal Organization Diagram");

    // Check if vis.js is loaded
    if (typeof vis === "undefined") {
      console.warn("vis.js not found, attempting to load...");
      // Could add dynamic loading here if needed
    }
  }
});
