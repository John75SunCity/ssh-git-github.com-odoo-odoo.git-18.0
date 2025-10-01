from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
from datetime import datetime
import re


class RecordsDocumentBulkUploadWizard(models.TransientModel):
    _name = 'records.document.bulk.upload.wizard'
    _description = 'Bulk Document/File Upload Wizard'

    upload_file = fields.Binary(string='Upload File (XLSX/CSV)', required=True, help='Spreadsheet containing rows of files/documents to index.')
    filename = fields.Char(string='Filename')
    container_id = fields.Many2one('records.container', string='Default Container', help='Optional container applied when a row omits container reference.')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, help='Customer owning the uploaded documents.')
    has_header = fields.Boolean(string='First Row is Header', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('parsed', 'Parsed'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='draft', string='Status', readonly=True)
    line_ids = fields.One2many('records.document.bulk.upload.line', 'wizard_id', string='Parsed Lines')
    error_log = fields.Text(string='Error Log')

    def action_download_template(self):  # Placeholder – will generate simple CSV for now
        """Return a minimal CSV template as an ir.actions.act_url (future: XLSX)."""
        header = 'name,description,container,temp_barcode,document_type,received_date\n'
        content = header + 'Example File,"Optional description",CONTAINER-REF,,GENERAL,2025-10-01\n'
        b64 = base64.b64encode(content.encode())
        return {
            'type': 'ir.actions.act_url',
            'url': 'data:text/csv;base64,%s' % b64.decode(),
            'target': 'self',
        }

    def action_parse(self):
        self.ensure_one()
        if not self.upload_file:
            raise UserError(_('Please upload a file to parse.'))
        # Basic CSV parse fallback (XLSX parsing can be added with openpyxl if dependency allowed)
        try:
            data = base64.b64decode(self.upload_file)
            text = data.decode(errors='ignore')
        except Exception as e:
            raise UserError(_('Failed to decode file: %s') % e)
        lines = text.splitlines()
        if self.has_header and lines:
            lines = lines[1:]
        parsed = []
        errors = []
        seq = 0
        # Preload valid document type codes (active types)
        type_codes = {t.code.strip().upper(): t.id for t in self.env['records.document.type'].search([]) if t.code}
        date_patterns = [
            '%Y-%m-%d',  # ISO
            '%m/%d/%Y',  # US
            '%d/%m/%Y',  # EU
        ]
        def normalize_date(val):
            if not val:
                return ''
            v = val.strip()
            for pat in date_patterns:
                try:
                    dt = datetime.strptime(v, pat)
                    return dt.strftime('%Y-%m-%d')
                except Exception:
                    continue
            return ''  # invalid -> blank so create() default can apply or user can correct
        tf_pattern = re.compile(r'^TF\d{7}$')
        for raw in lines:
            seq += 1
            if not raw.strip():
                continue
            cols = [c.strip() for c in raw.split(',')]
            while len(cols) < 6:
                cols.append('')
            name, description, container_ref, temp_barcode, doc_type_code, received_date = cols[:6]
            # Validate temp barcode format if provided; else blank -> auto assign later
            if temp_barcode and not tf_pattern.match(temp_barcode):
                errors.append(_('Line %s: Invalid temp barcode format %s (expected TF#######)') % (seq, temp_barcode))
                temp_barcode = ''
            normalized_date = normalize_date(received_date)
            if received_date and not normalized_date:
                errors.append(_('Line %s: Invalid date %s (expected YYYY-MM-DD or MM/DD/YYYY or DD/MM/YYYY)') % (seq, received_date))
            received_date = normalized_date
            original_type_code = doc_type_code
            doc_type_id = False
            if doc_type_code:
                key = doc_type_code.strip().upper()
                if key in type_codes:
                    doc_type_id = type_codes[key]
                else:
                    errors.append(_('Line %s: Unknown document type code %s') % (seq, original_type_code))
                    doc_type_code = ''
            parsed.append({
                'sequence': seq,
                'name': name or _('Unnamed %s') % seq,
                'description': description,
                'container_ref': container_ref,
                'temp_barcode': temp_barcode,
                'doc_type_code': doc_type_code,
                'doc_type_id': doc_type_id,
                'received_date': received_date,
            })
        # Reset old lines
        self.line_ids.unlink()
        line_vals = []
        for item in parsed:
            line_vals.append((0, 0, {
                'sequence': item['sequence'],
                'name': item['name'],
                'raw_description': item['description'],
                'raw_container_ref': item['container_ref'],
                'raw_temp_barcode': item['temp_barcode'],
                'raw_doc_type_code': item['doc_type_code'],
                'doc_type_id': item['doc_type_id'] or False,
                'raw_received_date': item['received_date'],
            }))
        new_state = 'parsed'
        if errors:
            new_state = 'error'
        self.write({'line_ids': line_vals, 'state': new_state, 'error_log': '\n'.join(errors) if errors else False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def action_commit(self):
        self.ensure_one()
        if self.state not in ('parsed',):
            raise UserError(_('Parse lines and resolve errors before committing (current state: %s).') % self.state)
        Document = self.env['records.document']
        created = 0
        for line in self.line_ids:
            vals = {
                'name': line.name,
                'description': line.raw_description,
                'partner_id': self.partner_id.id,
            }
            # Container resolution placeholder (by exact name match)
            if line.raw_container_ref:
                container = self.env['records.container'].search([('name', '=', line.raw_container_ref)], limit=1)
                if container:
                    vals['container_id'] = container.id
                elif self.container_id:
                    vals['container_id'] = self.container_id.id
            elif self.container_id:
                vals['container_id'] = self.container_id.id
            # Provided temp barcode (optional) – uniqueness handled by constraint
            if line.raw_temp_barcode:
                vals['temp_barcode'] = line.raw_temp_barcode
            if line.raw_received_date:
                vals['received_date'] = line.raw_received_date
            if line.doc_type_id:
                vals['doc_type_id'] = line.doc_type_id.id
            try:
                Document.create([vals])
                created += 1
            except Exception as e:
                # Append to error log; continue processing
                existing = self.error_log or ''
                self.error_log = (existing + ('\n' if existing else '') + _('Line %s failed: %s') % (line.sequence, e))
        self.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'default_error_log': self.error_log},
        }


class RecordsDocumentBulkUploadLine(models.TransientModel):
    _name = 'records.document.bulk.upload.line'
    _description = 'Bulk Document Upload Line'
    _order = 'sequence'

    wizard_id = fields.Many2one('records.document.bulk.upload.wizard', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Seq')
    name = fields.Char(string='Proposed Name')
    raw_description = fields.Char(string='Raw Description')
    raw_container_ref = fields.Char(string='Raw Container Ref')
    raw_temp_barcode = fields.Char(string='Raw Temp Barcode')
    raw_doc_type_code = fields.Char(string='Raw Document Type Code')
    raw_received_date = fields.Char(string='Raw Received Date')
    doc_type_id = fields.Many2one('records.document.type', string='Document Type', help='Resolved document type from provided code during parsing.')
