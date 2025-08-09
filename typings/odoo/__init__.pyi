# Odoo stubs to prevent import errors in VS Code
from typing import Any

# Core Odoo modules
models: Any
fields: Any
api: Any
_: Any

# Odoo exceptions
class exceptions:
    class UserError(Exception): ...
    class ValidationError(Exception): ...
    class AccessError(Exception): ...
    class RedirectWarning(Exception): ...

# HTTP module
class http:
    request: Any
