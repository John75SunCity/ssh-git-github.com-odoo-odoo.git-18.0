#!/bin/bash

# Comprehensive Debugging Script for Odoo Records Management
# This script enables detailed debugging and error logging for batch error resolution

echo "🔍 Setting up comprehensive debugging for Odoo Records Management..."

# Set debugging environment variables
export ODOO_LOG_LEVEL="debug"
export ODOO_DEV_MODE="all"

# Database name for testing
DB_NAME="records_management_debug"

# Create the debugging configuration
cat > odoo_debug.conf << 'EOF'
[options]
# Database configuration
db_name = records_management_debug
db_user = odoo
db_password = odoo
db_host = localhost
db_port = 5432

# Comprehensive logging configuration
log_level = debug
logfile = /tmp/odoo_debug.log

# Enable all development features
dev = all

# Detailed log handlers for comprehensive debugging
log_handler = :DEBUG
log_handler = odoo:DEBUG
log_handler = odoo.models:DEBUG
log_handler = odoo.fields:DEBUG
log_handler = odoo.tools.convert:DEBUG
log_handler = odoo.modules:DEBUG
log_handler = odoo.addons:DEBUG
log_handler = werkzeug:WARNING

# HTTP and SQL debugging
log_web = True
log_sql = True

# Server configuration
addons_path = addons,/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management
EOF

echo "📋 Debugging configuration created: odoo_debug.conf"

# Function to run Odoo with comprehensive debugging
debug_install() {
    echo "🚀 Installing records_management with comprehensive debugging..."
    
    ./odoo-bin \
        --config=odoo_debug.conf \
        --database=$DB_NAME \
        --init=records_management \
        --stop-after-init \
        --log-level=debug \
        --log-handler=:DEBUG \
        --log-handler=odoo.tools.convert:DEBUG \
        --log-handler=odoo.modules.loading:DEBUG \
        --dev=all \
        2>&1 | tee /tmp/odoo_install_debug.log
    
    echo "📊 Installation debug log saved to: /tmp/odoo_install_debug.log"
}

# Function to run Odoo with comprehensive debugging (update mode)
debug_update() {
    echo "🔄 Updating records_management with comprehensive debugging..."
    
    ./odoo-bin \
        --config=odoo_debug.conf \
        --database=$DB_NAME \
        --update=records_management \
        --stop-after-init \
        --log-level=debug \
        --log-handler=:DEBUG \
        --log-handler=odoo.tools.convert:DEBUG \
        --log-handler=odoo.modules.loading:DEBUG \
        --dev=all \
        2>&1 | tee /tmp/odoo_update_debug.log
    
    echo "📊 Update debug log saved to: /tmp/odoo_update_debug.log"
}

# Function to analyze debug logs for specific errors
analyze_errors() {
    echo "🔍 Analyzing debug logs for errors..."
    
    if [ -f "/tmp/odoo_install_debug.log" ]; then
        echo "📋 ParseError issues:"
        grep -n "ParseError\|ERROR.*odoo.tools.convert" /tmp/odoo_install_debug.log | head -20
        
        echo -e "\n📋 Field does not exist errors:"
        grep -n "Field.*does not exist\|KeyError.*field" /tmp/odoo_install_debug.log | head -20
        
        echo -e "\n📋 Missing action errors:"
        grep -n "is not a valid action\|action.*not found" /tmp/odoo_install_debug.log | head -20
        
        echo -e "\n📋 Access rights errors:"
        grep -n "AccessError\|access denied" /tmp/odoo_install_debug.log | head -10
        
        echo -e "\n📋 Import errors:"
        grep -n "ImportError\|ModuleNotFoundError" /tmp/odoo_install_debug.log | head -10
        
        echo -e "\n📋 Summary of all ERROR lines:"
        grep -c "ERROR" /tmp/odoo_install_debug.log
        
        echo -e "\n📋 Critical errors (first 10):"
        grep -n "ERROR" /tmp/odoo_install_debug.log | head -10
    else
        echo "❌ No debug log found. Run debug_install or debug_update first."
    fi
}

