# Hierarchical Inventory Architecture for Records Management

## Business Requirements

Records management service provider that tracks physical items at multiple levels:

1. **Containers** (boxes) - Customer's property stored in warehouse
2. **File Folders** - Removable from containers for delivery to customer
3. **Individual Documents** - Removable from files for scanning/delivery
4. **Digital Scans** - Electronic copies (not physical inventory)

### Service Scenarios

**Scenario 1: Deliver entire container**
- Container leaves warehouse → Customer site
- Track: Container location change
- Return: Container back to warehouse shelf

**Scenario 2: Deliver file folder only**
- File removed from container → Delivery
- Track: File location change, container stays in warehouse
- Return: File back to original container

**Scenario 3: Scan individual document**
- Document removed from file → Scanning department
- Scan created → Email/portal delivery
- Track: Document location, create digital copy
- Return: Document back to file, file back to container

## Stock.Quant Hierarchical Architecture

### Level 1: Container (Box)
```python
stock.quant:
    product_id = "Records Box - Standard"
    lot_id = "BOX-12345"
    owner_id = res.partner (City of Las Cruces)
    location_id = stock.location (Warehouse / Aisle 5 / Shelf B-3)
    is_records_container = True
    
records.container:
    quant_id = stock.quant (link to above)
    barcode = "BOX-12345"
    container_type_id = "Standard Box"
    # All custom RM fields
```

### Level 2: File Folder (inside container)
```python
stock.quant:
    product_id = "File Folder"
    lot_id = "FILE-HR-2024-001"
    owner_id = res.partner (City of Las Cruces)
    location_id = stock.location (same as container when stored)
    is_records_file = True
    parent_quant_id = Container's quant_id (track origin)
    
records.file:
    quant_id = stock.quant (link to above)
    barcode = "FILE-HR-2024-001"
    container_id = records.container (which box it belongs to)
    # Custom file metadata
```

### Level 3: Individual Document (inside file)
```python
stock.quant:
    product_id = "Document/Paper"
    lot_id = "DOC-CONTRACT-JD-001"
    owner_id = res.partner (City of Las Cruces)
    location_id = stock.location (scanning dept when removed)
    is_records_document = True
    parent_quant_id = File's quant_id (track origin)
    
records.document:
    quant_id = stock.quant (link to above)
    barcode = "DOC-CONTRACT-JD-001"
    file_id = records.file (which file it belongs to)
    container_id = records.container (original container)
    # Custom document metadata
```

### Level 4: Digital Scan (NOT inventory)
```python
# No stock.quant - digital asset only
records.document.scan:
    document_id = records.document
    scan_file = Binary (PDF)
    scan_date = Date
    sent_via = Selection (email/portal/fax)
    # Digital delivery tracking
```

## Stock Movement Scenarios

### Movement 1: Deliver File to Customer
```python
# Create stock.picking (Delivery Order)
stock.picking:
    picking_type_id = "Delivery"
    partner_id = City of Las Cruces
    
stock.move:
    product_id = "File Folder"
    product_uom_qty = 1
    
stock.move.line:
    lot_id = "FILE-HR-2024-001"
    location_id = Warehouse / Aisle 5
    location_dest_id = Customer / City of Las Cruces Site
    owner_id = City of Las Cruces (preserved!)
    
# Result:
# - File quant moved to customer location
# - Container quant stays at warehouse
# - parent_quant_id preserved (remembers it came from BOX-12345)
```

### Movement 2: Return File to Container
```python
# Create stock.picking (Receipt/Return)
stock.picking:
    picking_type_id = "Receipt"
    partner_id = City of Las Cruces
    
stock.move.line:
    lot_id = "FILE-HR-2024-001"
    location_id = Customer / City of Las Cruces Site
    location_dest_id = Warehouse / Aisle 5 / Shelf B-3
    owner_id = City of Las Cruces (preserved!)
    
# Result:
# - File quant back to warehouse (same location as container)
# - records.file.container_id still links to BOX-12345
```

### Movement 3: Remove Document for Scanning
```python
stock.move.line:
    lot_id = "DOC-CONTRACT-JD-001"
    location_id = Warehouse / Aisle 5 (from file)
    location_dest_id = Warehouse / Scanning Department
    owner_id = City of Las Cruces
    
# Result:
# - Document quant at scanning location
# - parent_quant_id points to FILE-HR-2024-001
# - Create digital scan (no quant - just binary data)
```

## Portal User Experience

