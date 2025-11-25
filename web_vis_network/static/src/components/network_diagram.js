/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * NetworkDiagram Component
 *
 * Owl component for rendering vis.js network diagrams.
 * This is a reusable component that can be used across multiple modules.
 *
 * Usage:
 * ------
 * import { NetworkDiagram } from "@web_vis_network/components/network_diagram";
 *
 * In your template:
 * <NetworkDiagram nodes="state.nodes" edges="state.edges" options="state.options"/>
 *
 * Props:
 * ------
 * - nodes: Array of node objects (required)
 * - edges: Array of edge objects (required)
 * - options: vis.js options object (optional)
 * - height: Container height in pixels (default: 600)
 */
export class NetworkDiagram extends Component {
    static template = "web_vis_network.NetworkDiagram";

    static props = {
        nodes: { type: Array, optional: false },
        edges: { type: Array, optional: false },
        options: { type: Object, optional: true },
        height: { type: Number, optional: true },
        onNodeClick: { type: Function, optional: true },
        onEdgeClick: { type: Function, optional: true },
    };

    static defaultProps = {
        height: 600,
        options: {},
    };

    setup() {
        this.containerRef = useRef("network-container");
        this.network = null;

        onMounted(() => {
            this.initNetwork();
        });

        onWillUnmount(() => {
            if (this.network) {
                this.network.destroy();
            }
        });
    }

    initNetwork() {
        if (typeof vis === 'undefined') {
            console.error('vis.js library not loaded! Make sure web_vis_network module is installed.');
            return;
        }

        const container = this.containerRef.el;
        const nodes = new vis.DataSet(this.props.nodes);
        const edges = new vis.DataSet(this.props.edges);

        const data = { nodes, edges };
        const options = this.getDefaultOptions();

        // Merge custom options with defaults
        const finalOptions = Object.assign({}, options, this.props.options);

        // Create network
        this.network = new vis.Network(container, data, finalOptions);

        // Attach event handlers if provided
        if (this.props.onNodeClick) {
            this.network.on('click', (params) => {
                if (params.nodes.length > 0) {
                    this.props.onNodeClick(params.nodes[0], params);
                }
            });
        }

        if (this.props.onEdgeClick) {
            this.network.on('click', (params) => {
                if (params.edges.length > 0) {
                    this.props.onEdgeClick(params.edges[0], params);
                }
            });
        }
    }

    getDefaultOptions() {
        return {
            nodes: {
                shape: 'box',
                font: {
                    size: 14,
                    face: 'arial'
                },
                borderWidth: 2,
                shadow: true
            },
            edges: {
                arrows: {
                    to: { enabled: true, scaleFactor: 0.5 }
                },
                smooth: {
                    type: 'cubicBezier',
                    forceDirection: 'horizontal'
                },
                font: {
                    size: 12,
                    align: 'middle'
                }
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 200,
                    springConstant: 0.04,
                    damping: 0.09
                }
            },
            interaction: {
                hover: true,
                navigationButtons: true,
                keyboard: true,
                tooltipDelay: 200
            }
        };
    }

    /**
     * Update the network data
     * Call this method when nodes or edges change
     */
    updateData(nodes, edges) {
        if (this.network) {
            this.network.setData({
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            });
        }
    }

    /**
     * Fit the network to the viewport
     */
    fit() {
        if (this.network) {
            this.network.fit();
        }
    }

    /**
     * Stabilize the network physics
     */
    stabilize() {
        if (this.network) {
            this.network.stabilize();
        }
    }
}

// Register the component
registry.category("vis_components").add("network_diagram", NetworkDiagram);
