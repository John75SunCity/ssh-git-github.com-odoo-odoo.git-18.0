from odoo.tests.common import TransactionCase

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