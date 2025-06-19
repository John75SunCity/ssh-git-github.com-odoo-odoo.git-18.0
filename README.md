# Records Management Odoo Module

This repository contains a custom Odoo module named **Records Management** for Odoo 8.0.  
It is designed for use in a Dockerized development environment, such as GitHub Codespaces or VS Code Dev Containers.

---

## Features

- Custom models and views for managing records
- Integration with Odoo stock and web modules
- Demo data and scheduled actions for testing
- Ready for deployment and further customization

---

## Project Structure

```
.
├── records_management/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── scrm_records_management.py
│   ├── views/
│   │   ├── inventory_template.xml
│   │   └── pickup_request.xml
│   ├── security/
│   │   └── ir.model.access.csv
│   └── (other module files)
├── .devcontainer/
│   ├── devcontainer.json
│   └── .vscode/
│       ├── launch.json
│       └── settings.json
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) installed (or use GitHub Codespaces)
- (Optional) [VS Code](https://code.visualstudio.com/) with the Dev Containers extension

### Running Odoo with Docker

1. **Clone this repository:**
   ```sh
   git clone https://github.com/<your-username>/ssh-git-github.com-odoo-odoo.git-8.0.git
   cd ssh-git-github.com-odoo-odoo.git-8.0
   ```

2. **Start Odoo and PostgreSQL using Docker Compose:**
   ```sh
   docker-compose up
   ```

3. **Access Odoo in your browser:**
   - Go to [http://localhost:8069](http://localhost:8069) (or use the forwarded port in Codespaces).

4. **Create a new database:**
   - Master password: `admin` (default)
   - Choose a database name and admin password

5. **Update the Apps list and install the module:**
   - Go to **Settings > Modules > Update Modules List**
   - Search for "Records Management" in the Apps menu and click **Install**

---

## Development

- All custom code is in the `records_management` module.
- To make changes, edit the Python or XML files, then restart Odoo and update the module.
- Use the Docker CLI (`docker`) in your dev container terminal to manage containers.

---

## Troubleshooting

- **Odoo not starting?**  
  Check the logs in your terminal for errors.
- **Module not visible?**  
  Make sure you updated the Apps list and removed the "Apps" filter in the Apps menu.
- **Port 8069 not accessible?**  
  Ensure Docker is running and the port is not blocked by a firewall.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## License

This project is licensed under the MIT License.

---

## Credits

- [Odoo S.A.](https://www.odoo.com/) for the Odoo framework
- [Docker](https://www.docker.com/) for containerization
- GitHub Codespaces and VS Code for the development environment

---

*Happy
