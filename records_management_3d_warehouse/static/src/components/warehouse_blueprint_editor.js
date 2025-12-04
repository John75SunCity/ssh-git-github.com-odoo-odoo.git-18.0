/** @odoo-module **/
/**
 * 2D Warehouse Blueprint Editor with Indoor Navigation
 *
 * Features:
 * - Canvas-based blueprint drawing from measurements
 * - Drag & drop walls, doors, aisles, shelving units
 * - Coordinate extraction for 3D integration
 * - Indoor navigation / pathfinding (A* algorithm)
 * - Turn-by-turn directions like Google Maps
 * - Overlay 2D on 3D view mode
 *
 * Based on Grok recommendations: Floorspace.js patterns + Three.js integration
 */

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ============================================================================
// PATHFINDING - A* Algorithm for Indoor Navigation
// ============================================================================

class PathfindingGrid {
    constructor(width, height, cellSize) {
        this.width = Math.ceil(width / cellSize);
        this.height = Math.ceil(height / cellSize);
        this.cellSize = cellSize;
        this.grid = this.createGrid();
        this.obstacles = new Set();
    }

    createGrid() {
        const grid = [];
        for (let y = 0; y < this.height; y++) {
            grid[y] = [];
            for (let x = 0; x < this.width; x++) {
                grid[y][x] = { x, y, walkable: true, g: 0, h: 0, f: 0, parent: null };
            }
        }
        return grid;
    }

    addObstacle(x1, y1, x2, y2) {
        // Mark cells as non-walkable (for walls, shelves, etc.)
        const startX = Math.floor(Math.min(x1, x2) / this.cellSize);
        const endX = Math.ceil(Math.max(x1, x2) / this.cellSize);
        const startY = Math.floor(Math.min(y1, y2) / this.cellSize);
        const endY = Math.ceil(Math.max(y1, y2) / this.cellSize);

        for (let y = startY; y < endY && y < this.height; y++) {
            for (let x = startX; x < endX && x < this.width; x++) {
                if (this.grid[y] && this.grid[y][x]) {
                    this.grid[y][x].walkable = false;
                    this.obstacles.add(`${x},${y}`);
                }
            }
        }
    }

    clearObstacles() {
        this.obstacles.clear();
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                this.grid[y][x].walkable = true;
            }
        }
    }

    getNeighbors(node) {
        const neighbors = [];
        const { x, y } = node;
        const directions = [
            { dx: 0, dy: -1 }, { dx: 0, dy: 1 },  // Up, Down
            { dx: -1, dy: 0 }, { dx: 1, dy: 0 },  // Left, Right
            { dx: -1, dy: -1 }, { dx: 1, dy: -1 }, // Diagonals
            { dx: -1, dy: 1 }, { dx: 1, dy: 1 }
        ];

        for (const { dx, dy } of directions) {
            const nx = x + dx;
            const ny = y + dy;
            if (nx >= 0 && nx < this.width && ny >= 0 && ny < this.height) {
                if (this.grid[ny][nx].walkable) {
                    // For diagonals, check if both adjacent cells are walkable
                    if (dx !== 0 && dy !== 0) {
                        if (this.grid[y][nx].walkable && this.grid[ny][x].walkable) {
                            neighbors.push(this.grid[ny][nx]);
                        }
                    } else {
                        neighbors.push(this.grid[ny][nx]);
                    }
                }
            }
        }
        return neighbors;
    }

    heuristic(a, b) {
        // Octile distance (better for 8-directional movement)
        const dx = Math.abs(a.x - b.x);
        const dy = Math.abs(a.y - b.y);
        return Math.max(dx, dy) + (Math.sqrt(2) - 1) * Math.min(dx, dy);
    }

    findPath(startX, startY, endX, endY) {
        // Convert world coordinates to grid coordinates
        const startGridX = Math.floor(startX / this.cellSize);
        const startGridY = Math.floor(startY / this.cellSize);
        const endGridX = Math.floor(endX / this.cellSize);
        const endGridY = Math.floor(endY / this.cellSize);

        // Validate bounds
        if (startGridX < 0 || startGridX >= this.width || startGridY < 0 || startGridY >= this.height ||
            endGridX < 0 || endGridX >= this.width || endGridY < 0 || endGridY >= this.height) {
            return null;
        }

        // Reset grid
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const node = this.grid[y][x];
                node.g = 0;
                node.h = 0;
                node.f = 0;
                node.parent = null;
            }
        }

        const startNode = this.grid[startGridY][startGridX];
        const endNode = this.grid[endGridY][endGridX];

        if (!startNode.walkable || !endNode.walkable) {
            return null;
        }

        const openSet = [startNode];
        const closedSet = new Set();

        while (openSet.length > 0) {
            // Get node with lowest f score
            openSet.sort((a, b) => a.f - b.f);
            const current = openSet.shift();

            if (current === endNode) {
                // Reconstruct path
                const path = [];
                let node = current;
                while (node) {
                    path.unshift({
                        x: node.x * this.cellSize + this.cellSize / 2,
                        y: node.y * this.cellSize + this.cellSize / 2,
                        gridX: node.x,
                        gridY: node.y
                    });
                    node = node.parent;
                }
                return this.simplifyPath(path);
            }

            closedSet.add(`${current.x},${current.y}`);

            for (const neighbor of this.getNeighbors(current)) {
                if (closedSet.has(`${neighbor.x},${neighbor.y}`)) continue;

                const isDiagonal = neighbor.x !== current.x && neighbor.y !== current.y;
                const moveCost = isDiagonal ? 1.414 : 1;
                const tentativeG = current.g + moveCost;

                const inOpenSet = openSet.includes(neighbor);

                if (!inOpenSet || tentativeG < neighbor.g) {
                    neighbor.parent = current;
                    neighbor.g = tentativeG;
                    neighbor.h = this.heuristic(neighbor, endNode);
                    neighbor.f = neighbor.g + neighbor.h;

                    if (!inOpenSet) {
                        openSet.push(neighbor);
                    }
                }
            }
        }

        return null; // No path found
    }

    simplifyPath(path) {
        if (path.length < 3) return path;

        const simplified = [path[0]];
        let lastDirection = null;

        for (let i = 1; i < path.length; i++) {
            const prev = path[i - 1];
            const curr = path[i];
            const dx = Math.sign(curr.x - prev.x);
            const dy = Math.sign(curr.y - prev.y);
            const direction = `${dx},${dy}`;

            if (direction !== lastDirection) {
                simplified.push(curr);
                lastDirection = direction;
            }
        }

        // Always include the last point
        if (simplified[simplified.length - 1] !== path[path.length - 1]) {
            simplified.push(path[path.length - 1]);
        }

        return simplified;
    }

    generateDirections(path, locationMap) {
        if (!path || path.length < 2) return [];

        const directions = [];
        let totalDistance = 0;

        for (let i = 1; i < path.length; i++) {
            const prev = path[i - 1];
            const curr = path[i];

            const dx = curr.x - prev.x;
            const dy = curr.y - prev.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            totalDistance += distance;

            let direction = '';
            let icon = '';

            // Determine cardinal direction
            if (Math.abs(dx) > Math.abs(dy)) {
                direction = dx > 0 ? 'right' : 'left';
                icon = dx > 0 ? '→' : '←';
            } else {
                direction = dy > 0 ? 'down' : 'up';
                icon = dy > 0 ? '↓' : '↑';
            }

            // Check for nearby landmarks
            let landmark = '';
            for (const [id, loc] of Object.entries(locationMap)) {
                const ldx = Math.abs(curr.x - loc.x);
                const ldy = Math.abs(curr.y - loc.y);
                if (ldx < this.cellSize * 2 && ldy < this.cellSize * 2) {
                    landmark = loc.name;
                    break;
                }
            }

            directions.push({
                step: i,
                instruction: `Turn ${direction}`,
                icon: icon,
                distance: Math.round(distance / 12), // Convert to feet
                landmark: landmark,
                position: { x: curr.x, y: curr.y }
            });
        }

        return {
            directions: directions,
            totalDistance: Math.round(totalDistance / 12), // feet
            estimatedTime: Math.round(totalDistance / 12 / 4) // minutes at 4 ft/sec walking speed
        };
    }
}

