# Hard Drive Serial Number Scanning Feature

## Overview

The Hard Drive Serial Number Scanning feature provides a comprehensive workflow for tracking hard drives through the destruction process, ensuring NAID compliance and accurate billing.

## Key Features

### 🔍 Dual-Location Scanning Workflow
- **Customer Location Scanning**: Capture serial numbers at customer site before transport
- **Facility Verification**: Re-scan drives at facility to confirm all drives are accounted for
- **Certificate Generation**: Include verified serial numbers in destruction certificates

### 📊 Enhanced Billing Accuracy
- **Automatic Quantity Detection**: Uses actual scanned drive count for billing when available
- **Manual Override**: Falls back to manual quantity entry when scanning not used
- **Cost Calculations**: `quantity * rate` based on accurate drive counts

### 🛡️ NAID Compliance Features
- **Serial Number Hashing**: SHA256 hashing for data integrity (ISO 27001)
- **Chain of Custody**: Complete tracking from customer to destruction
- **Audit Trail**: Full scanning and verification history
- **Certificate Integration**: Verified serial numbers included in destruction certificates

## Models

### 1. ShreddingHardDrive Model (`shredding.hard_drive`)

**Core Fields:**
- `serial_number`: Required serial number for tracking
- `hashed_serial`: SHA256 hash for integrity verification
- `service_id`: Link to parent shredding service

**Customer Scanning Fields:**
- `scanned_at_customer`: Boolean flag
- `scanned_at_customer_date`: Timestamp of customer scan
- `scanned_at_customer_by`: User who performed scan
- `customer_location_notes`: Additional notes

**Facility Verification Fields:**
- `verified_before_destruction`: Boolean flag
- `verified_at_facility_date`: Timestamp of facility verification
- `verified_at_facility_by`: User who performed verification
- `facility_verification_notes`: Additional notes

**Destruction Tracking:**
- `destroyed`: Boolean flag
- `destruction_date`: Timestamp of destruction
- `destruction_method`: Method used (shred, crush, degauss, wipe)

**Certificate Generation:**
- `included_in_certificate`: Include in certificate (default: True)
- `certificate_line_text`: Generated text for certificate

### 2. HardDriveScanWizard Model (`hard_drive.scan.wizard`)

**Scanning Interface:**
- `service_id`: Target shredding service
- `scan_location`: Customer or facility scanning
- `serial_number`: Single serial entry
- `scanned_serials`: List of scanned numbers in session
- `scan_count`: Running count

**Bulk Operations:**
- `bulk_serial_input`: Multi-line serial input
- `scan_notes`: Session notes

## Workflow Process

### Phase 1: Customer Location Scanning
1. Create or open shredding service (service_type = 'hard_drive')
2. Click "📱 Scan at Customer" button
3. Use barcode scanner or manual entry to capture serial numbers
4. Supports both single and bulk scanning modes
5. Automatically creates `shredding.hard_drive` records with customer scan flags

### Phase 2: Transport to Facility
- Hard drives are transported with chain of custody documentation
- Serial numbers are preserved in system for verification

### Phase 3: Facility Verification
1. Click "🏭 Verify at Facility" button
2. Re-scan all serial numbers to confirm receipt
3. System validates against customer scan list
4. Marks drives as verified before destruction

### Phase 4: Destruction Process
1. Select destruction method for each drive
2. Mark drives as destroyed with timestamp
3. Generate destruction certificate with verified serial numbers

## Action Methods

### Service-Level Actions
- `action_scan_hard_drives_customer()`: Open customer scanning wizard
- `action_scan_hard_drives_facility()`: Open facility verification wizard
- `action_view_hard_drives()`: View all drives for service

### Hard Drive Actions
- `action_mark_customer_scanned()`: Mark as scanned at customer
- `action_mark_facility_verified()`: Mark as verified at facility
- `action_mark_destroyed()`: Mark as destroyed

### Wizard Actions
- `action_scan_serial()`: Process single serial number
- `action_bulk_scan()`: Process multiple serial numbers
- `action_finish_scan()`: Complete scanning session

