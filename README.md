# Records Management for Odoo 8.0

This repository contains the `records_management` module for Odoo 8.0. It is designed to enhance document and record management capabilities within Odoo.

## Setup Instructions

1. Clone the repository and initialize submodules:
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

3. Configure your Odoo instance to use this repository as per your deployment method (Odoo.sh, local installation, etc.).

## Development

- Ensure all dependencies in `requirements.txt` are installed.
- This repository is configured to work with Odoo.sh for deployment.
- The project includes proper Git submodule configuration for the Odoo core.

## Project Structure

- `requirements.txt` - Python dependencies for the Odoo modules
- `package.json` - Node.js dependencies if needed
- `.gitmodules` - Git submodule configuration (includes Odoo core)
- `entrypoint.sh` - Service startup script
- `.devcontainer/` - VS Code development container configuration

## Additional Notes

- The repository is configured with the official Odoo 8.0 core as a submodule.
- Use Odoo.sh or your preferred Odoo deployment method to run the application.
- For local development, ensure you have Odoo 8.0 properly configured.

## License

This project is licensed under the MIT License.