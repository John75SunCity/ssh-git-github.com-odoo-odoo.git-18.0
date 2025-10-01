/** @odoo-module **/
/**
 * Portal Inventory Owl Component
 * Modern interactive inventory management for portal users.
 */
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PortalInventoryComponent extends Component {
    static template = "records_management.PortalInventoryComponent";
    static props = {
        pageSize: { type: Number, optional: true },
    };

    setup() {
        this.searchTimeout = null;
        this.autoRefresh = null;
        this.state = useState({
            rawItems: [],
            filteredItems: [],
            searchQuery: "",
            filters: { type: "", status: "" },
            sortBy: "date_desc",
            viewMode: "grid",
            selectionMode: false,
            selectedIds: new Set(),
            allSelected: false,
            isLoading: false,
            currentPage: 1,
            pageSize: this.props.pageSize || 24,
            totalPages: 1,
        });

        onMounted(async () => {
            await this.fetchInventory();
            this.restorePreferences();
            this.autoRefresh = setInterval(() => this.refreshData(), 120000); // 2 min
        });

        onWillUnmount(() => {
            if (this.searchTimeout) clearTimeout(this.searchTimeout);
            if (this.autoRefresh) clearInterval(this.autoRefresh);
        });
    }

    restorePreferences() {
        try {
            const view = localStorage.getItem("portal_inventory_view");
            if (view) this.state.viewMode = view;
        } catch (_) {}
    }

    persistPreferences() {
        try { localStorage.setItem("portal_inventory_view", this.state.viewMode); } catch(_) {}
    }

    async fetchInventory() {
        this.state.isLoading = true;
        try {
            const result = await rpc("/my/inventory/data", {
                page: this.state.currentPage,
                page_size: this.state.pageSize,
                filters: this.state.filters,
                search: this.state.searchQuery,
                sort: this.state.sortBy,
            });
            if (result.success) {
                // Normalize items
                const items = (result.items || []).map((it) => this.normalizeItem(it));
                this.state.rawItems = items;
                this.state.totalPages = Math.max(1, Math.ceil((result.total || items.length) / this.state.pageSize));
                this.applyClientFilters();
            }
        } catch (error) {
            console.error("Inventory load error", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    normalizeItem(it) {
        const status = (it.status || it.state || "").toLowerCase();
        const statusMap = { active: "success", archived: "warning", destroyed: "danger" };
        return {
            id: it.id,
            name: it.name || it.display_name || `Item ${it.id}`,
            reference: it.reference || it.ref || "",
            type: it.type || it.model || it._name || "unknown",
            displayType: (it.type_label || it.type || "").replace(/_/g, " ").toUpperCase(),
            location: it.location || it.location_name || (it.location_id && it.location_id[1]) || "",
            status: status,
            statusColor: statusMap[status] || "secondary",
            statusLabel: status ? status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "Unknown",
            date: it.date || it.create_date || "",
        };
    }

    applyClientFilters() {
        let items = [...this.state.rawItems];
        const q = this.state.searchQuery.toLowerCase();
        if (q) {
            items = items.filter((i) =>
                i.name.toLowerCase().includes(q) ||
                (i.reference && i.reference.toLowerCase().includes(q)) ||
                (i.location && i.location.toLowerCase().includes(q))
            );
        }
        if (this.state.filters.type) items = items.filter((i) => i.type === this.state.filters.type);
        if (this.state.filters.status) items = items.filter((i) => i.status === this.state.filters.status);

        // Sort
        items.sort((a, b) => {
            switch (this.state.sortBy) {
                case "date_desc": return (b.date || "") > (a.date || "") ? 1 : -1;
                case "date_asc": return (a.date || "") > (b.date || "") ? 1 : -1;
                case "name_asc": return a.name.localeCompare(b.name);
                case "name_desc": return b.name.localeCompare(a.name);
            }
            return 0;
        });

        this.state.filteredItems = items;
        this.state.allSelected = items.length && items.every((it) => this.state.selectedIds.has(it.id));
    }

    onSearchInput(ev) {
        const val = ev.target.value;
        this.state.searchQuery = val;
        if (this.searchTimeout) clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => this.applyClientFilters(), 250);
    }

    applyFilters() {
        this.applyClientFilters();
    }

    clearFilters() {
        this.state.searchQuery = "";
        this.state.filters = { type: "", status: "" };
        this.state.sortBy = "date_desc";
        this.applyClientFilters();
    }

    toggleView() {
        this.state.viewMode = this.state.viewMode === "grid" ? "list" : "grid";
        this.persistPreferences();
    }

    toggleSelectionMode() {
        this.state.selectionMode = !this.state.selectionMode;
        if (!this.state.selectionMode) this.clearSelection();
    }

    toggleSelectAll(ev) {
        if (ev.target.checked) {
            this.state.filteredItems.forEach((it) => this.state.selectedIds.add(it.id));
        } else {
            this.state.selectedIds.clear();
        }
        this.applyClientFilters();
    }

    toggleSelect(item) {
        if (this.state.selectedIds.has(item.id)) this.state.selectedIds.delete(item.id);
        else this.state.selectedIds.add(item.id);
        this.applyClientFilters();
    }

    rowClick(ev, item) {
        if (!this.state.selectionMode) return;
        this.toggleSelect(item);
    }

    cardClick(ev, item) {
        if (this.state.selectionMode) {
            this.toggleSelect(item);
        }
    }

    clearSelection() {
        this.state.selectedIds.clear();
        this.applyClientFilters();
    }

    async viewItem(item) {
        window.location.href = `/my/inventory/${item.id}`;
    }

    async requestPickup(item) {
        try {
            await rpc("/my/inventory/add_to_pickup", { item_id: item.id });
            this.showToast("Added to pickup request", "success");
        } catch (e) { this.showToast("Pickup error", "danger"); }
    }

    async requestDestruction(item) {
        if (!confirm("Request destruction of this item?")) return;
        try {
            await rpc("/my/inventory/request_destruction", { item_id: item.id });
            this.showToast("Destruction requested", "warning");
        } catch (e) { this.showToast("Destruction error", "danger"); }
    }

    async batchToPickup() {
        if (!this.state.selectedIds.size) return;
        try {
            await rpc("/my/inventory/batch_pickup", { ids: [...this.state.selectedIds] });
            this.showToast("Batch pickup requested", "success");
            this.clearSelection();
        } catch (e) { this.showToast("Batch error", "danger"); }
    }

    async batchDestruction() {
        if (!this.state.selectedIds.size) return;
        if (!confirm("Request destruction for selected items?")) return;
        try {
            await rpc("/my/inventory/batch_destruction", { ids: [...this.state.selectedIds] });
            this.showToast("Batch destruction requested", "warning");
            this.clearSelection();
        } catch (e) { this.showToast("Batch error", "danger"); }
    }

    async addTempInventory() {
        const type = prompt("Type (box/document/file):");
        if (!type) return;
        const description = prompt("Description:");
        if (!description) return;
        try {
            const res = await rpc("/my/inventory/add_temp", { type, description });
            if (res.barcode) {
                this.showToast(`Temp created: ${res.barcode}`, "success");
                this.refreshData();
            } else {
                this.showToast("Creation failed", "danger");
            }
        } catch (e) { this.showToast("Creation error", "danger"); }
    }

    async refreshData() {
        await this.fetchInventory();
    }

    async goToPage(page) {
        if (page < 1 || page > this.state.totalPages) return;
        this.state.currentPage = page;
        await this.fetchInventory();
    }

    showToast(message, type = "info") {
        const containerId = "portal_inventory_toasts";
        let container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement("div");
            container.id = containerId;
            container.style.position = "fixed";
            container.style.top = "20px";
            container.style.right = "20px";
            container.style.zIndex = 9999;
            document.body.appendChild(container);
        }
        const alert = document.createElement("div");
        alert.className = `alert alert-${type} py-2 px-3 mb-2 shadow-sm fade show`;
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="close ml-2" data-dismiss="alert">&times;</button>
            </div>`;
        container.appendChild(alert);
        setTimeout(() => { if (alert.parentNode) alert.parentNode.removeChild(alert); }, 4500);
    }
}

registry.category("public_components").add("records_management.PortalInventoryComponent", PortalInventoryComponent);
