# 🔥 LIVE ERROR MONITORING FOR RECORDS MANAGEMENT

## 🎯 **NON-INTRUSIVE MONITORING SYSTEM**

This monitoring system **DOES NOT AFFECT MODULE LOADING** and provides real-time error tracking and notifications directly from your Odoo Records Management module.

---

## 🚀 **QUICK SETUP GUIDE**

### **1. Add Monitoring to Your Module**

#### **Update `__init__.py`**

```python
# Add to your existing __init__.py
from . import monitoring
```

#### **Update `__manifest__.py`**

```python
# Add to your data files list:
'data': [
    # ... your existing files ...
    'security/monitoring_security.xml',
    'security/monitoring_access.csv', 
    'views/monitoring_views.xml',
    'data/monitoring_crons.xml',
],

# Add external dependencies for notifications:
'external_dependencies': {
    'python': [
        'requests',  # For webhook notifications
        # ... your existing dependencies ...
    ],
},
```

---

## 🛠️ **MONITORING FEATURES**

### **1. Automatic Error Logging** ✨

- **Zero Impact**: Uses background threads, won't slow down your module
- **Smart Deduplication**: Prevents spam from repeated errors
- **Rich Context**: Captures user, session, model, method details

### **2. Real-Time Notifications** 📱

- **Webhooks**: Send alerts to Slack, Discord, Teams, or custom endpoints
- **Email Alerts**: Critical errors trigger immediate email notifications
- **SMS Integration**: Can integrate with Odoo's SMS system

### **3. Performance Tracking** ⚡

- **Method Timing**: Track slow operations automatically
- **Memory Usage**: Monitor resource consumption
- **Health Checks**: Automated system health verification every 15 minutes

### **4. Live API Endpoints** 🌐

#### **Public Health Check** (No Auth Required)

```bash
curl https://your-odoo.com/records_management/monitor/health
```

#### **Recent Errors** (User Auth)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-odoo.com/records_management/monitor/errors?limit=10&severity=high
```

#### **Performance Data** (User Auth)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-odoo.com/records_management/monitor/performance?hours=24
```

#### **Real-Time Stream** (User Auth)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-odoo.com/records_management/monitor/stream
```

---

## 🔧 **EASY INTEGRATION**

### **Option 1: Decorator Method** (Recommended)

```python
# Add to any model method for automatic monitoring
from .monitoring.live_monitor import RecordsManagementMonitoringHelper

class YourModel(models.Model):
    _name = 'your.model'
    
    @RecordsManagementMonitoringHelper.monitor_method
    def your_critical_method(self):
        # Your existing code
        # Automatic error logging and performance tracking!
        pass
```

### **Option 2: Manual Logging**

```python
# Manual error logging
try:
    # Your risky operation
    result = some_complex_operation()
except Exception as e:
    self.env['records.management.monitor'].log_error(
        error_msg=str(e),
        traceback_str=traceback.format_exc(),
        severity='high',
        model=self._name,
        method='your_method_name'
    )
    raise

# Log user actions
RecordsManagementMonitoringHelper.log_user_action(
    self.env, 
    'Document Destruction Completed',
    context={'doc_count': 150, 'weight': 25.5}
)
```

---

## 📊 **MONITORING DASHBOARD**

Access via Odoo menu: **Records Management → Monitoring → Monitoring Logs**

### **Features:**

- 🔍 **Real-time error list** with severity filtering
- 📈 **Performance analytics** and trend analysis  
- 🏥 **Health status** with automated checks
- 🔔 **Notification status** tracking
- 📋 **User action logs** for audit trails

---

## 🔔 **NOTIFICATION SETUP**

### **Webhook Configuration**

```python
# Set webhook URL in Odoo settings
# Go to: Settings → Technical → Parameters → System Parameters
# Key: records_management.monitoring_webhook_url
# Value: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Or your custom endpoint:
# Value: https://your-monitoring-service.com/api/alerts
```

### **Email Notifications**

```python
# Set notification email
# Key: records_management.monitoring_email  
# Value: admin@yourcompany.com
```

### **Webhook Payload Example**

```json
{
    "timestamp": "2025-07-27T14:30:00Z",
    "severity": "critical",
    "type": "error", 
    "message": "Database connection failed",
    "model": "records.box",
    "method": "create_box",
    "user": "John Doe",
    "company": "Your Company",
    "traceback": "...",
    "occurrence_count": 3
}
```

---

## 🚨 **EXTERNAL MONITORING INTEGRATION**

### **Send Alerts TO Your Module**

```bash
# External systems can send alerts to your Odoo
curl -X POST https://your-odoo.com/records_management/monitor/webhook/receive \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Server CPU high", 
       "severity": "warning",
       "type": "performance",
       "source": "nagios"
     }'
