#!/bin/bash

echo "🔧 Installing VS Code Extensions for Odoo Development..."

# Core Python development
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension ms-python.debugpy
code --install-extension ms-python.isort

# GitHub Copilot
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat

# GitHub integration
code --install-extension github.vscode-pull-request-github
code --install-extension github.codespaces

# Web development
code --install-extension ms-vscode.vscode-json
code --install-extension ms-vscode.vscode-typescript-next
code --install-extension bradlc.vscode-tailwindcss
code --install-extension formulahendry.auto-rename-tag
code --install-extension esbenp.prettier-vscode

# Remote development
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-vscode-remote.remote-ssh
code --install-extension ms-vscode.remote-server
code --install-extension ms-vscode-remote.remote-wsl

# XML/YAML support
code --install-extension redhat.vscode-xml
code --install-extension redhat.vscode-yaml
code --install-extension dotjoshjohnson.xml

# Odoo-specific extensions
code --install-extension odoo.odoo-snippets
code --install-extension jigar-patel.odoosnippets
code --install-extension scapigliato.vsc-odoo-development
code --install-extension trinhanhngoc.vscode-odoo

# Additional useful tools
code --install-extension ms-vscode.hexeditor
code --install-extension ms-toolsai.jupyter
code --install-extension davidanson.vscode-markdownlint
code --install-extension dbaeumer.vscode-eslint
code --install-extension donjayamanne.githistory
code --install-extension mechatroner.rainbow-csv
code --install-extension msoffice.microsoft-office-add-in-debugger

echo "✅ Extension installation complete!"
echo "🔄 You may need to reload VS Code window (Ctrl+Shift+P -> 'Developer: Reload Window')"
