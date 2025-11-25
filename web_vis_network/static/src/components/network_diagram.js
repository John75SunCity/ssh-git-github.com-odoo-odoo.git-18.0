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
        this.visLoaded = false;

        onMounted(async () => {
            await this.ensureVisLoaded();
            this.initNetwork();
        });

        onWillUnmount(() => {
            if (this.network) {
                this.network.destroy();
            }
        });
    }

    /**
     * Ensure vis.js library is loaded
     * Loads from CDN if local files not available
     */
    async ensureVisLoaded() {
        if (typeof vis !== 'undefined') {
            this.visLoaded = true;
            return;
        }

        console.log('vis.js not found locally, loading from CDN...');

        // Load CSS
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = 'https://cdn.jsdelivr.net/npm/vis-network@9.1.9/dist/dist/vis-network.min.css';
        document.head.appendChild(cssLink);

        // Load JavaScript
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js';
            script.onload = () => {
                console.log('vis.js loaded successfully from CDN');
                this.visLoaded = true;
                resolve();
            };
            script.onerror = () => {
                console.error('Failed to load vis.js from CDN');
                reject(new Error('Failed to load vis.js'));
            };
            document.head.appendChild(script);
        });
    }

    initNetwork() {
        if (typeof vis === 'undefined') {
            console.error('vis.js library not loaded! Unable to render network diagram.');
            const container = this.containerRef.el;
            container.innerHTML = '<div style="padding: 20px; text-align: center; color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">' +
                '<h4>⚠️ vis.js Library Not Available</h4>' +
                '<p>The vis.js library could not be loaded. Please check your internet connection or contact your administrator.</p>' +
                '<p>See web_vis_network module README.md for installation instructions.</p>' +
                '</div>';
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