### Portal User Requests
```python
# Customer logs in and sees their inventory grouped hierarchically
owner_id = user.partner_id.commercial_partner_id

# All their containers
containers = stock.quant.search([
    ('owner_id', '=', owner_id),
    ('is_records_container', '=', True)
])

# All their files (whether in containers or out for delivery)
files = stock.quant.search([
    ('owner_id', '=', owner_id),
    ('is_records_file', '=', True)
])

# Current location shows:
# - In warehouse: Available for retrieval
# - In transit: Being delivered
# - At customer site: Currently with customer
```

### Portal Retrieval Request Flow
```python
# 1. Customer requests specific file
portal.request:
    request_type = "file_retrieval"
    requested_items = [FILE-HR-2024-001]
    
# 2. System creates delivery order
stock.picking:
    partner_id = City of Las Cruces
    move_line_ids = [(lot_id=FILE-HR-2024-001)]
    
# 3. Barcode scan to pick
# Warehouse staff scans FILE-HR-2024-001
# System confirms: From BOX-12345, Aisle 5, Shelf B-3

# 4. Delivery
# File location_id changes: Warehouse → Customer Site

# 5. Return
# Customer done → return request → reverse movement
```

## Benefits of This Architecture

### ✅ Full Traceability
- Every physical item has stock.quant record
- Stock moves create audit trail
- parent_quant_id tracks "where it came from"
- owner_id ALWAYS preserved (customer ownership)

### ✅ Barcode Integration
- Each level gets unique barcode (lot_id)
- Scan container → see all files inside
- Scan file → see all documents inside
- Scan document → see parent file + container

### ✅ Location Accuracy
- Real-time location tracking via stock.quant.location_id
- Warehouse staff: "Where is FILE-HR-2024-001?" → Scan shows exact location
- Customer portal: "Where are my files?" → Shows which at warehouse, which in transit, which at site

### ✅ Delivery Orders
- stock.picking = Delivery order (PDF printable)
- Lists all items being delivered
- Barcode scannable for validation
- Electronic signature capture
- Return tracking

### ✅ Inventory Valuation
- Optional: Track storage costs per item
- Billing based on stock.quant records
- Monthly storage: Count quants where owner_id = customer

### ✅ Portal Visibility
- Customer sees ALL their inventory:
  - Containers at warehouse
  - Files out for delivery
  - Documents being scanned
- Real-time status updates via stock move tracking

## Implementation Checklist

### Phase 1: Extend Stock Models
- [x] stock.quant (is_records_container, is_records_file, is_records_document)
- [x] stock.location (records management fields)
- [ ] stock.quant.parent_quant_id (track hierarchical origin)

### Phase 2: Link Existing Models
- [ ] records.container.quant_id → stock.quant
- [ ] records.file.quant_id → stock.quant (create model if needed)
- [ ] records.document.quant_id → stock.quant
- [ ] All three: owner_id from quant, location_id from quant

### Phase 3: Movement Tracking
- [ ] Extend stock.picking for retrieval/delivery/return
- [ ] Portal request → stock.picking creation
- [ ] Barcode scanning workflow
- [ ] Return workflow (put items back where they came from)

### Phase 4: Portal Integration
- [ ] Portal: View inventory grouped by container/file/document
- [ ] Portal: Request file retrieval
- [ ] Portal: Track delivery status
- [ ] Portal: Request return
- [ ] Portal: View movement history

### Phase 5: Billing Integration
- [ ] Count quants by owner_id for monthly billing
- [ ] Track item-level charges (scan fee, delivery fee, etc.)
- [ ] Invoice generation based on stock movements

## Migration Strategy

### Option A: Dual System (Temporary)
- Keep existing records.container, records.document
- Add quant_id links
- Gradually populate stock.quant records
- Sync location changes

### Option B: Full Migration
- Create stock.quant for each container/file/document
- Migrate all location data
- Switch to stock-first approach
- Deprecate standalone location tracking

## Key Odoo Features Leveraged

1. **stock.quant.owner_id** - Customer ownership
2. **stock.location hierarchy** - Warehouse → Aisle → Shelf
3. **stock.lot (Serial Numbers)** - Unique barcode per item
4. **stock.picking** - Delivery/return orders
5. **stock.move.line** - Detailed movement tracking
6. **Barcode scanning** - Native Odoo mobile app support
7. **Portal views** - Customer self-service
8. **Inventory reports** - Standard Odoo reporting

## Conclusion

This hierarchical architecture:
- ✅ Tracks containers, files, AND documents independently
- ✅ Preserves "where it came from" (parent_quant_id)
- ✅ Maintains customer ownership through all movements
- ✅ Enables partial delivery (just a file, just a document)
- ✅ Full audit trail via stock moves
- ✅ Portal-ready for customer self-service
- ✅ Billing-ready via inventory counts
- ✅ Leverages Odoo's robust stock infrastructure
