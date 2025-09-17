# -*- coding: utf-8 -*-
"""Tests for Records Retention Policy computed fields.

Covers:
    * review_state derivation
    * retention_display formatting
    * overdue_days calculation
    * is_latest_version logic

Assumptions:
    Basic environment with minimal dependencies loaded. Adapt domains as needed if
    custom security or required related models impose constraints.
"""
from odoo.tests.common import TransactionCase
from datetime import date, timedelta


class TestRetentionPolicyComputed(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Policy = self.env['records.retention.policy']

    def _create_policy(self, **vals):
        defaults = {
            'name': 'Test Policy',
            'retention_unit': 'years',
            'retention_period': 5,
        }
        defaults.update(vals)
        return self.Policy.create(defaults)

    def test_retention_display_years(self):
        policy = self._create_policy(retention_unit='years', retention_period=7)
        # Force compute
        _ = policy.retention_display
        self.assertIn('7', policy.retention_display)

    def test_retention_display_indefinite(self):
        policy = self._create_policy(retention_unit='indefinite', retention_period=0)
        _ = policy.retention_display
        self.assertEqual(policy.retention_display, 'Indefinite')

    def test_review_state_expired(self):
        policy = self._create_policy(expiration_date=date.today() - timedelta(days=1))
        policy._compute_review_state()
        self.assertEqual(policy.review_state, 'expired')

    def test_review_state_overdue(self):
        policy = self._create_policy(next_review_date=date.today() - timedelta(days=1))
        policy._compute_review_state()
        self.assertEqual(policy.review_state, 'overdue')

    def test_review_state_current(self):
        policy = self._create_policy()
        policy._compute_review_state()
        self.assertEqual(policy.review_state, 'current')

    def test_overdue_days_expiration(self):
        policy = self._create_policy(expiration_date=date.today() - timedelta(days=5))
        policy._compute_overdue_days()
        self.assertEqual(policy.overdue_days, 5)

    def test_overdue_days_review(self):
        policy = self._create_policy(next_review_date=date.today() - timedelta(days=3))
        policy._compute_overdue_days()
        self.assertEqual(policy.overdue_days, 3)

    def test_is_latest_version_no_versions(self):
        policy = self._create_policy(version=1)
        policy._compute_is_latest_version()
        self.assertTrue(policy.is_latest_version)

    def test_is_latest_version_with_versions(self):
        policy = self._create_policy(version=2)
        # Simulate version_ids relationship by creating related version records
        Version = self.env['records.retention.policy.version']
        Version.create({'policy_id': policy.id, 'version': '1'})
        Version.create({'policy_id': policy.id, 'version': '2'})
        policy._compute_is_latest_version()
        self.assertTrue(policy.is_latest_version)
