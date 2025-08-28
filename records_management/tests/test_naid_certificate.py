"""
Test cases for the naid.certificate model in the records management module.

NAID Certificate model handles destruction certificates for NAID AAA compliance.
Tests cover certificate lifecycle, PDF generation, state management, and constraints.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import base64

class TestNaidCertificate(TransactionCase):
    """Test cases for naid.certificate model"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()

        # Common test data setup
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test partner for certificates
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer for NAID Certificate',
            'email': 'naid.test@customer.example',
            'phone': '+1-555-NAID',
            'is_company': True,
        })

        # Create test technician user
        cls.technician_user = cls.env['res.users'].create({
            'name': 'Test NAID Technician',
            'login': 'naid.tech@company.test',
            'email': 'naid.tech@company.test',
        })

        # Create test FSM task for integration
        cls.fsm_task = cls.env['project.task'].create({
            'name': 'Test Destruction Task',
            'partner_id': cls.partner.id,
            'user_ids': [(6, 0, [cls.technician_user.id])],
            'date_end': datetime.now() + timedelta(hours=2),
        })

        # Create test certificate item
        cls.certificate_item = cls.env['naid.certificate.item'].create({
            'name': 'Test Destroyed Documents',
            'quantity': 100.0,
            'weight': 25.5,
            'material_type': 'Paper',
        })

        cls.company = cls.env.ref('base.main_company')

    def setUp(self):
        """Set up test data for each test method"""
        super().setUp()

        # Create test instance with minimal required fields
        self.test_record = self._create_test_record()

    def _create_test_record(self, **kwargs):
        """Helper method to create NAID certificate test records with default values"""
        default_values = {
            'partner_id': self.partner.id,
            'destruction_date': datetime.now(),
        }
        default_values.update(kwargs)

        return self.env['naid.certificate'].create(default_values)

    # ========================================================================
    # CORE CRUD TESTS
    # ========================================================================

    def test_create_naid_certificate(self):
        """Test basic NAID certificate creation"""
        record = self._create_test_record()
        self.assertTrue(record.exists())
        self.assertEqual(record._name, 'naid.certificate')
        # Certificate number should be auto-generated (not 'New')
        self.assertNotEqual(record.certificate_number, 'New')
        self.assertEqual(record.state, 'draft')
        self.assertEqual(record.partner_id, self.partner)

    def test_certificate_number_auto_generation(self):
        """Test certificate number auto-generation on create"""
        # Mock sequence to return specific value
        with patch.object(self.env['ir.sequence'], 'next_by_code', return_value='CERT-TEST-001'):
            record = self._create_test_record()
            self.assertEqual(record.certificate_number, 'CERT-TEST-001')

    def test_name_field_related_to_certificate_number(self):
        """Test name field is properly related to certificate_number"""
        with patch.object(self.env['ir.sequence'], 'next_by_code', return_value='CERT-REL-001'):
            record = self._create_test_record()
            self.assertEqual(record.name, record.certificate_number)
            self.assertEqual(record.name, 'CERT-REL-001')

    def test_fsm_task_integration(self):
        """Test FSM task integration and onchange behavior"""
        record = self._create_test_record(fsm_task_id=self.fsm_task.id)
        record._onchange_fsm_task_id()
        self.assertEqual(record.partner_id, self.fsm_task.partner_id)
        self.assertEqual(record.res_model, 'project.task')
        self.assertEqual(record.res_id, self.fsm_task.id)

    def test_technician_compute_from_fsm_task(self):
        """Test technician computation from FSM task"""
        record = self._create_test_record(fsm_task_id=self.fsm_task.id)
        record._compute_technician_user_id()
        self.assertEqual(record.technician_user_id, self.technician_user)

    # ========================================================================
    # STATE MANAGEMENT TESTS
    # ========================================================================

    def test_action_issue_certificate_success(self):
        """Test successful certificate issuing"""
        record = self._create_test_record()
        # Add destruction items to make certificate valid
        record.destruction_item_ids = [(0, 0, {
            'name': 'Test Items',
            'quantity': 50.0,
            'weight': 10.0,
        })]

        # Mock PDF generation
        with patch.object(record, '_generate_certificate_pdf', return_value=b'test_pdf_content'):
            record.action_issue_certificate()

        self.assertEqual(record.state, 'issued')
        self.assertIsNotNone(record.issue_date)
        self.assertTrue(record.certificate_data)
        self.assertTrue(record.certificate_filename.startswith('CoD-'))

    def test_action_issue_certificate_validation_no_items(self):
        """Test certificate issuing fails without destruction items"""
        record = self._create_test_record()

        with self.assertRaises(UserError) as cm:
            record.action_issue_certificate()

        self.assertIn('no destroyed items', str(cm.exception))

    def test_action_issue_certificate_validation_wrong_state(self):
        """Test certificate issuing fails if not in draft state"""
        record = self._create_test_record()
        record.state = 'sent'

        with self.assertRaises(UserError) as cm:
            record.action_issue_certificate()

        self.assertIn('Only draft certificates', str(cm.exception))

    def test_action_send_by_email(self):
        """Test sending certificate by email"""
        record = self._create_test_record()
        record.state = 'issued'

        # Mock email template
        template_mock = MagicMock()
        with patch.object(self.env, 'ref', return_value=template_mock):
            record.action_send_by_email()

        self.assertEqual(record.state, 'sent')
        template_mock.send_mail.assert_called_once_with(record.id, force_send=True)

    def test_action_send_by_email_wrong_state(self):
        """Test sending certificate fails if not issued"""
        record = self._create_test_record()
        record.state = 'draft'

        with self.assertRaises(UserError) as cm:
            record.action_send_by_email()

        self.assertIn('Only issued certificates', str(cm.exception))

    def test_action_cancel_certificate(self):
        """Test canceling certificate"""
        record = self._create_test_record()
        record.action_cancel()
        self.assertEqual(record.state, 'cancelled')

    def test_action_reset_to_draft(self):
        """Test resetting certificate to draft"""
        record = self._create_test_record()
        record.write({
            'state': 'issued',
            'issue_date': datetime.now(),
            'certificate_data': b'test_data',
            'certificate_filename': 'test.pdf',
        })

        record.action_reset_to_draft()

        self.assertEqual(record.state, 'draft')
        self.assertFalse(record.issue_date)
        self.assertFalse(record.certificate_data)
        self.assertFalse(record.certificate_filename)

    # ========================================================================
    # COMPUTE METHODS TESTS
    # ========================================================================

    def test_compute_totals_with_items(self):
        """Test total weight and items computation"""
        record = self._create_test_record()

        # Add destruction items
        record.destruction_item_ids = [
            (0, 0, {'name': 'Item 1', 'quantity': 10, 'weight': 5.0}),
            (0, 0, {'name': 'Item 2', 'quantity': 20, 'weight': 7.5}),
        ]

        record._compute_totals()

        self.assertEqual(record.total_weight, 12.5)  # 5.0 + 7.5
        self.assertEqual(record.total_items, 30)     # 10 + 20

    def test_compute_totals_with_containers(self):
        """Test total computation includes containers and boxes"""
        record = self._create_test_record()

        # Create test containers
        container1 = self.env['records.container'].create({
            'name': 'Test Container 1',
            'partner_id': self.partner.id,
        })
        container2 = self.env['records.container'].create({
            'name': 'Test Container 2',
            'partner_id': self.partner.id,
        })

        record.container_ids = [(6, 0, [container1.id, container2.id])]
        record._compute_totals()

        # Should count containers in total items
        self.assertEqual(record.total_items, 2)

    def test_compute_totals_null_safety(self):
        """Test compute totals handles null values safely"""
        record = self._create_test_record()

        # Add item with null weight
        record.destruction_item_ids = [
            (0, 0, {'name': 'Item with null weight', 'quantity': 5, 'weight': False}),
        ]

        record._compute_totals()

        # Should handle null weight gracefully
        self.assertEqual(record.total_weight, 0.0)
        self.assertEqual(record.total_items, 5)

    # ========================================================================
    # BUSINESS LOGIC TESTS
    # ========================================================================

    def test_generate_certificate_pdf(self):
        """Test PDF generation logic"""
        record = self._create_test_record()

        # Mock report generation
        report_mock = MagicMock()
        report_mock._render_qweb_pdf.return_value = (b'pdf_content', 'pdf')

        with patch.object(self.env, 'ref', return_value=report_mock):
            result = record._generate_certificate_pdf()

        # Should return base64 encoded content
        self.assertEqual(result, base64.b64encode(b'pdf_content'))
        report_mock._render_qweb_pdf.assert_called_once_with(record.ids)

    def test_witness_information_fields(self):
        """Test witness information storage"""
        record = self._create_test_record()

        witness_name = "John Witness"
        witness_signature = b"signature_data"

        record.write({
            'witness_name': witness_name,
            'witness_signature': witness_signature,
        })

        self.assertEqual(record.witness_name, witness_name)
        self.assertEqual(record.witness_signature, witness_signature)

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_shredding_service_integration(self):
        """Test integration with shredding service"""
        # Create shredding service
        shredding_service = self.env['shredding.service'].create({
            'name': 'Test Shredding Service',
            'partner_id': self.partner.id,
            'service_date': date.today(),
        })

        record = self._create_test_record(shredding_service_id=shredding_service.id)

        self.assertEqual(record.shredding_service_id, shredding_service)

    def test_many2many_relationships(self):
        """Test Many2many relationships with containers and boxes"""
        record = self._create_test_record()

        # Create test containers
        container = self.env['records.container'].create({
            'name': 'Test Destruction Container',
            'partner_id': self.partner.id,
        })

        box = self.env['records.container'].create({
            'name': 'Test Destruction Box',
            'partner_id': self.partner.id,
        })

        # Test adding containers and boxes
        record.container_ids = [(6, 0, [container.id])]
        record.box_ids = [(6, 0, [box.id])]

        self.assertIn(container, record.container_ids)
        self.assertIn(box, record.box_ids)

    # ========================================================================
    # FIELD VALIDATION TESTS
    # ========================================================================

    def test_required_fields_validation(self):
        """Test required field validation"""
        with self.assertRaises(ValidationError):
            self.env['naid.certificate'].create({
                # Missing required partner_id and destruction_date
            })

    def test_readonly_fields_enforcement(self):
        """Test readonly field enforcement"""
        record = self._create_test_record()

        # These fields should be readonly after creation
        initial_company = record.company_id
        record.write({'company_id': self.env.ref('base.main_company').id})

        # Company should remain unchanged due to readonly
        self.assertEqual(record.company_id, initial_company)

    def test_copy_false_fields(self):
        """Test copy=False field behavior"""
        record = self._create_test_record()

        copied_record = record.copy()

        # Certificate number should not be copied
        self.assertNotEqual(copied_record.certificate_number, record.certificate_number)

    # ========================================================================
    # CONSTRAINT TESTS
    # ========================================================================

    def test_future_destruction_date_constraint(self):
        """Test constraint preventing future destruction dates"""
        future_date = datetime.now() + timedelta(days=30)

        with self.assertRaises(ValidationError):
            self._create_test_record(destruction_date=future_date)

    def test_duplicate_certificate_number_constraint(self):
        """Test constraint preventing duplicate certificate numbers"""
        # Create first certificate
        record1 = self._create_test_record()
        cert_num = record1.certificate_number

        # Try to create second with same number
        with self.assertRaises(ValidationError):
            self.env['naid.certificate'].create({
                'partner_id': self.partner.id,
                'destruction_date': datetime.now(),
                'certificate_number': cert_num,
            })

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_access_rights(self):
        """Test model access rights"""
        # Test basic model access
        self.assertTrue(self.env['naid.certificate'].check_access_rights('read'))
        self.assertTrue(self.env['naid.certificate'].check_access_rights('create'))

    def test_record_rules(self):
        """Test record-level security rules"""
        record = self._create_test_record()

        # User should be able to access their own company's certificates
        self.assertTrue(record.exists())

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_bulk_certificate_creation(self):
        """Test performance with bulk certificate operations"""
        vals_list = []
        for i in range(10):
            vals_list.append({
                'partner_id': self.partner.id,
                'destruction_date': datetime.now() + timedelta(hours=i),
            })

        # Test bulk create
        certificates = self.env['naid.certificate'].create(vals_list)
        self.assertEqual(len(certificates), 10)

        # All should have unique certificate numbers
        cert_numbers = certificates.mapped('certificate_number')
        self.assertEqual(len(cert_numbers), len(set(cert_numbers)))

    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================

    def test_missing_email_template_error(self):
        """Test error handling when email template is missing"""
        record = self._create_test_record()
        record.state = 'issued'

        # Mock missing template
        with patch.object(self.env, 'ref', side_effect=ValueError('Template not found')):
            with self.assertRaises(UserError) as cm:
                record.action_send_by_email()

            self.assertIn('email template', str(cm.exception))

    def test_pdf_generation_error_handling(self):
        """Test error handling in PDF generation"""
        record = self._create_test_record()

        # Mock report generation failure
        with patch.object(self.env, 'ref', side_effect=Exception('Report error')):
            with self.assertRaises(Exception):
                record._generate_certificate_pdf()
