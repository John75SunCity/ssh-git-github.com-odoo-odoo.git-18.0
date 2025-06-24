# Records Management for Odoo 8.0

This repository contains the `records_management` module for Odoo 8.0. It is designed to enhance document and record management capabilities within Odoo.

## Setup Instructions

1. Clone the repository and initialize submodules:
   ```bash
   git clone --recurse-submodules git@github.com:John75SunCity/ssh-git-github.com-odoo-odoo.git-8.0.git
   ```

2. Build and start the Docker container:
   ```bash
   docker-compose up --build
   ```

3. Access the Odoo instance at `http://localhost:8069`.

## Development

- Ensure all dependencies in `requirements.txt` are installed.
- Use the `custom_addons` directory for custom module development.

## Additional Notes

- The `entrypoint.sh` script is used to start the Odoo and PostgreSQL services. Ensure it is executable by running:
  ```bash
  chmod +x entrypoint.sh
  ```

- The `openerp_test.py` file contains test cases for the `records_management` module. Use it to validate the module's functionality:
  ```bash
  python openerp_test.py
  ```

## License

This project is licensed under the MIT License.