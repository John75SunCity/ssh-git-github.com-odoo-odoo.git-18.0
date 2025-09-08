# -*- coding: utf-8 -*-
"""
Import controller files to register HTTP routes.

- portal: portal-specific routes (e.g., certificate downloads for NAID auditing)
from . import http_controller  # Handles general HTTP controllers for custom endpoints.
- main: main controllers for core functionality (inventory, requests)
- field_label_portal: field label customization portal controllers
- intelligent_search: intelligent search and auto-suggestion controllers
"""

from . import portal  # portal routes
from . import http_controller  # HTTP endpoints
from . import main  # core controllers
from . import field_label_portal  # field label customization portal
from . import intelligent_search  # search controllers
from . import work_order_portal  # work order portal controllers
from . import pos_customer_history  # POS customer history JSON endpoint
