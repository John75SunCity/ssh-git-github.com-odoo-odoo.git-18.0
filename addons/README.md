# External Addons Directory

This directory contains submodules for external Odoo modules used in the project. These are managed via the `.gitmodules` file and provide additional functionality to enhance the Records Management module (e.g., async processing for shredding workflows, advanced reporting for NAID audits).

## Included Submodules
- **queue_job**: Asynchronous task processing (e.g., for background shredding or bale invoicing to improve performance).
- **server_tools**: Additional server utilities for system management and monitoring.
- **reporting_engine**: Advanced reporting capabilities (e.g., custom NAID-compliant destruction certificates and inventory reports).
- **stock_logistics**: Enhanced inventory features for better tracking of physical assets like document boxes and paper bales.
- **web**: Enhanced UI components for a modern, user-friendly interface (e.g., responsive dashboards and visualizations like trailer loading).

## Setup and Usage
These submodules are automatically fetched and initialized using Git submodules. Run the following command in the repository root to set them up:

```bash
git submodule update --init --recursive
