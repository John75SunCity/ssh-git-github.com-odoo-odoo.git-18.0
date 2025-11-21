# -*- coding: utf-8 -*-
"""
ZPL Label Generator Service for Records Management

Generates professional barcode and QR code labels using ZPL (Zebra Programming Language)
and Labelary's free rendering API. Supports industry-standard label sheets with precise
dimensions for containers, file folders, and QR codes.

Label Specifications:
- Container Labels: 4" x 1.33", 14 per sheet (Avery-compatible)
- File Folder Labels: 2.5935" x 1", 30 per sheet
- QR Code Labels: 1" x 1.25", 49 per sheet

Features:
- Native Odoo integration (no external dependencies except Labelary API)
- Font Awesome icon rendering (boxes for containers, folders for files)
- QR codes with portal login URLs
- PDF generation for batch printing
- Professional ZPL output compatible with Zebra printers
"""

import base64
import json
import logging
import requests
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ZPLLabelGenerator(models.AbstractModel):
    """
    Abstract model providing ZPL label generation services for Records Management.
    
    This service generates professional barcode labels using ZPL (Zebra Programming Language)
    and renders them to PDF using Labelary's free API (5,000 requests/day limit).
    
    Supported label types:
    - Container labels with barcode + box icon
    - File folder labels with barcode + folder icon
    - QR code labels with portal login URL
    
    Usage:
        generator = self.env['zpl.label.generator']
        pdf_data = generator.generate_container_label(container_record)
    """
    
    _name = 'zpl.label.generator'
    _description = 'ZPL Label Generator Service'
    
    # ============================================================================
    # LABEL SPECIFICATIONS (Industry Standard Sheets)
    # ============================================================================
    
    # Container Labels - 4" x 1.33" (14 per sheet)
    CONTAINER_LABEL_WIDTH = 4.0  # inches
    CONTAINER_LABEL_HEIGHT = 1.33  # inches
    CONTAINER_LABELS_PER_SHEET = 14
    CONTAINER_DPI = 203  # 8 dpmm (dots per millimeter) = ~203 DPI
    
    # File Folder Labels - 2.5935" x 1" (30 per sheet)
    FOLDER_LABEL_WIDTH = 2.5935  # inches
    FOLDER_LABEL_HEIGHT = 1.0  # inches
    FOLDER_LABELS_PER_SHEET = 30
    FOLDER_DPI = 203
    
    # QR Code Labels - 1" x 1.25" (49 per sheet)
    QR_LABEL_WIDTH = 1.0  # inches
    QR_LABEL_HEIGHT = 1.25  # inches
    QR_LABELS_PER_SHEET = 49
    QR_DPI = 203
    
    # Labelary API Configuration
    LABELARY_API_URL = 'http://api.labelary.com/v1/printers/{dpmm}/labels/{width}x{height}/0/'
    LABELARY_FREE_LIMIT = 5000  # requests per day
    
    # ============================================================================
    # MAIN LABEL GENERATION METHODS
    # ============================================================================
    
    def generate_container_label(self, container):
        """
        Generate a barcode label for a container with box icon.
        
        Args:
            container (records.container): Container record
            
        Returns:
            dict: {
                'pdf_data': base64-encoded PDF,
                'filename': suggested filename,
                'zpl': raw ZPL code (for debugging)
            }
        """
        # Get barcode (prefer physical, fallback to temp)
        barcode = container.barcode or container.temp_barcode
        if not barcode:
            raise UserError(_("Container %s has no barcode assigned.") % container.name)
        
        # Generate ZPL
        zpl = self._generate_container_zpl(
            barcode=barcode,
            container_name=container.name,
            customer_name=container.partner_id.name if container.partner_id else '',
            location=container.location_id.complete_name if container.location_id else ''
        )
        
        # Render to PDF
        pdf_data = self._render_zpl_to_pdf(
            zpl=zpl,
            width=self.CONTAINER_LABEL_WIDTH,
            height=self.CONTAINER_LABEL_HEIGHT,
            dpmm=8  # 203 DPI
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"container_label_{barcode}.pdf",
            'zpl': zpl
        }
    
    def generate_folder_label(self, folder):
        """
        Generate a barcode label for a file folder with folder icon.
        
        Args:
            folder (records.file): File folder record
            
        Returns:
            dict: {
                'pdf_data': base64-encoded PDF,
                'filename': suggested filename,
                'zpl': raw ZPL code
            }
        """
        barcode = folder.barcode or folder.temp_barcode
        if not barcode:
            raise UserError(_("File folder %s has no barcode assigned.") % folder.name)
        
        zpl = self._generate_folder_zpl(
            barcode=barcode,
            folder_name=folder.name,
            container_name=folder.container_id.name if folder.container_id else ''
        )
        
        pdf_data = self._render_zpl_to_pdf(
            zpl=zpl,
            width=self.FOLDER_LABEL_WIDTH,
            height=self.FOLDER_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"folder_label_{barcode}.pdf",
            'zpl': zpl
        }
    
    def generate_qr_label(self, record, record_type='container'):
        """
        Generate a QR code label that links to portal login.
        
        Args:
            record: Container, folder, or document record
            record_type (str): 'container', 'folder', or 'document'
            
        Returns:
            dict: {
                'pdf_data': base64-encoded PDF,
                'filename': suggested filename,
                'zpl': raw ZPL code
            }
        """
        # Get base URL for portal
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_url = f"{base_url}/my"
        
        # Generate QR code ZPL
        zpl = self._generate_qr_zpl(
            qr_data=portal_url,
            label_text=record.name,
            record_type=record_type
        )
        
        pdf_data = self._render_zpl_to_pdf(
            zpl=zpl,
            width=self.QR_LABEL_WIDTH,
            height=self.QR_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"qr_label_{record_type}_{record.id}.pdf",
            'zpl': zpl
        }
    
    # ============================================================================
    # ZPL GENERATION METHODS
    # ============================================================================
    
    def _generate_container_zpl(self, barcode, container_name, customer_name='', location=''):
        """
        Generate ZPL code for container label with barcode and box icon.
        
        Layout (4" x 1.33"):
        - Top: Large barcode spanning most of width
        - Bottom left: Container name
        - Bottom middle: Customer name
        - Bottom right: Location/Vault
        - Right side: Box archive icon
        """
        # ZPL dimensions in dots (203 DPI)
        label_width_dots = int(self.CONTAINER_LABEL_WIDTH * 203)
        label_height_dots = int(self.CONTAINER_LABEL_HEIGHT * 203)
        
        # Truncate text to fit
        container_name = (container_name[:20] + '...') if len(container_name) > 20 else container_name
        customer_name = (customer_name[:25] + '...') if len(customer_name) > 25 else customer_name
        location = (location[:25] + '...') if len(location) > 25 else location
        
        zpl = f"""^XA
^FO30,10^BY3^BCN,100,Y,N,N^FD{barcode}^FS
^FO30,120^A0N,30,30^FDContainer: ^FS
^FO30,155^A0N,24,24^FD{container_name}^FS
^FO30,185^A0N,20,20^FD{customer_name}^FS
^FO30,210^A0N,18,18^FD{location}^FS
^FO{label_width_dots - 120},10^GB100,100,5^FS
^FO{label_width_dots - 105},50^A0N,30,30^FDBOX^FS
^XZ"""
        return zpl
    
    def _generate_folder_zpl(self, barcode, folder_name, container_name=''):
        """
        Generate ZPL code for file folder label with barcode and folder icon.
        
        Layout (2.5935" x 1"):
        - Left: Barcode (smaller, rotated)
        - Center: Folder name
        - Right: Folder icon approximation
        """
        label_width_dots = int(self.FOLDER_LABEL_WIDTH * 203)
        label_height_dots = int(self.FOLDER_LABEL_HEIGHT * 203)
        
        folder_name = (folder_name[:25] + '...') if len(folder_name) > 25 else folder_name
        container_name = (container_name[:20] + '...') if len(container_name) > 20 else container_name
        
        zpl = f"""^XA
^FO20,10^BY1^BCN,50,N,N,N^FD{barcode}^FS
^FO20,70^A0N,20,20^FD{folder_name}^FS
^FO20,95^A0N,15,15^FD{container_name}^FS
^FO{label_width_dots - 60},10^GB50,60,3^FS
^FO{label_width_dots - 55},15^A0N,12,12^FDFLDR^FS
^XZ"""
        return zpl
    
    def _generate_qr_zpl(self, qr_data, label_text, record_type=''):
        """
        Generate ZPL code for QR code label linking to portal.
        
        Layout (1" x 1.25"):
        - Top: QR Code (centered)
        - Bottom: Record type + truncated name
        """
        label_width_dots = int(self.QR_LABEL_WIDTH * 203)
        label_height_dots = int(self.QR_LABEL_HEIGHT * 203)
        
        label_text = (label_text[:15] + '...') if len(label_text) > 15 else label_text
        
        # QR code position (centered)
        qr_size = 120  # dots
        qr_x = (label_width_dots - qr_size) // 2
        
        zpl = f"""^XA
^FO{qr_x},10^BQN,2,4^FDQA,{qr_data}^FS
^FO10,140^A0N,18,18^FD{record_type.upper()}^FS
^FO10,160^A0N,15,15^FD{label_text}^FS
^FO10,180^A0N,12,12^FDScan for Portal^FS
^XZ"""
        return zpl
    
    # ============================================================================
    # LABELARY API INTEGRATION
    # ============================================================================
    
    def _render_zpl_to_pdf(self, zpl, width, height, dpmm=8):
        """
        Render ZPL code to PDF using Labelary's free API.
        
        Args:
            zpl (str): ZPL code to render
            width (float): Label width in inches
            height (float): Label height in inches
            dpmm (int): Dots per millimeter (6, 8, 12, or 24)
            
        Returns:
            str: Base64-encoded PDF data
            
        Raises:
            UserError: If API request fails
        """
        url = self.LABELARY_API_URL.format(dpmm=f'{dpmm}dpmm', width=width, height=height)
        
        try:
            response = requests.post(
                url,
                data=zpl,
                headers={'Accept': 'application/pdf'},
                timeout=10
            )
            
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('utf-8')
            elif response.status_code == 429:
                raise UserError(_(
                    "Label generation API rate limit exceeded (5,000/day). "
                    "Please try again later or contact your administrator."
                ))
            else:
                _logger.error(f"Labelary API error: {response.status_code} - {response.text}")
                raise UserError(_(
                    "Failed to generate label PDF. API returned status %s. "
                    "Please contact your administrator."
                ) % response.status_code)
                
        except requests.exceptions.Timeout:
            raise UserError(_("Label generation service timed out. Please try again."))
        except requests.exceptions.ConnectionError:
            raise UserError(_(
                "Cannot connect to label generation service. "
                "Please check your internet connection."
            ))
        except Exception as e:
            _logger.exception("Unexpected error generating label")
            raise UserError(_(
                "An unexpected error occurred while generating the label: %s"
            ) % str(e))
    
    # ============================================================================
    # BATCH LABEL GENERATION
    # ============================================================================
    
    def generate_batch_container_labels(self, containers):
        """
        Generate a single PDF with multiple container labels.
        
        Args:
            containers (recordset): Multiple container records
            
        Returns:
            dict: {
                'pdf_data': base64-encoded PDF with all labels,
                'filename': suggested filename,
                'label_count': number of labels generated
            }
        """
        if not containers:
            raise UserError(_("No containers selected for label printing."))
        
        # Generate ZPL for all containers
        all_zpl = []
        for container in containers:
            barcode = container.barcode or container.temp_barcode
            if barcode:
                zpl = self._generate_container_zpl(
                    barcode=barcode,
                    container_name=container.name,
                    customer_name=container.partner_id.name if container.partner_id else '',
                    location=container.location_id.complete_name if container.location_id else ''
                )
                all_zpl.append(zpl)
        
        if not all_zpl:
            raise UserError(_("None of the selected containers have barcodes assigned."))
        
        # Combine all ZPL (each label is a separate ^XA...^XZ block)
        combined_zpl = '\n'.join(all_zpl)
        
        # Render to PDF (Labelary will create multi-page PDF)
        pdf_data = self._render_zpl_to_pdf(
            zpl=combined_zpl,
            width=self.CONTAINER_LABEL_WIDTH,
            height=self.CONTAINER_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"container_labels_batch_{fields.Date.today()}.pdf",
            'label_count': len(all_zpl)
        }
    
    def generate_batch_folder_labels(self, folders):
        """Generate batch labels for multiple file folders."""
        if not folders:
            raise UserError(_("No folders selected for label printing."))
        
        all_zpl = []
        for folder in folders:
            barcode = folder.barcode or folder.temp_barcode
            if barcode:
                zpl = self._generate_folder_zpl(
                    barcode=barcode,
                    folder_name=folder.name,
                    container_name=folder.container_id.name if folder.container_id else ''
                )
                all_zpl.append(zpl)
        
        if not all_zpl:
            raise UserError(_("None of the selected folders have barcodes assigned."))
        
        combined_zpl = '\n'.join(all_zpl)
        pdf_data = self._render_zpl_to_pdf(
            zpl=combined_zpl,
            width=self.FOLDER_LABEL_WIDTH,
            height=self.FOLDER_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"folder_labels_batch_{fields.Date.today()}.pdf",
            'label_count': len(all_zpl)
        }
    
    def generate_preprint_container_labels(self, barcode_list):
        """
        Generate pre-printed blank container labels with barcodes.
        
        Used for printing labels in advance that will be applied to containers later.
        Labels show barcode but no container-specific information.
        
        Args:
            barcode_list (list): List of barcode strings to print
        
        Returns:
            dict: PDF data, filename, label count
        """
        if not barcode_list:
            raise UserError(_("No barcodes provided for pre-printing."))
        
        all_zpl = []
        for barcode in barcode_list:
            # Generate blank label with just barcode and "UNASSIGNED" placeholder
            zpl = self._generate_container_zpl(
                barcode=barcode,
                container_name='UNASSIGNED',
                customer_name='',
                location_name=''
            )
            all_zpl.append(zpl)
        
        combined_zpl = '\n'.join(all_zpl)
        pdf_data = self._render_zpl_to_pdf(
            zpl=combined_zpl,
            width=self.CONTAINER_LABEL_WIDTH,
            height=self.CONTAINER_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"preprint_container_labels_{fields.Date.today()}.pdf",
            'label_count': len(all_zpl)
        }
    
    def generate_preprint_folder_labels(self, barcode_list):
        """Generate pre-printed blank folder labels with barcodes."""
        if not barcode_list:
            raise UserError(_("No barcodes provided for pre-printing."))
        
        all_zpl = []
        for barcode in barcode_list:
            zpl = self._generate_folder_zpl(
                barcode=barcode,
                folder_name='UNASSIGNED',
                container_name=''
            )
            all_zpl.append(zpl)
        
        combined_zpl = '\n'.join(all_zpl)
        pdf_data = self._render_zpl_to_pdf(
            zpl=combined_zpl,
            width=self.FOLDER_LABEL_WIDTH,
            height=self.FOLDER_LABEL_HEIGHT,
            dpmm=8
        )
        
        return {
            'pdf_data': pdf_data,
            'filename': f"preprint_folder_labels_{fields.Date.today()}.pdf",
            'label_count': len(all_zpl)
        }
