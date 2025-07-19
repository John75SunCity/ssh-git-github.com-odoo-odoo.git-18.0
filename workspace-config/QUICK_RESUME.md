# Quick Session Recovery Guide

## For AI Assistant - COPY/PASTE THIS INTO NEW SESSION:

````markdown
# Quick Session Recovery Guide

## For AI Assistant - COPY/PASTE THIS INTO NEW SESSION:

```
I have an Odoo 18.0 Records Management module deployment issue.

We've systematically fixed 12 major issues:
✅ Duplicate models, field references, security domains, external IDs, CSV access, imports, model fields

Current Error: "Invalid field 'description' on model 'records.tag'"
Reality: Field DOES exist in records_tag.py but Odoo has cached old model definition

Root Cause: Need to UPGRADE module instead of INSTALL to refresh model cache
Status: Field added, version bumped to 18.0.2.10.0, all committed

Please review /workspaces/ssh-git-github.com-odoo-odoo.git-18.0/workspace-config/CURRENT_SESSION_STATUS.md for complete context.

Ready to try module UPGRADE instead of install.
```

## For Human - Quick Resume:
1. ☑️ Fixed 12 deployment issues systematically
2. ☑️ Added missing description field to records.tag model  
3. ☑️ Incremented module version for upgrade
4. ⏭️ Ready to UPGRADE module (not install)

**Next Action**: In Odoo Apps, find Records Management and click UPGRADE button.

````

## For Human - Quick Resume:
1. ☑️ All previous fixes are committed and deployed
2. ☑️ Systematic field audit completed  
3. ☑️ 4 major errors resolved
4. ⏭️ Ready for next error iteration

**Next Action**: Deploy and paste any new RPC_ERROR message.
