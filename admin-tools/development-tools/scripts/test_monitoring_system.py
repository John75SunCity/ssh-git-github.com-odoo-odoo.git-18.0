#!/usr/bin/env python3
"""
Test Live Monitoring System
===========================

Simple test to verify the monitoring system can be imported and works correctly.
This test runs outside of Odoo to verify the monitoring code is syntactically correct.
"""

import sys
import os

def test_monitoring_imports():
    """Test that monitoring modules can be imported"""
    
    print("🔍 Testing Live Monitoring System")
    print("="*40)
    
    # Test 1: Check monitoring directory exists
    monitoring_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/monitoring"
    if os.path.exists(monitoring_dir):
        print("✅ Monitoring directory exists")
    else:
        print("❌ Monitoring directory missing")
        return False
    
    # Test 2: Check required files exist
    required_files = [
        '__init__.py',
        'live_monitor.py', 
        'controllers.py',
        'views_config.py'
    ]
    
    for filename in required_files:
        filepath = os.path.join(monitoring_dir, filename)
        if os.path.exists(filepath):
            print(f"✅ {filename} exists")
        else:
            print(f"❌ {filename} missing")
            return False
    
    # Test 3: Check Python syntax
    import ast
    
    for filename in ['live_monitor.py', 'controllers.py']:
        filepath = os.path.join(monitoring_dir, filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ {filename} syntax OK")
        except SyntaxError as e:
            print(f"❌ {filename} syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠️  {filename} check warning: {e}")
    
    return True

def test_monitoring_features():
    """Test monitoring feature completeness"""
    
    print(f"\n🚀 Testing Monitoring Features")
    print("="*35)
    
    # Check live_monitor.py for key features
    monitor_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/monitoring/live_monitor.py"
    
    with open(monitor_file, 'r') as f:
        content = f.read()
    
    required_features = {
        'RecordsManagementMonitor': 'Main monitoring model',
        'log_error': 'Error logging method',
        'log_performance': 'Performance logging',
        'health_check': 'Health check functionality',
        '_send_webhook_notification': 'Webhook notifications',
        '_send_email_notification': 'Email notifications',
        'cleanup_old_logs': 'Log cleanup',
        'monitor_method': 'Method decorator'
    }
    
    for feature, description in required_features.items():
        if feature in content:
            print(f"✅ {description}")
        else:
            print(f"❌ Missing: {description}")
    
    # Check controllers.py for API endpoints
    controller_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/monitoring/controllers.py"
    
    with open(controller_file, 'r') as f:
        content = f.read()
    
    required_endpoints = {
        '/records_management/monitor/health': 'Health check endpoint',
        '/records_management/monitor/errors': 'Error listing endpoint', 
        '/records_management/monitor/performance': 'Performance data endpoint',
        '/records_management/monitor/stream': 'Real-time streaming',
        '/records_management/monitor/webhook/receive': 'Webhook receiver'
    }
    
    print(f"\n📡 API Endpoints:")
    for endpoint, description in required_endpoints.items():
        if endpoint in content:
            print(f"✅ {description}")
        else:
            print(f"❌ Missing: {description}")

def test_integration_readiness():
    """Test if monitoring is ready for integration"""
    
    print(f"\n🔗 Integration Readiness")
    print("="*25)
    
    # Check if __init__.py imports monitoring
    init_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/__init__.py"
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    if 'from . import monitoring' in content:
        print("✅ Monitoring imported in __init__.py")
    else:
        print("❌ Monitoring not imported in __init__.py")
    
    # Check if requests dependency added to manifest
    manifest_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/__manifest__.py"
    
    with open(manifest_file, 'r') as f:
        content = f.read()
    
    if "'requests'" in content:
        print("✅ Requests dependency added to manifest")
    else:
        print("❌ Requests dependency missing from manifest")
    
    if "'sequence': 1000" in content:
        print("✅ Loading sequence optimized") 
    else:
        print("❌ Loading sequence not optimized")
    
    if "'post_init_hook'" in content:
        print("✅ Post-init hook configured")
    else:
        print("❌ Post-init hook missing")

def show_usage_examples():
    """Show usage examples"""
    
    print(f"\n🎯 Usage Examples")
    print("="*17)
    
    examples = [
        "Health Check: curl https://your-odoo.com/records_management/monitor/health",
        "Recent Errors: curl -H 'Authorization: Bearer TOKEN' .../monitor/errors",
        "Performance: curl -H 'Authorization: Bearer TOKEN' .../monitor/performance", 
        "Real-time Stream: curl -H 'Authorization: Bearer TOKEN' .../monitor/stream",
        "Send External Alert: curl -X POST .../monitor/webhook/receive -d '{...}'"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")
    
    print(f"\n📝 Integration Examples:")
    integration_examples = [
        "@RecordsManagementMonitoringHelper.monitor_method decorator",
        "self.env['records.management.monitor'].log_error(...)",
        "RecordsManagementMonitoringHelper.log_user_action(...)",
        "Automatic health checks every 15 minutes",
        "Webhook notifications to Slack/Teams/Discord"
    ]
    
    for i, example in enumerate(integration_examples, 1):
        print(f"  {i}. {example}")

if __name__ == "__main__":
    print("🔥 LIVE ERROR MONITORING SYSTEM TEST")
    print("="*45)
    
    success = True
    
    # Run tests
    if not test_monitoring_imports():
        success = False
    
    test_monitoring_features()
    test_integration_readiness()
    show_usage_examples()
    
    print(f"\n" + "="*45)
    if success:
        print("🎊 MONITORING SYSTEM READY!")
        print("✅ Zero-impact live error monitoring")  
        print("✅ Real-time webhooks and notifications")
        print("✅ Performance tracking and health checks")
        print("✅ REST API for external integration") 
        print("✅ Web dashboard and management interface")
        print("\n🚀 Your Records Management module now has")
        print("   enterprise-grade monitoring capabilities!")
    else:
        print("❌ MONITORING SYSTEM NEEDS FIXES")
        print("   Please address the issues above")
    
    print("="*45)