// ============================================================================
// 2D BLUEPRINT EDITOR COMPONENT
// ============================================================================

export class WarehouseBlueprintEditor extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.canvasRef = useRef("blueprint-canvas");
        this.overlayCanvasRef = useRef("overlay-canvas");

        this.state = useState({
            blueprintId: this.props.action?.params?.blueprint_id || null,
            blueprint: null,
            loading: true,
            error: null,

            // Editor state
            mode: 'select', // select, wall, door, aisle, shelf, zone, navigate
            selectedElement: null,
            isDragging: false,
            dragStart: null,

            // View state
            zoom: 1,
            panX: 0,
            panY: 0,
            showGrid: true,
            gridSize: 12, // 1 foot = 12 inches
            showLabels: true,
            showDimensions: true,

            // Elements
            walls: [],
            doors: [],
            aisles: [],
            shelves: [],
            zones: [],
            locations: [],

            // Navigation
            navigationMode: false,
            navigationStart: null,
            navigationEnd: null,
            currentPath: null,
            currentDirections: null,

            // Coordinate export
            coordinateFormat: 'json', // json, csv, geojson

            // Cursor tracking and coordinate picking
            cursorPosition: { x: 0, y: 0 },
            showCursor: true,
            pickCoordinatesMode: false,
            pickedPoints: [], // Array of {x, y, label} for marked points
            pickingStep: 'start', // 'start' or 'end'
        });

        // Canvas context
        this.ctx = null;
        this.overlayCtx = null;

        // Pathfinding grid
        this.pathfinder = null;

        // Location map for navigation labels
        this.locationMap = {};

        onMounted(async () => {
            await this.loadBlueprint();
            this.initCanvas();
        });

        onWillUnmount(() => {
            this.cleanup();
        });
    }

    // ============================================================================
    // DATA LOADING
    // ============================================================================

    async loadBlueprint() {
        try {
            this.state.loading = true;

            if (!this.state.blueprintId) {
                // Get first available blueprint
                const blueprints = await this.orm.searchRead(
                    'warehouse.blueprint',
                    [['active', '=', true]],
                    ['id', 'name', 'length', 'width', 'height', 'warehouse_id', 'blueprint_data'],
                    { limit: 1 }
                );

                if (blueprints.length > 0) {
                    this.state.blueprintId = blueprints[0].id;
                    this.state.blueprint = blueprints[0];
                }
            } else {
                const blueprints = await this.orm.searchRead(
                    'warehouse.blueprint',
                    [['id', '=', this.state.blueprintId]],
                    ['id', 'name', 'length', 'width', 'height', 'warehouse_id', 'blueprint_data']
                );

                if (blueprints.length > 0) {
                    this.state.blueprint = blueprints[0];
                }
            }

            if (this.state.blueprint) {
                // Load blueprint elements
                await this.loadBlueprintElements();

                // Initialize pathfinder
                this.initPathfinder();
            }

            this.state.loading = false;

        } catch (error) {
            console.error("Error loading blueprint:", error);
            this.state.error = error.message;
            this.state.loading = false;
        }
    }

    async loadBlueprintElements() {
        if (!this.state.blueprintId) return;

        // Load walls
        this.state.walls = await this.orm.searchRead(
            'warehouse.wall',
            [['blueprint_id', '=', this.state.blueprintId]],
            ['id', 'name', 'start_x', 'start_y', 'end_x', 'end_y', 'thickness', 'wall_type']
        );

        // Load doors
        this.state.doors = await this.orm.searchRead(
            'warehouse.door',
            [['blueprint_id', '=', this.state.blueprintId]],
            ['id', 'name', 'pos_x', 'pos_y', 'width', 'door_type', 'rotation']
        );

        // Load zones/offices
        this.state.zones = await this.orm.searchRead(
            'warehouse.office',
            [['blueprint_id', '=', this.state.blueprintId]],
            ['id', 'name', 'pos_x', 'pos_y', 'width', 'length', 'zone_type', 'color']
        );

        // Load stock locations with coordinates
        const blueprint = this.state.blueprint;
        if (blueprint.warehouse_id) {
            this.state.locations = await this.orm.searchRead(
                'stock.location',
                [
                    ['warehouse_id', '=', blueprint.warehouse_id[0]],
                    ['is_records_location', '=', true]
                ],
                ['id', 'name', 'complete_name', 'posx', 'posy', 'posz', 'barcode', 'max_capacity', 'current_usage']
            );

            // Build location map for navigation
            this.locationMap = {};
            for (const loc of this.state.locations) {
                this.locationMap[loc.id] = {
                    x: loc.posx || 0,
                    y: loc.posy || 0,
                    z: loc.posz || 0,
                    name: loc.name,
                    barcode: loc.barcode
                };
            }
        }

        // Parse stored blueprint data if exists
        if (blueprint.blueprint_data) {
            try {
                const data = JSON.parse(blueprint.blueprint_data);
                if (data.shelves) this.state.shelves = data.shelves;
                if (data.aisles) this.state.aisles = data.aisles;
            } catch (e) {
                console.warn("Could not parse blueprint data:", e);
            }
        }
    }

    initPathfinder() {
        if (!this.state.blueprint) return;

        const { length, width } = this.state.blueprint;
        const cellSize = 24; // 2 feet per cell for pathfinding

        this.pathfinder = new PathfindingGrid(length, width, cellSize);

        // Add walls as obstacles
        for (const wall of this.state.walls) {
            this.pathfinder.addObstacle(
                wall.start_x, wall.start_y,
                wall.end_x, wall.end_y
            );
        }

        // Add shelves as obstacles
        for (const shelf of this.state.shelves) {
            this.pathfinder.addObstacle(
                shelf.x, shelf.y,
                shelf.x + shelf.width, shelf.y + shelf.depth
            );
        }

        // Add zones as obstacles (depending on type)
        for (const zone of this.state.zones) {
            if (zone.zone_type === 'office' || zone.zone_type === 'restricted') {
                this.pathfinder.addObstacle(
                    zone.pos_x, zone.pos_y,
                    zone.pos_x + zone.width, zone.pos_y + zone.length
                );
            }
        }
    }

    // ============================================================================
    // CANVAS INITIALIZATION
    // ============================================================================

    initCanvas() {
        const canvas = this.canvasRef.el;
        const overlayCanvas = this.overlayCanvasRef.el;

        if (!canvas || !overlayCanvas) {
            console.warn("Canvas elements not ready");
            return;
        }

        // Set canvas size
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        overlayCanvas.width = container.clientWidth;
        overlayCanvas.height = container.clientHeight;

        this.ctx = canvas.getContext('2d');
        this.overlayCtx = overlayCanvas.getContext('2d');

        // Set up event listeners
        this.setupCanvasEvents(overlayCanvas);

        // Initial render
        this.render();
    }

    setupCanvasEvents(canvas) {
        // Mouse events
        canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        canvas.addEventListener('wheel', this.onWheel.bind(this));
        canvas.addEventListener('dblclick', this.onDoubleClick.bind(this));

        // Touch events for mobile
        canvas.addEventListener('touchstart', this.onTouchStart.bind(this));
        canvas.addEventListener('touchmove', this.onTouchMove.bind(this));
        canvas.addEventListener('touchend', this.onTouchEnd.bind(this));

        // Keyboard events
        document.addEventListener('keydown', this.onKeyDown.bind(this));
    }

    cleanup() {
        document.removeEventListener('keydown', this.onKeyDown.bind(this));
    }

    // ============================================================================
    // RENDERING
    // ============================================================================

    render() {
        if (!this.ctx || !this.state.blueprint) return;

        const ctx = this.ctx;
        const canvas = this.canvasRef.el;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Save context state
        ctx.save();

        // Apply zoom and pan
        ctx.translate(this.state.panX, this.state.panY);
        ctx.scale(this.state.zoom, this.state.zoom);

        // Draw grid
        if (this.state.showGrid) {
            this.drawGrid(ctx);
        }

        // Draw warehouse outline
        this.drawWarehouseOutline(ctx);

        // Draw zones
        this.drawZones(ctx);

        // Draw walls
        this.drawWalls(ctx);

        // Draw doors
        this.drawDoors(ctx);

        // Draw shelves
        this.drawShelves(ctx);

        // Draw aisles
        this.drawAisles(ctx);

        // Draw locations
        this.drawLocations(ctx);

        // Draw dimensions if enabled
        if (this.state.showDimensions) {
            this.drawDimensions(ctx);
        }

        // Restore context state
        ctx.restore();

        // Render overlay (navigation path, selection, etc.)
        this.renderOverlay();
    }

    drawGrid(ctx) {
        const blueprint = this.state.blueprint;
        const gridSize = this.state.gridSize;
        const scale = this.getScale();

        ctx.strokeStyle = '#E0E0E0';
        ctx.lineWidth = 0.5;

        // Vertical lines
        for (let x = 0; x <= blueprint.length; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x * scale, 0);
            ctx.lineTo(x * scale, blueprint.width * scale);
            ctx.stroke();
        }

        // Horizontal lines
        for (let y = 0; y <= blueprint.width; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y * scale);
            ctx.lineTo(blueprint.length * scale, y * scale);
            ctx.stroke();
        }

        // Major grid lines (every 10 feet = 120 inches)
        ctx.strokeStyle = '#BDBDBD';
        ctx.lineWidth = 1;

        for (let x = 0; x <= blueprint.length; x += 120) {
            ctx.beginPath();
            ctx.moveTo(x * scale, 0);
            ctx.lineTo(x * scale, blueprint.width * scale);
            ctx.stroke();
        }

        for (let y = 0; y <= blueprint.width; y += 120) {
            ctx.beginPath();
            ctx.moveTo(0, y * scale);
            ctx.lineTo(blueprint.length * scale, y * scale);
            ctx.stroke();
        }
    }

    drawWarehouseOutline(ctx) {
        const blueprint = this.state.blueprint;
        const scale = this.getScale();

        ctx.strokeStyle = '#333333';
        ctx.lineWidth = 3;
        ctx.setLineDash([]);

        ctx.strokeRect(0, 0, blueprint.length * scale, blueprint.width * scale);

        // Fill with light background
        ctx.fillStyle = '#FAFAFA';
        ctx.fillRect(0, 0, blueprint.length * scale, blueprint.width * scale);
    }

    drawWalls(ctx) {
        const scale = this.getScale();

        for (const wall of this.state.walls) {
            ctx.strokeStyle = wall.wall_type === 'exterior' ? '#333333' : '#666666';
            ctx.lineWidth = (wall.thickness || 6) * scale / 12;
            ctx.lineCap = 'round';

            ctx.beginPath();
            ctx.moveTo(wall.start_x * scale, wall.start_y * scale);
            ctx.lineTo(wall.end_x * scale, wall.end_y * scale);
            ctx.stroke();

            // Label
            if (this.state.showLabels && wall.name) {
                const midX = ((wall.start_x + wall.end_x) / 2) * scale;
                const midY = ((wall.start_y + wall.end_y) / 2) * scale;
                this.drawLabel(ctx, wall.name, midX, midY - 10);
            }
        }
    }

    drawDoors(ctx) {
        const scale = this.getScale();

        for (const door of this.state.doors) {
            const x = door.pos_x * scale;
            const y = door.pos_y * scale;
            const width = (door.width || 36) * scale;

            ctx.save();
            ctx.translate(x, y);
            ctx.rotate((door.rotation || 0) * Math.PI / 180);

            // Door opening (gap in wall)
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(-width / 2, -3, width, 6);

            // Door swing arc
            ctx.strokeStyle = '#2196F3';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.arc(0, 0, width * 0.8, 0, Math.PI / 2);
            ctx.stroke();
            ctx.setLineDash([]);

            // Door icon
            ctx.fillStyle = '#2196F3';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('🚪', 0, -15);

            ctx.restore();

            // Label
            if (this.state.showLabels && door.name) {
                this.drawLabel(ctx, door.name, x, y - 25);
            }
        }
    }

    drawZones(ctx) {
        const scale = this.getScale();

        const zoneColors = {
            'office': 'rgba(33, 150, 243, 0.2)',
            'restricted': 'rgba(244, 67, 54, 0.2)',
            'staging': 'rgba(255, 193, 7, 0.2)',
            'loading': 'rgba(76, 175, 80, 0.2)',
            'processing': 'rgba(156, 39, 176, 0.2)',
        };

        const zoneBorders = {
            'office': '#2196F3',
            'restricted': '#F44336',
            'staging': '#FFC107',
            'loading': '#4CAF50',
            'processing': '#9C27B0',
        };

        for (const zone of this.state.zones) {
            const x = zone.pos_x * scale;
            const y = zone.pos_y * scale;
            const w = zone.width * scale;
            const h = zone.length * scale;

            // Fill
            ctx.fillStyle = zone.color || zoneColors[zone.zone_type] || 'rgba(158, 158, 158, 0.2)';
            ctx.fillRect(x, y, w, h);

            // Border
            ctx.strokeStyle = zoneBorders[zone.zone_type] || '#9E9E9E';
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 5]);
            ctx.strokeRect(x, y, w, h);
            ctx.setLineDash([]);

            // Label
            if (this.state.showLabels) {
                ctx.fillStyle = '#333333';
                ctx.font = 'bold 14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(zone.name, x + w / 2, y + h / 2);
            }
        }
    }

    drawShelves(ctx) {
        const scale = this.getScale();

        for (const shelf of this.state.shelves) {
            const x = shelf.x * scale;
            const y = shelf.y * scale;
            const w = shelf.width * scale;
            const d = shelf.depth * scale;

            // Shelf unit
            ctx.fillStyle = '#795548';
            ctx.fillRect(x, y, w, d);

            ctx.strokeStyle = '#5D4037';
            ctx.lineWidth = 1;
            ctx.strokeRect(x, y, w, d);

            // Show capacity indicator
            if (shelf.capacity && shelf.used !== undefined) {
                const utilization = shelf.used / shelf.capacity;
                ctx.fillStyle = utilization > 0.9 ? '#F44336' : utilization > 0.7 ? '#FFC107' : '#4CAF50';
                ctx.fillRect(x + 2, y + d - 6, (w - 4) * utilization, 4);
            }

            // Label
            if (this.state.showLabels && shelf.name) {
                this.drawLabel(ctx, shelf.name, x + w / 2, y - 5, 10);
            }
        }
    }

    drawAisles(ctx) {
        const scale = this.getScale();

        ctx.strokeStyle = '#FFB74D';
        ctx.lineWidth = 2;
        ctx.setLineDash([15, 10]);

        for (const aisle of this.state.aisles) {
            ctx.beginPath();
            ctx.moveTo(aisle.start_x * scale, aisle.start_y * scale);
            ctx.lineTo(aisle.end_x * scale, aisle.end_y * scale);
            ctx.stroke();

            // Aisle name
            if (this.state.showLabels && aisle.name) {
                const midX = ((aisle.start_x + aisle.end_x) / 2) * scale;
                const midY = ((aisle.start_y + aisle.end_y) / 2) * scale;
                this.drawLabel(ctx, aisle.name, midX, midY, 11, '#E65100');
            }
        }

        ctx.setLineDash([]);
    }

    drawLocations(ctx) {
        const scale = this.getScale();

        for (const loc of this.state.locations) {
            if (!loc.posx && !loc.posy) continue;

            const x = loc.posx * scale;
            const y = loc.posy * scale;

            // Location marker
            const utilization = loc.max_capacity > 0 ? loc.current_usage / loc.max_capacity : 0;
            ctx.fillStyle = utilization > 0.9 ? '#F44336' : utilization > 0.5 ? '#FFC107' : '#4CAF50';

            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.fill();

            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Location label
            if (this.state.showLabels) {
                this.drawLabel(ctx, loc.name, x, y - 15, 9);
            }
        }
    }

    drawDimensions(ctx) {
        const blueprint = this.state.blueprint;
        const scale = this.getScale();

        ctx.fillStyle = '#666666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // Length dimension
        const lengthFeet = Math.round(blueprint.length / 12);
        ctx.fillText(`${lengthFeet} ft`, (blueprint.length * scale) / 2, -20);

        // Width dimension
        ctx.save();
        ctx.translate(-20, (blueprint.width * scale) / 2);
        ctx.rotate(-Math.PI / 2);
        const widthFeet = Math.round(blueprint.width / 12);
        ctx.fillText(`${widthFeet} ft`, 0, 0);
        ctx.restore();
    }

    drawLabel(ctx, text, x, y, fontSize = 11, color = '#333333') {
        ctx.fillStyle = color;
        ctx.font = `${fontSize}px Arial`;
        ctx.textAlign = 'center';
        ctx.fillText(text, x, y);
    }

    renderOverlay() {
        if (!this.overlayCtx) return;

        const ctx = this.overlayCtx;
        const canvas = this.overlayCanvasRef.el;

        // Clear overlay
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.save();
        ctx.translate(this.state.panX, this.state.panY);
        ctx.scale(this.state.zoom, this.state.zoom);

        // Draw navigation path
        if (this.state.currentPath && this.state.currentPath.length > 0) {
            this.drawNavigationPath(ctx);
        }

        // Draw selected element highlight
        if (this.state.selectedElement) {
            this.drawSelectionHighlight(ctx);
        }

        // Draw drawing preview (for wall, etc.)
        if (this.state.isDragging && this.state.dragStart) {
            this.drawDragPreview(ctx);
        }

        // Draw picked coordinate points
        if (this.state.pickedPoints.length > 0) {
            this.drawPickedPoints(ctx);
        }

        ctx.restore();

        // Draw cursor position indicator (outside transform for screen coordinates)
        if (this.state.showCursor) {
            this.drawCursorInfo(this.overlayCtx);
        }
    }

    drawNavigationPath(ctx) {
        const scale = this.getScale();
        const path = this.state.currentPath;

        // Draw path line
        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 4;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        ctx.beginPath();
        ctx.moveTo(path[0].x * scale, path[0].y * scale);

        for (let i = 1; i < path.length; i++) {
            ctx.lineTo(path[i].x * scale, path[i].y * scale);
        }

        ctx.stroke();

        // Draw direction arrows
        ctx.fillStyle = '#2196F3';
        for (let i = 1; i < path.length - 1; i++) {
            const point = path[i];
            const prev = path[i - 1];
            const angle = Math.atan2(point.y - prev.y, point.x - prev.x);

            ctx.save();
            ctx.translate(point.x * scale, point.y * scale);
            ctx.rotate(angle);

            // Arrow
            ctx.beginPath();
            ctx.moveTo(5, 0);
            ctx.lineTo(-5, -5);
            ctx.lineTo(-5, 5);
            ctx.closePath();
            ctx.fill();

            ctx.restore();
        }

        // Start marker
        ctx.fillStyle = '#4CAF50';
        ctx.beginPath();
        ctx.arc(path[0].x * scale, path[0].y * scale, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('A', path[0].x * scale, path[0].y * scale);

        // End marker
        const end = path[path.length - 1];
        ctx.fillStyle = '#F44336';
        ctx.beginPath();
        ctx.arc(end.x * scale, end.y * scale, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText('B', end.x * scale, end.y * scale);
    }

    drawSelectionHighlight(ctx) {
        // Highlight selected element
        const elem = this.state.selectedElement;
        const scale = this.getScale();

        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);

        // TODO: Draw selection box based on element type
        ctx.setLineDash([]);
    }

    drawDragPreview(ctx) {
        const scale = this.getScale();
        const start = this.state.dragStart;
        const current = this.state.dragCurrent;

        if (!current) return;

        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);

        switch (this.state.mode) {
            case 'wall':
                ctx.beginPath();
                ctx.moveTo(start.x * scale, start.y * scale);
                ctx.lineTo(current.x * scale, current.y * scale);
                ctx.stroke();
                break;

            case 'zone':
            case 'shelf':
                const w = Math.abs(current.x - start.x);
                const h = Math.abs(current.y - start.y);
                const x = Math.min(start.x, current.x);
                const y = Math.min(start.y, current.y);
                ctx.strokeRect(x * scale, y * scale, w * scale, h * scale);
                break;
        }

        ctx.setLineDash([]);
    }

    getScale() {
        // Scale to fit canvas while maintaining aspect ratio
        if (!this.state.blueprint || !this.canvasRef.el) return 0.5;

        const canvas = this.canvasRef.el;
        const blueprint = this.state.blueprint;

        const scaleX = (canvas.width - 100) / blueprint.length;
        const scaleY = (canvas.height - 100) / blueprint.width;

        return Math.min(scaleX, scaleY, 1);
    }

    // ============================================================================
    // EVENT HANDLERS
    // ============================================================================

    onMouseDown(ev) {
        const pos = this.getMousePosition(ev);

        // Handle coordinate picking mode
        if (this.state.pickCoordinatesMode) {
            this.handleCoordinatePick(pos);
            return;
        }

        if (this.state.navigationMode) {
            this.handleNavigationClick(pos);
            return;
        }

        if (this.state.mode === 'select') {
            this.startSelection(pos);
        } else if (['wall', 'zone', 'shelf', 'aisle'].includes(this.state.mode)) {
            this.startDrawing(pos);
        }
    }

    onMouseMove(ev) {
        const pos = this.getMousePosition(ev);

        // Always update cursor position for coordinate display
        this.state.cursorPosition = {
            x: Math.round(pos.x),
            y: Math.round(pos.y),
            xFeet: Math.round(pos.x / 12 * 10) / 10,
            yFeet: Math.round(pos.y / 12 * 10) / 10
        };

        if (this.state.isDragging) {
            this.state.dragCurrent = pos;
        }

        // Always re-render overlay to show cursor position
        this.renderOverlay();
    }

    onMouseUp(ev) {
        const pos = this.getMousePosition(ev);

        if (this.state.isDragging) {
            this.finishDrawing(pos);
        }

        this.state.isDragging = false;
        this.state.dragStart = null;
        this.state.dragCurrent = null;
    }

    onWheel(ev) {
        ev.preventDefault();

        const delta = ev.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = this.state.zoom * delta;

        if (newZoom >= 0.1 && newZoom <= 5) {
            this.state.zoom = newZoom;
            this.render();
        }
    }

    onDoubleClick(ev) {
        const pos = this.getMousePosition(ev);

        if (this.state.navigationMode) {
            // Start navigation from this point
            this.state.navigationStart = pos;
            this.notification.add("Click destination to calculate route", { type: "info" });
        }
    }

    onTouchStart(ev) {
        if (ev.touches.length === 1) {
            const touch = ev.touches[0];
            this.onMouseDown({ clientX: touch.clientX, clientY: touch.clientY, target: ev.target });
        }
    }

    onTouchMove(ev) {
        if (ev.touches.length === 1) {
            const touch = ev.touches[0];
            this.onMouseMove({ clientX: touch.clientX, clientY: touch.clientY, target: ev.target });
        }
    }

    onTouchEnd(ev) {
        this.onMouseUp(ev);
    }

    onKeyDown(ev) {
        if (ev.key === 'Escape') {
            this.cancelCurrentAction();
        } else if (ev.key === 'Delete' || ev.key === 'Backspace') {
            this.deleteSelectedElement();
        }
    }

    getMousePosition(ev) {
        const canvas = this.overlayCanvasRef.el;
        const rect = canvas.getBoundingClientRect();
        const scale = this.getScale();

        const x = ((ev.clientX - rect.left - this.state.panX) / this.state.zoom) / scale;
        const y = ((ev.clientY - rect.top - this.state.panY) / this.state.zoom) / scale;

        return { x, y };
    }

    // ============================================================================
    // DRAWING ACTIONS
    // ============================================================================

    startDrawing(pos) {
        this.state.isDragging = true;
        this.state.dragStart = pos;
    }

    finishDrawing(pos) {
        const start = this.state.dragStart;
        if (!start) return;

        switch (this.state.mode) {
            case 'wall':
                this.addWall(start, pos);
                break;
            case 'zone':
                this.addZone(start, pos);
                break;
            case 'shelf':
                this.addShelf(start, pos);
                break;
            case 'aisle':
                this.addAisle(start, pos);
                break;
        }
    }

    async addWall(start, end) {
        const wall = {
            blueprint_id: this.state.blueprintId,
            name: `Wall ${this.state.walls.length + 1}`,
            start_x: Math.round(start.x),
            start_y: Math.round(start.y),
            end_x: Math.round(end.x),
            end_y: Math.round(end.y),
            thickness: 6,
            wall_type: 'interior'
        };

        try {
            const id = await this.orm.create('warehouse.wall', [wall]);
            wall.id = id[0];
            this.state.walls.push(wall);
            this.pathfinder.addObstacle(wall.start_x, wall.start_y, wall.end_x, wall.end_y);
            this.render();
            this.notification.add("Wall added", { type: "success" });
        } catch (error) {
            this.notification.add("Failed to add wall: " + error.message, { type: "danger" });
        }
    }

    async addZone(start, end) {
        const zone = {
            blueprint_id: this.state.blueprintId,
            name: `Zone ${this.state.zones.length + 1}`,
            pos_x: Math.round(Math.min(start.x, end.x)),
            pos_y: Math.round(Math.min(start.y, end.y)),
            width: Math.round(Math.abs(end.x - start.x)),
            length: Math.round(Math.abs(end.y - start.y)),
            zone_type: 'staging'
        };

        try {
            const id = await this.orm.create('warehouse.office', [zone]);
            zone.id = id[0];
            this.state.zones.push(zone);
            this.render();
            this.notification.add("Zone added", { type: "success" });
        } catch (error) {
            this.notification.add("Failed to add zone: " + error.message, { type: "danger" });
        }
    }

    addShelf(start, end) {
        const shelf = {
            id: `shelf_${Date.now()}`,
            name: `Shelf ${this.state.shelves.length + 1}`,
            x: Math.round(Math.min(start.x, end.x)),
            y: Math.round(Math.min(start.y, end.y)),
            width: Math.round(Math.abs(end.x - start.x)),
            depth: Math.round(Math.abs(end.y - start.y)),
            capacity: 50,
            used: 0
        };

        this.state.shelves.push(shelf);
        this.pathfinder.addObstacle(shelf.x, shelf.y, shelf.x + shelf.width, shelf.y + shelf.depth);
        this.saveBlueprintData();
        this.render();
        this.notification.add("Shelf added", { type: "success" });
    }

    addAisle(start, end) {
        const aisle = {
            id: `aisle_${Date.now()}`,
            name: `Aisle ${String.fromCharCode(65 + this.state.aisles.length)}`,
            start_x: Math.round(start.x),
            start_y: Math.round(start.y),
            end_x: Math.round(end.x),
            end_y: Math.round(end.y)
        };

        this.state.aisles.push(aisle);
        this.saveBlueprintData();
        this.render();
        this.notification.add("Aisle added", { type: "success" });
    }

    async saveBlueprintData() {
        const data = JSON.stringify({
            shelves: this.state.shelves,
            aisles: this.state.aisles
        });

        await this.orm.write('warehouse.blueprint', [this.state.blueprintId], {
            blueprint_data: data
        });
    }

    startSelection(pos) {
        // Find element at position
        const element = this.findElementAt(pos);
        this.state.selectedElement = element;
        this.renderOverlay();
    }

    findElementAt(pos) {
        // Check locations first
        for (const loc of this.state.locations) {
            if (loc.posx && loc.posy) {
                const dx = pos.x - loc.posx;
                const dy = pos.y - loc.posy;
                if (Math.sqrt(dx * dx + dy * dy) < 24) {
                    return { type: 'location', data: loc };
                }
            }
        }

        // Check shelves
        for (const shelf of this.state.shelves) {
            if (pos.x >= shelf.x && pos.x <= shelf.x + shelf.width &&
                pos.y >= shelf.y && pos.y <= shelf.y + shelf.depth) {
                return { type: 'shelf', data: shelf };
            }
        }

        // Check zones
        for (const zone of this.state.zones) {
            if (pos.x >= zone.pos_x && pos.x <= zone.pos_x + zone.width &&
                pos.y >= zone.pos_y && pos.y <= zone.pos_y + zone.length) {
                return { type: 'zone', data: zone };
            }
        }

        return null;
    }

    cancelCurrentAction() {
        this.state.isDragging = false;
        this.state.dragStart = null;
        this.state.dragCurrent = null;
        this.state.selectedElement = null;
        this.state.navigationMode = false;
        this.state.navigationStart = null;
        this.state.navigationEnd = null;
        this.state.pickCoordinatesMode = false;
        this.state.pickingStep = 'start';
        this.renderOverlay();
    }

    clearPickedPoints() {
        this.state.pickedPoints = [];
        this.state.pickingStep = 'start';
        this.renderOverlay();
    }

    togglePickCoordinatesMode() {
        this.state.pickCoordinatesMode = !this.state.pickCoordinatesMode;
        if (this.state.pickCoordinatesMode) {
            this.state.mode = 'select';
            this.state.pickedPoints = [];
            this.state.pickingStep = 'start';
            this.notification.add("Click to mark START point, then END point for wall coordinates", { type: "info" });
        } else {
            this.notification.add("Coordinate picking disabled", { type: "info" });
        }
        this.renderOverlay();
    }

    handleCoordinatePick(pos) {
        const point = {
            x: Math.round(pos.x),
            y: Math.round(pos.y),
            xFeet: Math.round(pos.x / 12 * 10) / 10,
            yFeet: Math.round(pos.y / 12 * 10) / 10,
            label: this.state.pickingStep === 'start' ? 'START' : 'END'
        };

        if (this.state.pickingStep === 'start') {
            // Clear previous points and add start
            this.state.pickedPoints = [point];
            this.state.pickingStep = 'end';
            this.notification.add(`START: X=${point.x}" (${point.xFeet}ft), Y=${point.y}" (${point.yFeet}ft) - Now click END point`, { type: "success" });
        } else {
            // Add end point
            this.state.pickedPoints.push(point);
            this.state.pickingStep = 'start';
            
            const start = this.state.pickedPoints[0];
            const end = point;
            
            // Show complete wall coordinates
            this.notification.add(
                `Wall coordinates: Start(${start.x}, ${start.y}) → End(${end.x}, ${end.y}) | ` +
                `In feet: Start(${start.xFeet}, ${start.yFeet}) → End(${end.xFeet}, ${end.yFeet})`,
                { type: "success", sticky: true }
            );
        }

        this.renderOverlay();
    }

    drawPickedPoints(ctx) {
        const scale = this.getScale();

        for (let i = 0; i < this.state.pickedPoints.length; i++) {
            const point = this.state.pickedPoints[i];
            const x = point.x * scale;
            const y = point.y * scale;

            // Draw marker circle
            ctx.beginPath();
            ctx.arc(x, y, 12, 0, Math.PI * 2);
            ctx.fillStyle = point.label === 'START' ? '#4CAF50' : '#F44336';
            ctx.fill();
            ctx.strokeStyle = '#FFFFFF';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Draw label
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(point.label === 'START' ? 'S' : 'E', x, y);

            // Draw coordinate box
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            const coordText = `${point.x}", ${point.y}" (${point.xFeet}ft, ${point.yFeet}ft)`;
            const textWidth = ctx.measureText(coordText).width + 10;
            const boxY = point.label === 'START' ? y - 35 : y + 20;
            
            ctx.fillRect(x - textWidth / 2, boxY, textWidth, 18);
            ctx.fillStyle = '#FFFFFF';
            ctx.font = '11px Arial';
            ctx.fillText(coordText, x, boxY + 10);

            // Draw line between points if we have both
            if (i === 1 && this.state.pickedPoints.length === 2) {
                const start = this.state.pickedPoints[0];
                ctx.beginPath();
                ctx.moveTo(start.x * scale, start.y * scale);
                ctx.lineTo(x, y);
                ctx.strokeStyle = '#2196F3';
                ctx.lineWidth = 3;
                ctx.setLineDash([8, 4]);
                ctx.stroke();
                ctx.setLineDash([]);

                // Draw length label
                const dx = point.x - start.x;
                const dy = point.y - start.y;
                const length = Math.sqrt(dx * dx + dy * dy);
                const midX = (start.x * scale + x) / 2;
                const midY = (start.y * scale + y) / 2;

                ctx.fillStyle = 'rgba(33, 150, 243, 0.9)';
                const lengthText = `Length: ${Math.round(length)}" (${Math.round(length / 12 * 10) / 10}ft)`;
                const lengthWidth = ctx.measureText(lengthText).width + 10;
                ctx.fillRect(midX - lengthWidth / 2, midY - 10, lengthWidth, 20);
                ctx.fillStyle = '#FFFFFF';
                ctx.font = 'bold 11px Arial';
                ctx.fillText(lengthText, midX, midY + 4);
            }
        }
    }

    drawCursorInfo(ctx) {
        const canvas = this.overlayCanvasRef.el;
        const pos = this.state.cursorPosition;

        // Only show if cursor is within blueprint bounds
        if (!this.state.blueprint || pos.x < 0 || pos.y < 0 ||
            pos.x > this.state.blueprint.length || pos.y > this.state.blueprint.width) {
            return;
        }

        // Draw cursor crosshair on the canvas (in transformed space)
        const scale = this.getScale();
        const screenX = pos.x * scale * this.state.zoom + this.state.panX;
        const screenY = pos.y * scale * this.state.zoom + this.state.panY;

        // Crosshair lines
        ctx.strokeStyle = 'rgba(33, 150, 243, 0.5)';
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);

        // Vertical line
        ctx.beginPath();
        ctx.moveTo(screenX, 0);
        ctx.lineTo(screenX, canvas.height);
        ctx.stroke();

        // Horizontal line
        ctx.beginPath();
        ctx.moveTo(0, screenY);
        ctx.lineTo(canvas.width, screenY);
        ctx.stroke();

        ctx.setLineDash([]);

        // Coordinate display box (bottom-right corner)
        const boxWidth = 200;
        const boxHeight = this.state.pickCoordinatesMode ? 80 : 60;
        const boxX = canvas.width - boxWidth - 10;
        const boxY = canvas.height - boxHeight - 10;

        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(boxX, boxY, boxWidth, boxHeight);

        ctx.fillStyle = '#FFFFFF';
        ctx.font = '12px monospace';
        ctx.textAlign = 'left';

        // Title
        ctx.font = 'bold 11px Arial';
        ctx.fillText('📍 Cursor Position', boxX + 10, boxY + 16);

        // Coordinates
        ctx.font = '12px monospace';
        ctx.fillText(`X: ${pos.x}" (${pos.xFeet} ft)`, boxX + 10, boxY + 34);
        ctx.fillText(`Y: ${pos.y}" (${pos.yFeet} ft)`, boxX + 10, boxY + 50);

        // Pick mode indicator
        if (this.state.pickCoordinatesMode) {
            ctx.fillStyle = this.state.pickingStep === 'start' ? '#4CAF50' : '#F44336';
            ctx.fillText(`Click: ${this.state.pickingStep.toUpperCase()} point`, boxX + 10, boxY + 68);
        }

        // Axis labels on the edges
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(screenX - 25, 5, 50, 18);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${pos.x}"`, screenX, 17);

        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(5, screenY - 9, 50, 18);
        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'left';
        ctx.fillText(`${pos.y}"`, 10, screenY + 5);
    }

    deleteSelectedElement() {
        // TODO: Implement delete selected element
        this.notification.add("Delete not yet implemented", { type: "warning" });
    }

    // ============================================================================
    // NAVIGATION
    // ============================================================================

    handleNavigationClick(pos) {
        if (!this.state.navigationStart) {
            this.state.navigationStart = pos;
            this.notification.add("Now click the destination", { type: "info" });
        } else {
            this.state.navigationEnd = pos;
            this.calculateNavigation();
        }
    }

    calculateNavigation() {
        if (!this.pathfinder || !this.state.navigationStart || !this.state.navigationEnd) {
            return;
        }

        const path = this.pathfinder.findPath(
            this.state.navigationStart.x,
            this.state.navigationStart.y,
            this.state.navigationEnd.x,
            this.state.navigationEnd.y
        );

        if (path) {
            this.state.currentPath = path;
            this.state.currentDirections = this.pathfinder.generateDirections(path, this.locationMap);
            this.renderOverlay();
            this.notification.add(
                `Route found: ${this.state.currentDirections.totalDistance} ft, ~${this.state.currentDirections.estimatedTime} min`,
                { type: "success" }
            );
        } else {
            this.notification.add("No path found between these points", { type: "warning" });
        }

        // Reset navigation points
        this.state.navigationStart = null;
        this.state.navigationEnd = null;
    }

    navigateToLocation(locationId) {
        const location = this.locationMap[locationId];
        if (!location) {
            this.notification.add("Location not found", { type: "danger" });
            return;
        }

        // Start from entrance (assumed at 0,0 or first door)
        let startX = 0;
        let startY = this.state.blueprint.width / 2;

        if (this.state.doors.length > 0) {
            startX = this.state.doors[0].pos_x;
            startY = this.state.doors[0].pos_y;
        }

        this.state.navigationStart = { x: startX, y: startY };
        this.state.navigationEnd = { x: location.x, y: location.y };
        this.calculateNavigation();
    }

    // ============================================================================
    // TOOLBAR ACTIONS
    // ============================================================================

    setMode(mode) {
        this.state.mode = mode;
        this.state.navigationMode = (mode === 'navigate');

        if (mode === 'navigate') {
            this.state.currentPath = null;
            this.state.currentDirections = null;
            this.notification.add("Click starting point, then destination", { type: "info" });
        }
    }

    toggleGrid() {
        this.state.showGrid = !this.state.showGrid;
        this.render();
    }

    toggleLabels() {
        this.state.showLabels = !this.state.showLabels;
        this.render();
    }

    zoomIn() {
        this.state.zoom = Math.min(this.state.zoom * 1.2, 5);
        this.render();
    }

    zoomOut() {
        this.state.zoom = Math.max(this.state.zoom / 1.2, 0.1);
        this.render();
    }

    resetView() {
        this.state.zoom = 1;
        this.state.panX = 50;
        this.state.panY = 50;
        this.render();
    }

    // ============================================================================
    // COORDINATE EXPORT
    // ============================================================================

    exportCoordinates() {
        const format = this.state.coordinateFormat;
        const data = this.gatherCoordinateData();

        let output;
        let filename;
        let mimeType;

        switch (format) {
            case 'json':
                output = JSON.stringify(data, null, 2);
                filename = 'warehouse_coordinates.json';
                mimeType = 'application/json';
                break;

            case 'csv':
                output = this.convertToCSV(data);
                filename = 'warehouse_coordinates.csv';
                mimeType = 'text/csv';
                break;

            case 'geojson':
                output = JSON.stringify(this.convertToGeoJSON(data), null, 2);
                filename = 'warehouse_coordinates.geojson';
                mimeType = 'application/geo+json';
                break;
        }

        this.downloadFile(output, filename, mimeType);
    }

    gatherCoordinateData() {
        return {
            blueprint: {
                id: this.state.blueprintId,
                name: this.state.blueprint?.name,
                length: this.state.blueprint?.length,
                width: this.state.blueprint?.width,
                height: this.state.blueprint?.height,
            },
            locations: this.state.locations.map(loc => ({
                id: loc.id,
                name: loc.name,
                barcode: loc.barcode,
                x: loc.posx,
                y: loc.posy,
                z: loc.posz,
                capacity: loc.max_capacity,
                usage: loc.current_usage
            })),
            walls: this.state.walls.map(w => ({
                id: w.id,
                name: w.name,
                start: { x: w.start_x, y: w.start_y },
                end: { x: w.end_x, y: w.end_y }
            })),
            zones: this.state.zones.map(z => ({
                id: z.id,
                name: z.name,
                type: z.zone_type,
                bounds: { x: z.pos_x, y: z.pos_y, width: z.width, height: z.length }
            })),
            shelves: this.state.shelves,
            aisles: this.state.aisles
        };
    }

    convertToCSV(data) {
        let csv = 'type,id,name,x,y,z,width,height\n';

        for (const loc of data.locations) {
            csv += `location,${loc.id},"${loc.name}",${loc.x},${loc.y},${loc.z},,\n`;
        }

        for (const zone of data.zones) {
            csv += `zone,${zone.id},"${zone.name}",${zone.bounds.x},${zone.bounds.y},,${zone.bounds.width},${zone.bounds.height}\n`;
        }

        for (const shelf of data.shelves) {
            csv += `shelf,${shelf.id},"${shelf.name}",${shelf.x},${shelf.y},,${shelf.width},${shelf.depth}\n`;
        }

        return csv;
    }

    convertToGeoJSON(data) {
        const features = [];

        // Warehouse outline
        features.push({
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: [[
                    [0, 0], [data.blueprint.length, 0],
                    [data.blueprint.length, data.blueprint.width], [0, data.blueprint.width],
                    [0, 0]
                ]]
            },
            properties: { type: 'warehouse', name: data.blueprint.name }
        });

        // Locations as points
        for (const loc of data.locations) {
            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Point',
                    coordinates: [loc.x, loc.y, loc.z]
                },
                properties: {
                    type: 'location',
                    id: loc.id,
                    name: loc.name,
                    barcode: loc.barcode
                }
            });
        }

        // Zones as polygons
        for (const zone of data.zones) {
            const b = zone.bounds;
            features.push({
                type: 'Feature',
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [b.x, b.y], [b.x + b.width, b.y],
                        [b.x + b.width, b.y + b.height], [b.x, b.y + b.height],
                        [b.x, b.y]
                    ]]
                },
                properties: { type: 'zone', id: zone.id, name: zone.name, zoneType: zone.type }
            });
        }

        return {
            type: 'FeatureCollection',
            features: features
        };
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    // ============================================================================
    // 3D INTEGRATION
    // ============================================================================

    async openIn3DView() {
        // Extract coordinates and open 3D view
        const coordinates = this.gatherCoordinateData();

        // Save coordinates to blueprint
        await this.orm.write('warehouse.blueprint', [this.state.blueprintId], {
            blueprint_data: JSON.stringify(coordinates)
        });

        // Open 3D view action
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'warehouse_3d_view',
            params: {
                blueprint_id: this.state.blueprintId,
                coordinates: coordinates
            }
        });
    }
}

WarehouseBlueprintEditor.template = "records_management_3d_warehouse.WarehouseBlueprintEditor";
WarehouseBlueprintEditor.components = {};

registry.category("actions").add("warehouse_blueprint_editor", WarehouseBlueprintEditor);