## Computed Fields

### Service-Level Counts
- `hard_drive_scanned_count`: Count of drives scanned at customer
- `hard_drive_verified_count`: Count of drives verified at facility

### Billing Integration
- `total_cost`: Uses scanned count when available, falls back to manual quantity
- `total_charge`: Same logic for customer billing

## Views and Interface

### 1. Shredding Service Form
- **Hard Drive Scanning Tab**: Added when service_type = 'hard_drive'
- **Progress Indicators**: Shows scanned vs verified counts
- **Action Buttons**: Customer scanning, facility verification, view all
- **Drive List**: Inline list with status indicators and action buttons

### 2. Hard Drive Scan Wizard
- **Location Selection**: Customer or facility scanning mode
- **Serial Entry**: Single or bulk scanning interface
- **Progress Tracking**: Running count and scanned list
- **Session Management**: Notes and completion actions

### 3. Hard Drive Detail Form
- **Scanning History**: Complete workflow tracking
- **Status Management**: Action buttons for workflow progression
- **Certificate Integration**: Auto-generated certificate text

## Security and Permissions

### Access Rights
- **Users**: Read, write, create (no delete) on hard drives
- **Managers**: Full CRUD access on all models
- **Wizards**: Full access for all user levels

### Data Integrity
- **Serial Hashing**: Automatic SHA256 hashing for verification
- **Duplicate Prevention**: Validation against existing serials
- **Audit Trail**: Complete user and timestamp tracking

## Testing

### Test Coverage
- `test_hard_drive_scanning.py`: Comprehensive test suite covering:
  - Hard drive creation from scans
  - Workflow progression (customer → facility → destruction)
  - Computed field calculations
  - Billing accuracy with scanned counts
  - Certificate line generation
  - Wizard functionality (single and bulk scanning)
  - Duplicate serial handling
  - Security and access controls

## Configuration

### Prerequisites
1. Service type must be set to 'hard_drive'
2. Proper user permissions in Records Management groups
3. Barcode scanners configured for serial number capture

### Setup Steps
1. Create shredding service with service_type = 'hard_drive'
2. Configure rate and base quantity
3. Use scanning workflow for accurate tracking and billing

## Benefits

### 🎯 Operational Benefits
- **Accuracy**: Eliminates manual counting errors
- **Efficiency**: Streamlined barcode scanning workflow
- **Compliance**: Full NAID AAA compliance tracking
- **Billing**: Accurate charge calculations

### 🛡️ Security Benefits
- **Data Integrity**: SHA256 hashing for verification
- **Audit Trail**: Complete tracking history
- **Chain of Custody**: Documented transfer process
- **Certificate Quality**: Verified serial number inclusion

### 💰 Business Benefits
- **Revenue Accuracy**: Billing based on actual quantities
- **Customer Confidence**: Transparent tracking process
- **Compliance Value**: NAID certification support
- **Efficiency Gains**: Reduced manual processes

## Integration Points

### 1. Certificate Generation
- Serial numbers automatically included in destruction certificates
- Certificate text generated from drive details
- NAID compliance verification integrated

### 2. Billing System
- Automatic quantity calculation from scanned counts
- Rate multiplication using actual verified quantities
- Invoice generation with accurate line items

### 3. Inventory Management
- Links to product catalog for hard drive destruction services
- Cost tracking and reporting integration
- Department billing allocation support

## Future Enhancements

### Planned Features
- **Mobile App Integration**: Native mobile scanning app
- **QR Code Generation**: Generate QR codes for chain of custody
- **Photo Documentation**: Camera integration for visual verification
- **GPS Tracking**: Location verification for scanning events
- **API Integration**: Customer portal scanning access

### Technical Improvements
- **Batch Processing**: Async processing for large scanning sessions
- **Data Export**: CSV/Excel export of scanning data
- **Reporting Dashboard**: Analytics for scanning efficiency
- **Integration APIs**: Third-party system connectivity
