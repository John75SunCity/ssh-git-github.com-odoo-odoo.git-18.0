from odoo.tests.common import TransactionCase
from datetime import datetime, date
from unittest.mock import patch, MagicMock
from odoo.exceptions import AccessError
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class TestAdvancedBillingContact(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a partner and billing profile for testing
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.company = self.env.user.company_id
        self.billing_profile = self.env['advanced.billing.profile'].create({
            'name': 'Test Billing Profile',
            'partner_id': self.partner.id,
            'company_id': self.company.id,
        })

    def test_create_contact_defaults(self):
        contact = self.env['advanced.billing.contact'].create({
            'name': 'Billing Contact 1',
            'email': 'billing1@example.com',
            'billing_profile_id': self.billing_profile.id,
        })
        self.assertTrue(contact.active)
        self.assertEqual(contact.contact_type, 'billing')
        self.assertTrue(contact.receive_storage_invoices)
        self.assertTrue(contact.receive_service_invoices)
        self.assertTrue(contact.receive_statements)
        self.assertTrue(contact.receive_reminders)
        self.assertEqual(contact.billing_profile_id, self.billing_profile)
        self.assertEqual(contact.partner_id, self.partner)
    def test_search_advanced_billing_contact_records(self):
        """Test searching advanced_billing_contact records"""
        # GitHub Copilot Pattern: Search and read operations
        record = self.env['advanced_billing_contact'].create({
            'name': 'Searchable Record'
        })
        
        found_records = self.env['advanced_billing_contact'].search([
            ('name', '=', 'Searchable Record')
        ])
        
        self.assertIn(record, found_records)
    def test_search_advanced_billing_contact_records(self):
        """Test searching advanced_billing_contact records"""
        # GitHub Copilot Pattern: Search and read operations
        record = self.env['advanced_billing_contact'].create({
            'name': 'Searchable Record'
        })

        found_records = self.env['advanced_billing_contact'].search([
            ('name', '=', 'Searchable Record')
        ])

        self.assertIn(record, found_records)




    def test_update_advanced_billing_contact_fields(self):
        """Test updating advanced_billing_contact record fields"""
        # GitHub Copilot Pattern: Update operations
        record = self.env['advanced_billing_contact'].create({
            'name': 'Original Name'
        })
        
        record.write({'name': 'Updated Name'})
        
        self.assertEqual(record.name, 'Updated Name')


    def test_delete_advanced_billing_contact_record(self):
        """Test deleting advanced_billing_contact record"""
        # GitHub Copilot Pattern: Delete operations
        record = self.env['advanced_billing_contact'].create({
            'name': 'To Be Deleted'
        })
        
        record_id = record.id
        record.unlink()
        
        self.assertFalse(self.env['advanced_billing_contact'].browse(record_id).exists())


    def test_validation_advanced_billing_contact_constraints(self):
        """Test validation constraints for advanced_billing_contact"""
        # GitHub Copilot Pattern: Validation testing with assertRaises
        with self.assertRaises(ValidationError):
            self.env['advanced_billing_contact'].create({
                # Add invalid data that should trigger validation
            })



    def test_primary_contact_auto_set(self):
        contact = self.env['advanced.billing.contact'].create({
            'name': 'Primary Contact',
            'email': 'primary@example.com',
            'billing_profile_id': self.billing_profile.id,
        })
        self.billing_profile.invalidate_cache()
        self.assertTrue(contact.primary_contact)
        self.assertEqual(self.billing_profile.primary_contact_id, contact)

    def test_only_one_primary_contact(self):
        c1 = self.env['advanced.billing.contact'].create({
            'name': 'Contact 1',
            'email': 'c1@example.com',
            'billing_profile_id': self.billing_profile.id,
        })
        c2 = self.env['advanced.billing.contact'].create({
            'name': 'Contact 2',
            'email': 'c2@example.com',
            'billing_profile_id': self.billing_profile.id,
        })
        # Set c2 as primary, c1 should be unset
        c2.action_set_primary()
        c1.refresh()
        c2.refresh()
        self.assertTrue(c2.primary_contact)
        self.assertFalse(c1.primary_contact)
        self.assertEqual(self.billing_profile.primary_contact_id, c2)

    def test_action_contact_now_sets_last_contact_date(self):
        contact = self.env['advanced.billing.contact'].create({
            'name': 'Contact Now',
            'email': 'now@example.com',
            'billing_profile_id': self.billing_profile.id,
        })
        self.assertFalse(contact.last_contact_date)
        contact.action_contact_now()
        self.assertTrue(contact.last_contact_date)

    def test_preferred_communication_choices(self):
        contact = self.env['advanced.billing.contact'].create({
            'name': 'Comm Pref',
            'email': 'comm@example.com',
            'billing_profile_id': self.billing_profile.id,
            'preferred_communication': 'portal',
        })
        self.assertEqual(contact.preferred_communication, 'portal')