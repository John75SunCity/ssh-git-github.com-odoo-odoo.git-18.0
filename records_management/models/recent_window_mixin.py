from datetime import date, timedelta

from odoo import models, api, _


class RMRecentWindowMixin(models.AbstractModel):
    """Reusable search helper for rolling time window filters.

    Design goals:
    - Avoid putting Python expressions (relativedelta, strftime) inside XML domain attributes.
    - Keep underlying authoritative date/datetime fields (no denormalized stored booleans unless needed elsewhere).
    - Provide consistent semantics across models: last 7 days, last 30 days, this week start, this month start, expiring soon.
    - Each inheriting model overrides `_rm_recent_reference_field_map()` to specify which logical keys map to real fields.
    
    Logical keys supported (may be subset per model):
        'create': creation date (`create_date`)
        'event': event date like custody or audit date
        'destruction': destruction or eligible destruction date
        'expiry': certification / retention expiry date
        'last_access': last access / activity date

    Search pseudo-fields patterns (boolean search-only, not real stored fields):
        is_recent_7d_<key>
        is_recent_30d_<key>
        expiring_30d_<key>   (date between today and today+30)

    We implement generic `_recency_search_builder` and generate search methods via `__getattr__` fallback for patterns.
    This keeps code minimal and extensible without declaring dozens of fields.
    """

    _name = 'rm.recent.window.mixin'
    _description = 'Recent Window Abstract Helper'

    # ------------------------------------------------------------------
    # Configuration hooks
    # ------------------------------------------------------------------
    def _rm_recent_reference_field_map(self):  # pragma: no cover - override in concrete models
        """Return dict logical_key -> actual field name.
        Example override:
            return {
                'create': 'create_date',
                'event': 'event_date',
                'destruction': 'destruction_eligible_date',
            }
        """
        return {'create': 'create_date'}

    # ------------------------------------------------------------------
    # Dynamic search attribute resolution
    # ------------------------------------------------------------------
    def __getattr__(self, name):
        """Dynamically provide _search_* methods for virtual recent fields.

        Patterns:
            _search_is_recent_7d_<key>
            _search_is_recent_30d_<key>
            _search_expiring_30d_<key>
        """
        if name.startswith('_search_'):
            try:
                prefix, logical = self._rm_parse_virtual_search_name(name)
            except ValueError:
                # In Odoo 18.0, we need to raise AttributeError directly
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

            def dynamic_search(op, value):
                return self._rm_build_dynamic_domain(prefix, logical, op, value)

            return dynamic_search
        
        # In Odoo 18.0, we need to raise AttributeError directly instead of calling super().__getattr__
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _rm_parse_virtual_search_name(name):
        # name like _search_is_recent_7d_create
        core = name.replace('_search_', '')
        if core.startswith('is_recent_7d_'):
            return ('recent_7d', core[len('is_recent_7d_'):])
        if core.startswith('is_recent_30d_'):
            return ('recent_30d', core[len('is_recent_30d_'):])
        if core.startswith('expiring_30d_'):
            return ('expiring_30d', core[len('expiring_30d_'):])
        raise ValueError('Not a recognized dynamic search field')

    # ------------------------------------------------------------------
    # Domain builders
    # ------------------------------------------------------------------
    def _rm_build_dynamic_domain(self, window_key, logical_key, operator, value):
        field_map = self._rm_recent_reference_field_map()
        if logical_key not in field_map:
            # Return neutral domain (no records) if misconfigured; safer than broad match
            return [('id', '=', 0)]
        real_field = field_map[logical_key]
        today = date.today()

        if operator not in ('=', '=='):
            # Only equality semantics supported; anything else returns neutral
            return [('id', '!=', 0)]

        if window_key == 'recent_7d':
            threshold = (today - timedelta(days=7)).isoformat()
            base = (real_field, '>=', threshold)
        elif window_key == 'recent_30d':
            threshold = (today - timedelta(days=30)).isoformat()
            base = (real_field, '>=', threshold)
        elif window_key == 'expiring_30d':
            # Between today and today + 30 days inclusive
            upper = (today + timedelta(days=30)).isoformat()
            base = ['&', (real_field, '>=', today.isoformat()), (real_field, '<=', upper)]
        else:
            return [('id', '!=', 0)]

        if isinstance(base, tuple):
            return [base] if value else ['!', base]
        # base is a compound list expression already
        return base if value else ['!', base]

    # Convenience for future extension points (e.g., adding month bounds)
    def _rm_month_range_domain(self, field_name):
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        # Simple next month start calculation
        if today.month == 12:
            next_month_start = date(today.year + 1, 1, 1).isoformat()
        else:
            next_month_start = date(today.year, today.month + 1, 1).isoformat()
        return ['&', (field_name, '>=', month_start), (field_name, '<', next_month_start)]
