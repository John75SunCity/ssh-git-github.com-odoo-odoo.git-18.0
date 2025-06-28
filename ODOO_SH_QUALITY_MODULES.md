# Odoo.sh Quality Modules Installation Guide

## Required Quality Modules for Records Management

Based on the Odoo.sh build error, you need to install the following Quality modules in your Odoo.sh instance:

### Core Quality Modules

1. **quality** - Base Quality module
2. **quality_control** - Quality Control processes
3. **quality_control_iot** - IoT integration for Quality Control
4. **quality_mrp** - Manufacturing & Quality integration
5. **quality_iot** - IoT Quality monitoring

### Installation Steps in Odoo.sh

1. **Log into your Odoo.sh dashboard**
2. **Navigate to your project**
3. **Go to the Apps/Modules section**
4. **Install modules in this order:**

   ```text
   1. quality (Base Quality module)
   2. quality_control
   3. quality_mrp
   4. quality_iot
   5. quality_control_iot
   ```

### Alternative: Install via Dependencies

You can also add these as dependencies in your `records_management/__manifest__.py`:

```python
'depends': [
    'base',
    'stock',
    'quality',
    'quality_control',
    'quality_mrp',
    'quality_iot',
    'quality_control_iot',
],
```

**Note**: Only add these dependencies if your module actually uses Quality features. If not, just install them separately in Odoo.sh.

### Verification

After installation, check that these modules appear in your Odoo.sh Apps list and are marked as "Installed".

### Troubleshooting

If you see errors like:

- "At least one test failed when loading the modules (quality_iot)"
- "quality_control_iot module not found"

This means the Quality modules are not installed in your Odoo.sh instance. Follow the installation steps above.

### Current Error Context

The error you're seeing:

```text
At least one test failed when loading the modules (quality_iot)
```

This is specifically because the `quality_iot` module (and likely others) are not installed in your Odoo.sh instance, even though they may be referenced or expected by the system.
