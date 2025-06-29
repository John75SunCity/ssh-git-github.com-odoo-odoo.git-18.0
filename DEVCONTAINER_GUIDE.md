# DevContainer Setup Guide

This document explains the improved DevContainer configuration for the Odoo development environment.

## What Was Fixed

### 1. **Mount Path Issues** ✅
- **Before**: Only mounted `records_management` to `/workspace/records_management`
- **After**: Mount entire workspace to `/workspace` for full project access
- **Benefit**: Access to all project files including configs, scripts, and documentation

### 2. **Workspace Alignment** ✅
- **Before**: Working directory was `/home/odoo`, mount was `/workspace/records_management`
- **After**: Working directory is `/workspace`, matching the mount point
- **Benefit**: Consistent file paths and easier navigation

### 3. **Enhanced VS Code Extensions** ✅
Added development-focused extensions:
- `ms-python.black-formatter` - Python code formatting
- `ms-python.flake8` - Python linting
- `ms-vscode.vscode-json` - JSON support
- `ms-vscode.vscode-typescript-next` - TypeScript support
- `esbenp.prettier-vscode` - Code formatting
- `formulahendry.auto-rename-tag` - HTML/XML tag management

### 4. **Port Forwarding** ✅
- **Added**: Automatic forwarding of Odoo ports (8069, 8071, 8072)
- **Benefit**: Direct access to Odoo web interface from host machine

### 5. **Environment Variables** ✅
Added essential environment variables:
- `PYTHONPATH` - Python module search paths
- `ODOO_RC` - Odoo configuration file location
- `PGHOST`, `PGPORT` - PostgreSQL connection settings

### 6. **Post-Creation Setup** ✅
- **Added**: `postCreateCommand` to run `npm install` automatically
- **Benefit**: Dependencies are installed when container is created

### 7. **Build Context** ✅
- **Fixed**: Build context set to parent directory (`..`)
- **Benefit**: Dockerfile can access files in workspace root

## File Structure

```
/workspace/                    # Container workspace (mounted from host)
├── .devcontainer/
│   ├── devcontainer.json     # VS Code devcontainer configuration
│   └── Dockerfile            # Container image definition
├── records_management/       # Your Odoo module
├── requirements.txt          # Python dependencies
├── package.json             # Node.js dependencies
├── odoo.conf               # Odoo configuration
├── setup-dev.sh           # Development setup script
└── ...                    # Other project files
```

## Usage

### Starting the DevContainer

1. **Open in VS Code**: Open the project folder in VS Code
2. **Reopen in Container**: VS Code will prompt to "Reopen in Container"
3. **Wait for Build**: First time will build the Docker image (may take a few minutes)
4. **Ready**: VS Code will connect to the container with all extensions installed

### Development Workflow

1. **Run Setup Script**:
   ```bash
   ./setup-dev.sh
   ```

2. **Start Odoo**:
   ```bash
   odoo -c odoo.conf
   ```

3. **Access Odoo**: Open http://localhost:8069 in your browser

4. **Install Modules**: Use Odoo's Apps menu to install your custom modules

### Available Ports

- **8069**: Odoo HTTP interface (automatically forwarded)
- **8071**: Odoo HTTPS interface  
- **8072**: Odoo Longpolling interface

## Configuration Files

### `devcontainer.json`
Main DevContainer configuration with:
- Build settings and context
- VS Code extensions and settings
- Port forwarding
- Environment variables
- Mount points

### `Dockerfile`
Container image definition with:
- Python 3.9 base image
- System dependencies (build tools, PostgreSQL client, Node.js)
- User creation (`odoo` user)
- Dependency installation
- Proper permissions

### `odoo.conf`
Odoo configuration file with:
- Database connection settings
- Module search paths
- Development-friendly settings
- Port configurations

## Troubleshooting

### Container Won't Start
- Check if Docker is running
- Verify Dockerfile syntax
- Check build context and file paths

### VS Code Won't Connect
- Ensure `remoteUser: "odoo"` exists in container
- Check container logs for errors
- Try rebuilding the container

### Module Not Found
- Verify `addons_path` in `odoo.conf`
- Check file permissions
- Ensure module has `__manifest__.py`

### Port Already in Use
- Change ports in `devcontainer.json` and `odoo.conf`
- Kill existing processes using the ports

## Best Practices

1. **Use the setup script** - Run `./setup-dev.sh` after container creation
2. **Keep configs in version control** - All configuration files are tracked
3. **Use proper Python paths** - Environment variables are pre-configured
4. **Leverage VS Code extensions** - Pre-installed extensions provide better development experience
5. **Monitor container resources** - Odoo can be resource-intensive

## Security Notes

- Default admin password is `admin` (change for production)
- PostgreSQL connection uses default credentials (configure for production)
- Container runs as `odoo` user (non-root) for security
- Development mode is enabled (disable for production)
