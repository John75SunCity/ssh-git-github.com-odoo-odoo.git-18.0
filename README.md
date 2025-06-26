# Records Management for Odoo 8.0

This repository contains the `records_management` module for Odoo 8.0. It is designed to enhance document and record management capabilities within Odoo and is structured for deployment on Odoo.sh.

## Module Location

The Records Management module is located at the root:
```
records_management/
```

This structure allows the module to be:
- Deployed directly on Odoo.sh
- Published to the Odoo App Store
- Used as a standalone Odoo addon

## Features

- Centralized records storage, search, permissions, and audit trails
- Integration with stock, mail, portal, and product modules
- Pickup request management
- Shredding service functionality  
- Stock move SMS validation
- Advanced stock picking and production lot features

## Setup Instructions

### For Odoo.sh Development:
1. Connect this repository to your Odoo.sh project
2. The module will be automatically available in your Odoo.sh instance
3. Install from Apps menu in Odoo.sh

### For Local Development:
1. Clone the repository:
   ```bash
   # Using HTTPS (recommended for most users)
   git clone --recurse-submodules https://github.com/John75SunCity/ssh-git-github.com-odoo-odoo.git-8.0.git
   
   # Or using SSH (requires SSH key setup)
   git clone --recurse-submodules git@github.com:John75SunCity/ssh-git-github.com-odoo-odoo.git-8.0.git
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add the repository folder to your Odoo addons path

## Development

- The Records Management module is a complete Odoo addon with models, views, controllers, and security configurations
- Module is structured for Odoo 8.0 compatibility
- Ready for Odoo.sh deployment and App Store publication
- Includes all necessary dependencies and configurations

## Project Structure

- `records_management/` - Main Records Management module (root level for Odoo.sh)
- `requirements.txt` - Python dependencies for the Odoo modules
- `package.json` - Node.js dependencies for development tools
- `.gitmodules` - Git submodule configuration (includes Odoo core)
- `entrypoint.sh` - Service startup script
- `.devcontainer/` - VS Code development container configuration

## Odoo.sh App Store Preparation

This repository is structured to be compatible with:
- ✅ Odoo.sh automatic deployment
- ✅ Odoo App Store submission requirements
- ✅ Standard Odoo addon installation process

## Additional Notes

- Module version: 8.0.1.0.0 (compatible with Odoo 8.0)
- License: OPL-1 (Odoo Proprietary License)
- The repository includes the official Odoo 8.0 core as a submodule for development
- Ready for production deployment on Odoo.sh

## License

This project is licensed under the Odoo Proprietary License (OPL-1).