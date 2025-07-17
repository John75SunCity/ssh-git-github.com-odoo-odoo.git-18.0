# -*- coding: utf-8 -*-
# Import controller files to register HTTP routes
from . import portal  # Handles portal-specific routes, e.g., certificate downloads for NAID auditing
from . import http_controller  # General HTTP controllers for custom endpoints
from . import main  # Main controllers for core functionality like inventory and requests
