# -*- coding: utf-8 -*-
"""Integration test invoking the basic JS tour.

Validates that the Records Management application root menu and Containers menu
load without JS crashes and that a list/kanban view is rendered.
"""
from odoo.tests.common import HttpCase, tagged


@tagged('-at_install', 'post_install')
class TestRecordsManagementBasicTour(HttpCase):
    """Runs the basic navigation tour.

    We mark it post_install to avoid slowing initial module installation.
    """

    def test_01_basic_navigation_tour(self):
        # Use admin for maximum menu access; could later parameterize with demo user.
        self.start_tour(
            "/web",
            'records_management_basic_tour',
            login='admin'
        )
