from . import models
from . import controllers
from . import wizards
from . import report
from . import post_init_hooks
# Expose hook at module root for Odoo manifest lookup
from .post_init_hooks import post_init_hook