# Function to create comprehensive error report
create_error_report() {
    echo "📝 Creating comprehensive error report..."
    
    REPORT_FILE="/tmp/records_management_error_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > $REPORT_FILE << EOF
# Records Management - Comprehensive Error Report
Generated: $(date)

## System Information
Odoo Version: 18.0
Module: records_management
Database: $DB_NAME

## Business Field Analysis Results
EOF

    # Run the business field analysis and append to report
    echo "Running business field analysis..."
    python3 /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/development-tools/find_business_missing_fields.py >> $REPORT_FILE 2>&1
    
    cat >> $REPORT_FILE << EOF

## Odoo Installation/Update Errors
EOF

    # Append debug log analysis
    if [ -f "/tmp/odoo_install_debug.log" ]; then
        echo "### ParseError Issues" >> $REPORT_FILE
        grep -n "ParseError\|ERROR.*odoo.tools.convert" /tmp/odoo_install_debug.log >> $REPORT_FILE
        
        echo -e "\n### Field Does Not Exist Errors" >> $REPORT_FILE
        grep -n "Field.*does not exist\|KeyError.*field" /tmp/odoo_install_debug.log >> $REPORT_FILE
        
        echo -e "\n### Missing Action Errors" >> $REPORT_FILE
        grep -n "is not a valid action\|action.*not found" /tmp/odoo_install_debug.log >> $REPORT_FILE
        
        echo -e "\n### All Critical Errors" >> $REPORT_FILE
        grep -n "ERROR" /tmp/odoo_install_debug.log >> $REPORT_FILE
    fi
    
    echo "📊 Comprehensive error report created: $REPORT_FILE"
}

# Function to run focused debugging on specific files
debug_specific_view() {
    if [ -z "$1" ]; then
        echo "Usage: debug_specific_view <view_file_name>"
        echo "Example: debug_specific_view records_location_views.xml"
        return 1
    fi
    
    echo "🔍 Debugging specific view file: $1"
    
    # Check if file exists in views directory
    VIEW_FILE="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views/$1"
    if [ -f "$VIEW_FILE" ]; then
        echo "📋 Found view file: $VIEW_FILE"
        
        # Extract field references from the view
        echo "📋 Field references in $1:"
        grep -n 'field name=' "$VIEW_FILE" | head -20
        
        # Run targeted debugging
        echo "🚀 Running targeted debugging for $1..."
        ./odoo-bin \
            --config=odoo_debug.conf \
            --database=$DB_NAME \
            --update=records_management \
            --stop-after-init \
            --log-level=debug \
            --log-handler=odoo.tools.convert:DEBUG \
            --dev=all \
            2>&1 | grep -A5 -B5 "$1" | tee "/tmp/debug_$1.log"
            
        echo "📊 Targeted debug log saved to: /tmp/debug_$1.log"
    else
        echo "❌ View file not found: $VIEW_FILE"
    fi
}

# Function to check current error status
check_current_status() {
    echo "📊 Current Records Management Status Check..."
    
    # Run the business field analysis
    echo "🔍 Running business field analysis..."
    python3 /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/development-tools/find_business_missing_fields.py
    
    # Quick installation test
    echo "🧪 Quick installation test..."
    ./odoo-bin \
        --addons-path=addons,/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management \
        --database=test_quick \
        --init=records_management \
        --stop-after-init \
        --log-level=error \
        2>&1 | grep -E "(ERROR|ParseError|does not exist)" | head -10
}

# Help function
show_help() {
    echo "🔧 Comprehensive Debugging Commands:"
    echo "  debug_install     - Install with full debugging"
    echo "  debug_update      - Update with full debugging"
    echo "  analyze_errors    - Analyze debug logs for errors"
    echo "  create_error_report - Create comprehensive error report"
    echo "  debug_specific_view <file> - Debug specific view file"
    echo "  check_current_status - Quick status check"
    echo ""
    echo "📋 Log files:"
    echo "  /tmp/odoo_debug.log - Main debug log"
    echo "  /tmp/odoo_install_debug.log - Installation debug log" 
    echo "  /tmp/odoo_update_debug.log - Update debug log"
    echo ""
    echo "🚀 Quick start: Run 'debug_install' then 'analyze_errors'"
}

# Main execution based on argument
case "$1" in
    "install")
        debug_install
        ;;
    "update")
        debug_update
        ;;
    "analyze")
        analyze_errors
        ;;
    "report")
        create_error_report
        ;;
    "view")
        debug_specific_view "$2"
        ;;
    "status")
        check_current_status
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_help
        ;;
esac

# Make functions available for interactive use
if [ "$1" = "" ]; then
    echo "🔧 Debugging functions loaded. Use the commands above or:"
    echo "  source comprehensive_debugging.sh"
    echo "  Then call functions directly: debug_install, analyze_errors, etc."
fi
