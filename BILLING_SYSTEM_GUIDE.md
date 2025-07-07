# Records Management Billing System - Complete Guide

## Overview

Your Odoo 18 Records Management module now includes a comprehensive billing system that perfectly matches your business model. The system handles all the charges from your pricing structure and automates the entire billing process.

## Key Features

### ✅ Storage Billing
- **Standard Box Storage**: $0.32/month per box
- **Map Box Storage**: $0.45/month per box  
- **Pallet Storage**: $2.50/month per pallet
- **Specialty Box Storage**: $0.50/month per box
- **Monthly Minimum**: $45.00 with automatic adjustment

### ✅ Service Categories

#### Transportation & Delivery
- Pickup Service: $25.00
- Delivery Service: $25.00
- Trip Charge: $15.00
- Transportation: $0.75 per mile

#### Box Management
- New Box Setup: $2.50
- Refile Box: $3.00
- Refile File/Folder: $1.50
- Permanent Removal: $2.00

#### Destruction Services
- Shredding per Box: $3.50
- Hard Drive Destruction: $15.00
- Uniform Destruction: $25.00

#### Retrieval Services
- **Regular**: Box $8.50, File $3.50
- **Rush (4hr)**: Box $15.00, File $8.50, Service Fee $25.00
- **Emergency (1hr)**: Box $25.00, File $15.00, Service Fee $50.00
- **Same Day Service**: $35.00

#### Shred Bin Services
- 32 Gallon Bin: $25.00
- 64 Gallon Bin: $35.00  
- 96 Gallon Bin: $45.00
- Console Service: $30.00
- Mobile Service: $40.00
- 23 Gallon Shredinator: $20.00

#### Shred Box Services
- Standard Size: $15.00
- Double Size: $25.00
- Odd/Large Size: $35.00

#### One-Time Services
- One Time 64G Bin: $45.00
- One Time 96G Bin: $55.00

#### Special Services
- Labor: $35.00/hour
- Indexing per Box: $12.50
- File Not Found: $5.00
- Unlock Shred Bin: $15.00
- Key Delivery: $10.00
- Shred-A-Thon: $250.00
- Damaged Property - Bin: $75.00

#### Product Sales
- File Box 10-Pack (with delivery): $45.00

## How It Works

### 1. Monthly Storage Calculation
```
Example: Customer with 100 boxes
- 100 boxes × $0.32 = $32.00
- Monthly minimum: $45.00
- Adjustment needed: $13.00
- Total storage: $45.00

Invoice lines:
- Storage 100 boxes: $32.00
- Monthly Storage Minimum Fee: $13.00
- Storage Total: $45.00
```

### 2. Service Requests
- Users create service requests through the portal or backend
- System automatically calculates costs based on service type
- Costs include quantity, distance, and complexity factors
- Services are tracked through approval workflow

### 3. Monthly Billing Process
1. **Automated Monthly Job**: Creates billing period first of each month
2. **Storage Calculation**: Counts all active boxes/pallets per customer
3. **Service Integration**: Includes all completed services from the period
4. **Minimum Fee Logic**: Applies monthly minimum with adjustment line
5. **Invoice Generation**: Creates detailed Odoo invoices

### 4. Invoice Structure
Each customer invoice includes:
- Detailed storage breakdown by type
- Monthly minimum adjustment (if applicable)
- Individual service line items
- Clear pricing and quantities
- Professional formatting

## System Access

### Configuration
- **Records Management > Billing > Billing Configuration**
  - Set all pricing rates
  - Configure monthly minimums
  - Manage service fees

### Monthly Billing
- **Records Management > Billing > Billing Periods**
  - Review monthly calculations
  - Approve billing before invoicing
  - Generate customer invoices

### Service Management
- **Records Management > Services > Service Requests**
  - Create and track service requests
  - Calculate costs automatically
  - Manage approval workflows

### Customer Portal
- Customers can view their inventory
- Request services online
- View billing history
- Department-level access control

## Integration with Odoo

### Accounting Integration
- Invoices created in `account.move` (standard Odoo invoices)
- Proper revenue account mapping
- Payment tracking and reconciliation
- Financial reporting integration

### Customer Management
- Integrated with Odoo contacts
- Department and user hierarchy
- Access control and permissions
- Portal user management

### Inventory Tracking
- Box and document management
- Location tracking
- Status management (active, destroyed, etc.)
- Retention policy compliance

## Automation Features

### Monthly Billing Automation
```python
# Cron job runs monthly to:
1. Create new billing period
2. Calculate storage for all customers
3. Apply minimum fee logic
4. Include completed services
5. Generate invoices automatically
```

### Cost Calculation
- Service requests auto-calculate costs
- Quantity-based pricing
- Distance-based transportation
- Emergency service surcharges
- Labor time tracking

### Workflow Automation
- Service approval routing
- Customer notifications
- Department access controls
- Billing period management

## Sample Monthly Invoice

**City of El Paso - July 2025**
```
STORAGE SERVICES:
Standard boxes          850 × $0.32 = $272.00
Map boxes               150 × $0.45 = $67.50
Specialty boxes          25 × $0.50 = $12.50
Pallets                   5 × $2.50 = $12.50
STORAGE SUBTOTAL:                    $364.50

SERVICE CHARGES:
New boxes (10 pack)       3 × $45.00 = $135.00
Pickup service            8 × $25.00 = $200.00
Shredding per box        45 × $3.50 = $157.50
Hard drive destruction   12 × $15.00 = $180.00
Regular retrieval        28 × $8.50 = $238.00
64 gallon bin service    15 × $35.00 = $525.00
Labor hours             8.5 × $35.00 = $297.50
Transportation        120mi × $0.75 = $90.00
SERVICES SUBTOTAL:                  $1,823.00

TOTAL AMOUNT DUE:                   $2,187.50
```

## Benefits

### For Your Business
- ✅ Matches your exact pricing structure
- ✅ Automates monthly billing process
- ✅ Reduces manual invoice creation
- ✅ Integrates with Odoo accounting
- ✅ Provides detailed cost tracking
- ✅ Handles complex service pricing

### For Your Customers
- ✅ Online portal access
- ✅ Self-service capabilities
- ✅ Transparent pricing
- ✅ Department-level management
- ✅ Service request tracking
- ✅ Detailed billing breakdown

### For Compliance
- ✅ Audit trail for all charges
- ✅ Retention policy management
- ✅ Approval workflows
- ✅ Document destruction tracking
- ✅ Customer authorization records

## Next Steps

1. **Configure Pricing**: Set up your specific rates in Billing Configuration
2. **Import Customer Data**: Load existing customers and box inventory
3. **Set Up Portal Access**: Invite customer users with appropriate permissions
4. **Test Billing**: Run a test billing period to verify calculations
5. **Train Users**: Provide training on portal and service request processes
6. **Go Live**: Enable automated monthly billing

Your billing system is ready to handle your complete records management business model!
