from odoo.tests import HttpCase, tagged
from odoo import api
import base64


@tagged('-at_install', 'post_install')
class TestPortalBulkUploadFlow(HttpCase):
    def setUp(self):
        super().setUp()
        # Create a portal user linked to partner
        self.partner = self.env['res.partner'].create({'name': 'Portal Customer'})
        self.portal_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Portal User',
            'login': 'portal_user_bulk@example.com',
            'email': 'portal_user_bulk@example.com',
            'partner_id': self.partner.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        # Ensure at least one doc type
        self.doc_type = self.env['records.document.type'].create({'name': 'General', 'code': 'GENERAL'})

    def test_portal_bulk_upload_parse_commit(self):
        # Login as portal user
        self.start_tour('/', 'portal', login='portal_user_bulk@example.com')  # basic login simulation
        csv_content = 'name,description,container,temp_barcode,document_type,received_date\n' \
                      'Portal File,Notes,, ,GENERAL,2025-10-01\n'
        b64 = base64.b64encode(csv_content.encode()).decode()
        Wizard = self.env['records.document.bulk.upload.wizard']
        # Simulate portal parse (controller does post with file -> we mimic server side)
        wizard = Wizard.create({
            'partner_id': self.partner.id,
            'upload_file': b64,
            'filename': 'portal_upload.csv',
            'has_header': True,
        })
        wizard.action_parse()
        self.assertIn(wizard.state, ('parsed', 'error'))
        self.assertFalse(wizard.error_log, 'Unexpected parse errors: %s' % wizard.error_log)
        self.assertEqual(len(wizard.line_ids), 1)
        line = wizard.line_ids[0]
        self.assertTrue(line.doc_type_id, 'Doc type should be resolved for GENERAL code')
        # Commit
        wizard.action_commit()
        self.assertEqual(wizard.state, 'done')
        doc = self.env['records.document'].search([('partner_id', '=', self.partner.id), ('name', '=', 'Portal File')], limit=1)
        self.assertTrue(doc, 'Document should be created')
        self.assertTrue(doc.temp_barcode.startswith('TF'), 'Temp barcode should be auto generated with TF prefix')
        self.assertEqual(doc.doc_type_id, self.doc_type, 'Doc type should have been assigned to created document')
