# Records Management System - User Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation and Setup](#installation-and-setup)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Required Apps and Dependencies](#required-apps-and-dependencies)
5. [Configuration](#configuration)
6. [Daily Operations](#daily-operations)
7. [Customer Portal Access](#customer-portal-access)
8. [Reporting and Analytics](#reporting-and-analytics)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)

## Overview

The Records Management System is a comprehensive solution for managing physical document boxes and their contents. It provides advanced tracking capabilities for box locations, document retention policies, pickup requests, shredding services, and customer inventory management.

### Key Features
- **Storage Box Management**: Track physical document boxes and their locations
- **Document Management**: Manage individual documents within boxes
- **Retention Policies**: Automate document lifecycle management
- **Pickup Requests**: Handle customer document retrieval requests
- **Shredding Services**: Manage secure document destruction
- **Customer Portal**: Allow customers to view their inventory online
- **Inventory Tracking**: Comprehensive reporting on stored items
- **Billing Integration**: Track storage fees and services
- **Barcode Support**: Efficient box and document scanning

## Installation and Setup

### Prerequisites
- Odoo 18.0 Community or Enterprise Edition
- Administrative access to Odoo instance

### Installation Steps

#### Step 1: Install Required Apps
Before installing Records Management, install these apps in the following order:

1. **Navigate to Apps menu** in Odoo
2. **Install the following apps in sequence:**

   **Essential Business Apps:**
   - Sales (`sale_management`) - Click "Activate"
   - Accounting (`account`) - Click "Activate" 
   - Point of Sale (`point_of_sale`) - Click "Activate"
   - eCommerce (`website_sale`) - Click "Activate"

   **Service Management Apps:**
   - Studio (`web_studio`) - Click "Activate"
   - Quality (`quality_control`) - Click "Activate"
   - Planning (`planning`) - Click "Activate"
   - Field Service (`industry_fsm`) - Click "Activate"
   - Repairs (`repair`) - Click "Activate"

   **Advanced Features:**
   - Barcode (`stock_barcode`) - Click "Activate"
   - Subscriptions (`sale_subscription`) - Click "Activate"
   - Timesheets (`timesheet_grid`) - Click "Activate"

#### Step 2: Install Records Management
1. **Search for "Records Management"** in the Apps menu
2. **Click "Activate"** to install the module
3. **Wait for installation** to complete

#### Step 3: Initial Configuration
1. **Navigate to Records Management** → Configuration → Settings
2. **Configure company-specific settings**
3. **Set up default retention policies**
4. **Configure master data** (locations, document types, etc.)

#### Step 4: User Access Setup
1. **Assign appropriate user groups** to staff members
2. **Configure portal access** for customers
3. **Test system access** with different user roles

## User Roles and Permissions

### Records Management User (`group_records_user`)
- **Access Level**: Basic operational access
- **Permissions**:
  - View and create storage boxes
  - Manage documents
  - Process pickup requests
  - View inventory reports
  - Access customer information

### Records Management Manager (`group_records_manager`)
- **Access Level**: Full administrative access
- **Permissions**:
  - All user permissions plus:
  - Configure master data (locations, document types, tags)
  - Manage retention policies
  - Configure products and services
  - Access all configuration menus
  - Manage user permissions

### Portal Users
- **Access Level**: Customer self-service
- **Permissions**:
  - View own inventory
  - Submit pickup requests
  - View document status
  - Access billing information

## Required Apps and Dependencies

The Records Management system depends on the following Odoo modules:

### Core Dependencies (Required)
- **Base** (`base`): Core Odoo functionality
- **Product** (`product`): Product and service management
- **Stock** (`stock`): Inventory and warehouse management
- **Mail** (`mail`): Communication and messaging
- **Web** (`web`): Web interface components
- **Portal** (`portal`): Customer portal functionality
- **Base Setup** (`base_setup`): Basic configuration

### Recommended Apps for Full Functionality
Before installing Records Management, install these apps for optimal integration:

#### Business Operations
- **Sales** (`sale_management`): For customer order management and service billing
- **Point of Sale** (`point_of_sale`): For front-desk operations and quick transactions
- **eCommerce** (`website_sale`): For online customer portal and service ordering
- **Accounting** (`account`): For automated billing and financial tracking
- **Invoicing** (`account`): For service billing and customer statements

#### Service Management
- **Studio** (`web_studio`): For customizing forms and workflows
- **Quality** (`quality_control`): For service quality tracking and audits
- **Planning** (`planning`): For scheduling pickup and delivery services
- **Field Service** (`industry_fsm`): For mobile technician operations
- **Repairs** (`repair`): For equipment maintenance tracking

#### Advanced Features
- **Barcode** (`stock_barcode`): For efficient box and document scanning
- **Subscriptions** (`sale_subscription`): For recurring storage fee billing
- **Timesheets** (`timesheet_grid`): For tracking service time and labor costs

### Installation Order
1. **First, install the recommended apps in this order:**
   ```
   1. Sales (sale_management)
   2. Accounting (account) 
   3. Point of Sale (point_of_sale)
   4. eCommerce (website_sale)
   5. Studio (web_studio)
   6. Quality (quality_control)
   7. Planning (planning)
   8. Field Service (industry_fsm)
   9. Repairs (repair)
   10. Barcode (stock_barcode)
   11. Subscriptions (sale_subscription)
   12. Timesheets (timesheet_grid)
   ```

2. **Then install Records Management module**
3. **Configure required settings**

### Why These Apps Are Recommended

- **Sales & Accounting**: Essential for billing customers for storage and services
- **Point of Sale**: Useful for walk-in customers and quick service transactions
- **eCommerce**: Enhances the customer portal experience
- **Studio**: Allows customization of records management workflows
- **Quality**: Ensures service standards and compliance tracking
- **Planning**: Optimizes delivery routes and technician schedules
- **Field Service**: Mobile app support for pickup/delivery operations
- **Repairs**: Tracks maintenance of storage equipment and vehicles
- **Barcode**: Critical for efficient warehouse operations
- **Subscriptions**: Automates recurring billing for storage services
- **Timesheets**: Tracks labor costs for accurate service pricing

### Integration Benefits

#### With Sales App
- Create quotations for storage services
- Convert quotes to sales orders automatically
- Track customer contracts and renewals
- Manage service pricing and discounts

#### With Accounting App
- Automatic invoice generation for storage fees
- Track accounts receivable from customers
- Generate financial reports by service type
- Handle tax calculations and compliance

#### With Point of Sale App
- Process walk-in customer transactions
- Handle cash/card payments for services
- Print receipts and service confirmations
- Manage front-desk operations efficiently

#### With eCommerce App
- Allow customers to order services online
- Integrate with the customer portal
- Enable online payment processing
- Automate service delivery workflows

#### With Barcode App
- Scan boxes and documents quickly
- Update locations with mobile devices
- Reduce data entry errors
- Improve inventory accuracy

### Post-Installation Setup

After installing all recommended apps, you'll have access to:

1. **Enhanced Dashboard**: Comprehensive business overview
2. **Integrated Workflows**: Seamless data flow between modules
3. **Advanced Reporting**: Cross-module analytics and insights
4. **Mobile Capabilities**: Field service and barcode scanning
5. **Customer Self-Service**: Full-featured online portal
6. **Automated Billing**: Recurring charges and service invoicing

## Configuration

### Master Data Setup

#### 1. Storage Locations
**Path**: Records Management → Configuration → Master Data → Storage Locations

Configure your physical storage facilities:
- **Location Code**: Unique identifier (e.g., "WH-A-01")
- **Location Name**: Descriptive name
- **Address**: Physical address
- **Capacity**: Maximum storage capacity
- **Active**: Enable/disable location

#### 2. Document Types
**Path**: Records Management → Configuration → Master Data → Document Types

Define document categories:
- **Type Name**: Document category (e.g., "Financial Records")
- **Default Retention**: Standard retention period
- **Description**: Additional details

#### 3. Classification Tags
**Path**: Records Management → Configuration → Master Data → Classification Tags

Create organizational tags:
- **Tag Name**: Classification label
- **Color**: Visual identifier
- **Active**: Enable/disable tag

#### 4. Retention Policies
**Path**: Records Management → Inventory → Retention Policies

Set up document lifecycle rules:
- **Policy Name**: Descriptive identifier
- **Retention Period**: Duration in years
- **Action After Expiry**: Destroy, Archive, or Review
- **Document Types**: Applicable categories

### Product Configuration

#### Service Products
**Path**: Records Management → Configuration → Products and Services → Service Products

Configure billable services:
- **Storage Services**: Monthly storage fees
- **Pickup Services**: Document retrieval charges
- **Shredding Services**: Secure destruction fees
- **Scanning Services**: Document digitization

### Security Settings

#### Multi-Company Rules
The system supports multi-company environments with automatic data segregation.

#### Access Rights
Configure user access through Settings → Users & Companies → Users.

## Daily Operations

### 1. Storage Box Management

#### Creating a Storage Box
**Path**: Records Management → Operations → Storage Boxes

1. Click "Create"
2. Fill required information:
   - **Box ID**: Unique identifier (auto-generated)
   - **Customer**: Select client
   - **Location**: Storage facility
   - **Description**: Box contents summary
   - **Tags**: Classification labels

3. Save the record

#### Managing Box Contents
- Navigate to the box record
- Use the "Documents" tab to add individual documents
- Scan barcodes for quick access
- Update status as needed

### 2. Document Management

#### Adding Documents
**Path**: Records Management → Operations → Documents

1. Click "Create"
2. Configure document details:
   - **Document Name**: Descriptive title
   - **Document Type**: Select category
   - **Storage Box**: Assign to container
   - **Retention Policy**: Apply lifecycle rules
   - **Customer**: Link to client

3. Add metadata and tags as needed

#### Document Lifecycle
- **Active**: Document is stored and accessible
- **Under Review**: Retention period expired, requires review
- **Scheduled for Destruction**: Approved for shredding
- **Destroyed**: Securely destroyed with certificate

### 3. Pickup Request Processing

#### Receiving Pickup Requests
**Path**: Records Management → Operations → Pickup Requests

Requests can come from:
- Customer portal submissions
- Phone/email requests (manual entry)
- Scheduled retrievals

#### Processing Steps
1. **Review Request**: Verify customer and items
2. **Locate Items**: Check storage locations
3. **Prepare Items**: Gather requested documents/boxes
4. **Schedule Pickup**: Coordinate with customer
5. **Complete Delivery**: Update status and invoice

### 4. Shredding Services

#### Managing Destruction Requests
**Path**: Records Management → Operations → Shredding Services

1. **Create Shredding Order**:
   - Select documents/boxes for destruction
   - Verify retention compliance
   - Schedule destruction date

2. **Process Destruction**:
   - Execute secure shredding
   - Generate certificates of destruction
   - Update document statuses

### 5. Inventory Management

#### Customer Inventory Tracking
**Path**: Records Management → Inventory → Customer Inventory

- View all items by customer
- Track storage locations
- Monitor retention schedules
- Generate customer statements

## Customer Portal Access

### Portal Setup

#### Enabling Portal Access
1. **Customer Configuration**:
   - Navigate to customer record
   - Enable "Is a Company" if applicable
   - Create portal user account
   - Assign portal permissions

2. **Portal Features**:
   - **Dashboard**: Overview of storage items
   - **Box Listing**: View stored boxes
   - **Document Details**: Individual document status
   - **Pickup Requests**: Submit retrieval requests
   - **Billing**: View storage charges

### Customer Instructions

#### Accessing the Portal
1. **Login**: Use provided credentials at [your-odoo-url]/web/login
2. **Dashboard**: View inventory summary
3. **Navigation**: Use menu to access different sections

#### Submitting Pickup Requests
1. Navigate to "Pickup Requests"
2. Click "Create Request"
3. Select items for retrieval
4. Specify delivery preferences
5. Submit request

#### Viewing Inventory
1. Go to "My Inventory"
2. Browse storage boxes
3. View document details
4. Check retention schedules

## Reporting and Analytics

### Standard Reports

#### Storage Reports
**Path**: Records Management → Reporting → Storage Reports

- **Box Contents Report**: Detailed box inventories
- **Location Utilization**: Storage capacity usage
- **Customer Summary**: Items by client

#### Inventory Reports
**Path**: Records Management → Reporting → Inventory Reports

- **Customer Inventory**: Comprehensive customer view
- **Retention Schedule**: Upcoming expiry dates
- **Activity Report**: Recent transactions

### Custom Reports

#### Creating Custom Views
1. Navigate to relevant menu
2. Use "Filters" and "Group By" options
3. Save custom views for reuse
4. Export data as needed

## Advanced Features

### Barcode Integration

#### Barcode Scanning
- Use mobile device or handheld scanner
- Scan box barcodes for quick access
- Update locations and status efficiently

#### Barcode Configuration
**Path**: Records Management → Operations → Storage Boxes → Barcode

- Generate barcode labels
- Print adhesive labels
- Configure barcode formats

### Automated Workflows

#### Scheduled Actions
The system includes automated tasks:
- **Retention Monitoring**: Daily check for expired documents
- **Billing Generation**: Monthly storage fee calculation
- **Notification Alerts**: Customer and staff notifications

#### Email Notifications
Configure automatic emails for:
- Pickup request confirmations
- Retention expiry warnings
- Billing statements
- Service completions

### Integration Features

#### Fleet Management
Track delivery vehicles and routes:
- **Vehicle Assignment**: Link pickups to vehicles
- **Route Optimization**: Efficient delivery planning
- **Driver Management**: Track personnel assignments

#### Billing Integration
Automatic billing for:
- Monthly storage fees
- Pickup service charges
- Shredding service fees
- Additional services

## Troubleshooting

### Common Issues

#### 1. Portal Access Problems
**Symptoms**: Customers cannot access portal
**Solutions**:
- Verify portal user is created and active
- Check customer contact has email address
- Confirm portal permissions are assigned
- Reset password if needed

#### 2. Barcode Scanning Issues
**Symptoms**: Barcodes not scanning properly
**Solutions**:
- Clean barcode labels
- Check scanner configuration
- Verify barcode format matches system
- Test with different scanning device

#### 3. Report Generation Errors
**Symptoms**: Reports not generating or showing wrong data
**Solutions**:
- Check user permissions
- Verify date ranges
- Clear browser cache
- Check for data consistency

#### 4. Retention Policy Not Working
**Symptoms**: Documents not moving through lifecycle
**Solutions**:
- Verify scheduled actions are running
- Check retention policy configuration
- Ensure document types are properly assigned
- Review system logs for errors

### Performance Optimization

#### Database Maintenance
- Regular cleanup of old records
- Archive completed transactions
- Monitor system performance
- Update search indexes

#### User Training
- Conduct regular training sessions
- Provide quick reference guides
- Establish standard operating procedures
- Monitor user adoption

### Support and Maintenance

#### Regular Maintenance Tasks
- **Weekly**: Review pending requests and expiring documents
- **Monthly**: Generate customer statements and reports
- **Quarterly**: Review retention policies and user access
- **Annually**: System backup and performance review

#### Getting Help
- Check system logs for error messages
- Consult Odoo community forums
- Review module documentation
- Contact system administrator

### Data Security

#### Access Control
- Regular review of user permissions
- Monitor login activity
- Implement strong password policies
- Enable two-factor authentication where possible

#### Data Backup
- Daily automated backups
- Regular backup testing
- Offsite backup storage
- Document recovery procedures

---

## Appendices

### A. Keyboard Shortcuts
- **Ctrl+K**: Quick search
- **Ctrl+Enter**: Save record
- **Alt+C**: Create new record
- **Alt+E**: Edit current record

### B. API Integration
The system provides REST API endpoints for integration with external systems. Contact your administrator for API documentation.

### C. Mobile App
A companion mobile app is available for barcode scanning and basic operations. Download from your organization's app store.

---

*This manual is for Records Management System v18.0.1.0.0. For the latest updates and additional resources, visit the project repository or contact your system administrator.*