```

### **Monitor Multiple Odoo Instances**

```python
# Python script to monitor multiple Odoo instances
import requests
import time

odoo_instances = [
    'https://production.odoo.com',
    'https://staging.odoo.com', 
    'https://development.odoo.com'
]

for instance in odoo_instances:
    try:
        response = requests.get(f"{instance}/records_management/monitor/health", timeout=5)
        health = response.json()
        print(f"{instance}: {health['status']}")
        
        if health['status'] != 'healthy':
            # Send alert to your monitoring system
            send_alert_to_monitoring_system(instance, health)
            
    except Exception as e:
        print(f"{instance}: ERROR - {e}")
```

---

## 📈 **PERFORMANCE BENEFITS**

### **Zero Impact Design**

- ✅ **Background Processing**: All logging happens in separate threads
- ✅ **Non-Blocking**: Main operations never wait for monitoring
- ✅ **Fail-Safe**: Monitoring errors don't affect your module
- ✅ **Lightweight**: Minimal memory and CPU overhead

### **Smart Features**

- 🧠 **Deduplication**: Prevents log spam from repeated errors
- 🕰️ **Time Windows**: Groups similar errors within time periods
- 🧹 **Auto-Cleanup**: Removes old logs automatically
- 📊 **Aggregation**: Provides statistics and trends

---

## 🔒 **SECURITY & PRIVACY**

### **Access Control**

- 👥 **User Roles**: Monitoring user vs monitoring manager
- 🔐 **Authentication**: API endpoints require proper auth
- 🌐 **CORS Support**: Configurable cross-origin access
- 🛡️ **Data Filtering**: Sensitive data automatically filtered

### **Data Protection**

- 🔒 **No Passwords**: Never logs authentication data
- 📋 **Context Filtering**: Removes sensitive information
- 🕰️ **Retention Policies**: Auto-delete old monitoring data
- 🔐 **Encrypted Transport**: HTTPS for all communications

---

## 🎛️ **CONFIGURATION OPTIONS**

### **System Parameters** (Settings → Technical → Parameters)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `records_management.monitoring_webhook_url` | Webhook for alerts | Empty |
| `records_management.monitoring_email` | Email for critical alerts | Empty |
| `records_management.monitoring_retention_days` | Days to keep logs | 30 |
| `records_management.monitoring_performance_threshold` | Seconds to log performance | 2.0 |
| `records_management.monitoring_health_check_interval` | Minutes between health checks | 15 |

---

## 🚀 **QUICK START CHECKLIST**

- [ ] **1. Add monitoring files** to your module
- [ ] **2. Update `__init__.py`** and `__manifest__.py`**
- [ ] **3. Install/update** your module
- [ ] **4. Configure webhook URL** (optional)
- [ ] **5. Configure notification email** (optional)
- [ ] **6. Test health endpoint**: `/records_management/monitor/health`
- [ ] **7. Add monitoring decorators** to critical methods
- [ ] **8. Check monitoring dashboard** in Odoo menu

---

## 🎊 **RESULT: LIVE ERROR MONITORING**

✅ **Automatic error detection** with zero impact on performance  
✅ **Real-time notifications** via webhook/email/SMS  
✅ **Performance monitoring** and health checks  
✅ **REST API** for external integration  
✅ **Web dashboard** for analysis and resolution  
✅ **Secure and privacy-focused** design  

**Your Records Management module now has enterprise-grade monitoring without affecting loading or performance!** 🚀
