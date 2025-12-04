# -*- coding: utf-8 -*-
"""
Import controller files to register HTTP routes.

- portal: Main portal controller (consolidated routes for all portal functionality)
- portal_interactive: portal export/import functionality
- advanced_search: advanced inventory search
- http_controller: HTTP endpoints
- field_label_portal: field label customization portal controllers
- intelligent_search: intelligent search and auto-suggestion controllers
- work_order_portal: work order portal controllers
- pos_customer_history: POS customer history JSON endpoint
- portal_barcode: portal barcode generation JSON endpoint
- portal_document_bulk_upload: portal document bulk upload
- portal_access: portal account access for admin users
- portal_calendar: portal service calendar (shredding, pickups, retrievals)
- destruction_portal: destruction & shredding dashboard

NOTE: main.py has been disabled (renamed to main.py.disabled) - all routes
consolidated into portal.py for maintainability.
"""

from . import portal  # Main portal controller (primary)
from . import portal_interactive  # portal export/import functionality
from . import advanced_search  # advanced inventory search
from . import http_controller  # HTTP endpoints
# from . import main  # DISABLED - consolidated into portal.py
from . import field_label_portal  # field label customization portal
from . import intelligent_search  # search controllers
from . import work_order_portal  # work order portal controllers
from . import pos_customer_history  # POS customer history JSON endpoint
from . import portal_barcode  # portal barcode generation JSON endpoint
from . import portal_document_bulk_upload  # portal document bulk upload
from . import portal_access  # portal account access for admin users
from . import portal_calendar  # portal service calendar (shredding, pickups, retrievals)
from . import destruction_portal  # destruction & shredding dashboard
from . import portal_features  # mobile, e-learning, compliance features
