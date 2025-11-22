odoo.define('records_management.portal_signature', [], function (require) {
    "use strict";

    // Frontend-compatible implementation without backend dependencies
    var _t = function(str) { return str; }; // Simple translation placeholder
    
    // No sign widget dependency - using custom implementation only
    var SignWidget = null;
    
    // Simple Widget base class replacement
    var Widget = function() {};
    Widget.extend = function(obj) {
        obj._super = function() {};
        return obj;
    };

    var PortalSignature = Widget.extend({
        template: 'portal_signature_canvas',
        
        init: function(parent, options) {
            this._super(parent);
            this.options = _.defaults(options || {}, {
                width: 600,
                height: 200,
                backgroundColor: '#ffffff',
                penColor: '#000000',
                lineWidth: 2,
                required: true,
                enableTyped: true,
                enableDrawn: true
            });
            this.signatureData = null;
            this.signatureType = 'drawn'; // 'drawn' or 'typed'
            this.isDrawing = false;
            this.lastX = 0;
            this.lastY = 0;
        },

        start: function() {
            var self = this;
            this._super.apply(this, arguments);
            
            this.setupCanvas();
            this.setupEventHandlers();
            this.setupTypedSignature();
            
            return this._super();
        },

        setupCanvas: function() {
            this.canvas = this.$('#signature_canvas')[0];
            this.ctx = this.canvas.getContext('2d');
            
            // Set canvas size
            this.canvas.width = this.options.width;
            this.canvas.height = this.options.height;
            
            // Set canvas style
            this.ctx.fillStyle = this.options.backgroundColor;
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.strokeStyle = this.options.penColor;
            this.ctx.lineWidth = this.options.lineWidth;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
        },

        setupEventHandlers: function() {
            var self = this;

            // Canvas drawing events
            this.$('#signature_canvas').on('mousedown touchstart', function(e) {
                self.startDrawing(e);
            });

            this.$('#signature_canvas').on('mousemove touchmove', function(e) {
                self.draw(e);
            });

            this.$('#signature_canvas').on('mouseup touchend mouseleave', function(e) {
                self.stopDrawing(e);
            });

            // Button events
            this.$('#clear_signature').on('click', function() {
                self.clearSignature();
            });

            this.$('#signature_type_drawn').on('click', function() {
                self.setSignatureType('drawn');
            });

            this.$('#signature_type_typed').on('click', function() {
                self.setSignatureType('typed');
            });

            this.$('#typed_signature_input').on('input', function() {
                self.updateTypedSignature();
            });

            // Prevent scrolling when touching the canvas
            document.body.addEventListener("touchstart", function (e) {
                if (e.target == self.canvas) {
                    e.preventDefault();
                }
            }, { passive: false });

            document.body.addEventListener("touchend", function (e) {
                if (e.target == self.canvas) {
                    e.preventDefault();
                }
            }, { passive: false });

            document.body.addEventListener("touchmove", function (e) {
                if (e.target == self.canvas) {
                    e.preventDefault();
                }
            }, { passive: false });
        },

        setupTypedSignature: function() {
            this.typedCanvas = this.$('#typed_signature_canvas')[0];
            this.typedCtx = this.typedCanvas.getContext('2d');
            
            this.typedCanvas.width = this.options.width;
            this.typedCanvas.height = this.options.height;
        },

        startDrawing: function(e) {
            if (this.signatureType !== 'drawn') return;
            
            this.isDrawing = true;
            var rect = this.canvas.getBoundingClientRect();
            var clientX = e.clientX || (e.touches && e.touches[0].clientX);
            var clientY = e.clientY || (e.touches && e.touches[0].clientY);
            
            this.lastX = clientX - rect.left;
            this.lastY = clientY - rect.top;
            
            this.ctx.beginPath();
            this.ctx.moveTo(this.lastX, this.lastY);
        },

        draw: function(e) {
            if (!this.isDrawing || this.signatureType !== 'drawn') return;
            
            e.preventDefault();
            var rect = this.canvas.getBoundingClientRect();
            var clientX = e.clientX || (e.touches && e.touches[0].clientX);
            var clientY = e.clientY || (e.touches && e.touches[0].clientY);
            
            var currentX = clientX - rect.left;
            var currentY = clientY - rect.top;
            
            this.ctx.lineTo(currentX, currentY);
            this.ctx.stroke();
            
            this.lastX = currentX;
            this.lastY = currentY;
        },

        stopDrawing: function(e) {
            if (!this.isDrawing) return;
            this.isDrawing = false;
            this.ctx.closePath();
        },

        setSignatureType: function(type) {
            this.signatureType = type;
            
            this.$('#signature_type_drawn').toggleClass('active', type === 'drawn');
            this.$('#signature_type_typed').toggleClass('active', type === 'typed');
            
            this.$('#drawn_signature_container').toggle(type === 'drawn');
            this.$('#typed_signature_container').toggle(type === 'typed');
            
            if (type === 'typed') {
                this.updateTypedSignature();
            }
        },

        updateTypedSignature: function() {
            var text = this.$('#typed_signature_input').val();
            
            this.typedCtx.fillStyle = this.options.backgroundColor;
            this.typedCtx.fillRect(0, 0, this.typedCanvas.width, this.typedCanvas.height);
            
            if (text) {
                this.typedCtx.fillStyle = this.options.penColor;
                this.typedCtx.font = '48px Brush Script MT, cursive';
                this.typedCtx.textAlign = 'center';
                this.typedCtx.textBaseline = 'middle';
                this.typedCtx.fillText(text, this.typedCanvas.width / 2, this.typedCanvas.height / 2);
            }
        },

        clearSignature: function() {
            if (this.signatureType === 'drawn') {
                this.ctx.fillStyle = this.options.backgroundColor;
                this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            } else {
                this.$('#typed_signature_input').val('');
                this.updateTypedSignature();
            }
            this.signatureData = null;
        },

        getSignatureData: function() {
            var canvas = this.signatureType === 'drawn' ? this.canvas : this.typedCanvas;
            return canvas.toDataURL('image/png');
        },

        hasSignature: function() {
            if (this.signatureType === 'drawn') {
                var imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
                var data = imageData.data;
                
                // Check if any pixel is not the background color
                for (var i = 0; i < data.length; i += 4) {
                    if (data[i] !== 255 || data[i + 1] !== 255 || data[i + 2] !== 255) {
                        return true;
                    }
                }
                return false;
            } else {
                return this.$('#typed_signature_input').val().trim().length > 0;
            }
        },

        validateSignature: function() {
            if (this.options.required && !this.hasSignature()) {
                this.showError(_t('Signature is required. Please sign before continuing.'));
                return false;
            }
            return true;
        },

        showError: function(message) {
            this.$('.signature-error').remove();
            this.$el.prepend(`
                <div class="alert alert-danger signature-error">
                    <i class="fa fa-exclamation-circle"></i> ${message}
                </div>
            `);
        }
    });

    var PortalSignatureManager = {
        init: function() {
            this.setupEventHandlers();
        },

        setupEventHandlers: function() {
            var self = this;

            // Sign request button
            $(document).on('click', '.sign-request-btn', function(e) {
                e.preventDefault();
                var requestId = $(this).data('request-id');
                var signType = $(this).data('sign-type') || 'request';
                self.openSignatureDialog(requestId, signType);
            });

            // Quick sign buttons
            $(document).on('click', '.quick-sign-btn', function(e) {
                e.preventDefault();
                var requestId = $(this).data('request-id');
                self.quickSign(requestId);
            });

            // Verify signature buttons
            $(document).on('click', '.verify-signature-btn', function(e) {
                e.preventDefault();
                var requestId = $(this).data('request-id');
                self.verifySignature(requestId);
            });
        },

        openSignatureDialog: function(requestId, signType) {
            var self = this;
            
            // If Odoo sign widget is available, use it
            if (SignWidget && signType === 'document') {
                return self.useOdooSignWidget(requestId);
            }

            // Otherwise use custom signature dialog
            this.showSignatureDialog(requestId, signType);
        },

        useOdooSignWidget: function(requestId) {
            var self = this;
            
            ajax.jsonRpc('/my/signature/get_sign_request', 'call', {
                'request_id': requestId
            }).then(function(result) {
                if (result.success && result.sign_request_id) {
                    new SignWidget(null, {
                        sign_request_id: result.sign_request_id,
                        token: result.token
                    }).open();
                } else {
                    self.showSignatureDialog(requestId, 'request');
                }
            }).catch(function(error) {
                console.error('Error loading sign widget:', error);
                self.showSignatureDialog(requestId, 'request');
            });
        },

        showSignatureDialog: function(requestId, signType) {
            var self = this;

            var dialog = new Dialog(this, {
                size: 'large',
                title: _t('Electronic Signature'),
                buttons: [
                    {
                        text: _t('Sign & Submit'),
                        classes: 'btn-primary',
                        click: function() {
                            self.submitSignature(requestId, signType, dialog);
                        }
                    },
                    {
                        text: _t('Cancel'),
                        close: true
                    }
                ],
                $content: $(core.qweb.render('portal_signature_dialog', {
                    request_id: requestId,
                    sign_type: signType
                }))
            });

            dialog.open().then(function() {
                // Initialize signature widget
                var signatureWidget = new PortalSignature(dialog, {
                    width: 600,
                    height: 200,
                    required: true
                });
                
                signatureWidget.appendTo(dialog.$('.signature-container'));
                dialog.signatureWidget = signatureWidget;

                // Load request details
                self.loadRequestDetails(requestId, dialog);
            });
        },

        loadRequestDetails: function(requestId, dialog) {
            ajax.jsonRpc('/my/signature/get_request_details', 'call', {
                'request_id': requestId
            }).then(function(result) {
                if (result.success) {
                    dialog.$('.request-details').html(result.html);
                    
                    // Show terms if required
                    if (result.terms_required) {
                        dialog.$('.terms-container').show();
                    }
                }
            });
        },

        submitSignature: function(requestId, signType, dialog) {
            var self = this;
            var signatureWidget = dialog.signatureWidget;

            // Validate signature
            if (!signatureWidget.validateSignature()) {
                return;
            }

            // Check terms acceptance if required
            if (dialog.$('#accept_terms').length && !dialog.$('#accept_terms').is(':checked')) {
                signatureWidget.showError(_t('You must accept the terms and conditions to continue.'));
                return;
            }

            // Show loading state
            dialog.$('.btn-primary').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Signing...');

            // Get signature data
            var signatureData = signatureWidget.getSignatureData();
            var signatureInfo = {
                data: signatureData,
                type: signatureWidget.signatureType,
                timestamp: new Date().toISOString(),
                ip_address: null, // Will be set on server
                user_agent: navigator.userAgent
            };

            // Submit signature
            ajax.jsonRpc('/my/signature/submit', 'call', {
                'request_id': requestId,
                'sign_type': signType,
                'signature_info': signatureInfo,
                'terms_accepted': dialog.$('#accept_terms').is(':checked')
            }).then(function(result) {
                if (result.success) {
                    dialog.close();
                    self.showSignatureSuccess(result);
                    
                    // Refresh page or update UI
                    if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                    } else {
                        location.reload();
                    }
                } else {
                    dialog.$('.btn-primary').prop('disabled', false).html(_t('Sign & Submit'));
                    signatureWidget.showError(result.error || _t('An error occurred while submitting your signature.'));
                }
            }).catch(function(error) {
                dialog.$('.btn-primary').prop('disabled', false).html(_t('Sign & Submit'));
                signatureWidget.showError(_t('Network error. Please try again.'));
                console.error('Signature submission error:', error);
            });
        },

        quickSign: function(requestId) {
            var self = this;
            
            var dialog = new Dialog(this, {
                title: _t('Quick Sign Confirmation'),
                size: 'medium',
                buttons: [
                    {
                        text: _t('Confirm & Sign'),
                        classes: 'btn-primary',
                        click: function() {
                            self.processQuickSign(requestId, dialog);
                        }
                    },
                    {
                        text: _t('Cancel'),
                        close: true
                    }
                ],
                $content: $(`
                    <div class="text-center">
                        <i class="fa fa-pen-square fa-3x text-primary mb-3"></i>
                        <h4>Quick Sign Confirmation</h4>
                        <p class="text-muted">
                            This will apply your default signature to the request. 
                            You can always provide a custom signature if needed.
                        </p>
                        <div class="form-check mt-3">
                            <input class="form-check-input" type="checkbox" id="quick_sign_terms">
                            <label class="form-check-label" for="quick_sign_terms">
                                I accept the terms and conditions for this request
                            </label>
                        </div>
                    </div>
                `)
            });

            dialog.open();
        },

        processQuickSign: function(requestId, dialog) {
            var self = this;

            if (!dialog.$('#quick_sign_terms').is(':checked')) {
                dialog.$('.modal-body').prepend(`
                    <div class="alert alert-warning">
                        <i class="fa fa-exclamation-triangle"></i> 
                        You must accept the terms and conditions to continue.
                    </div>
                `);
                return;
            }

            dialog.$('.btn-primary').prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Processing...');

            ajax.jsonRpc('/my/signature/quick_sign', 'call', {
                'request_id': requestId
            }).then(function(result) {
                if (result.success) {
                    dialog.close();
                    self.showSignatureSuccess(result);
                    location.reload();
                } else {
                    dialog.$('.btn-primary').prop('disabled', false).html(_t('Confirm & Sign'));
                    dialog.$('.modal-body').prepend(`
                        <div class="alert alert-danger">
                            <i class="fa fa-exclamation-circle"></i> 
                            ${result.error || _t('An error occurred during quick sign.')}
                        </div>
                    `);
                }
            });
        },

        verifySignature: function(requestId) {
            var self = this;

            ajax.jsonRpc('/my/signature/verify', 'call', {
                'request_id': requestId
            }).then(function(result) {
                var dialog = new Dialog(self, {
                    title: _t('Signature Verification'),
                    size: 'large',
                    buttons: [
                        {
                            text: _t('Close'),
                            close: true
                        }
                    ],
                    $content: $(result.html)
                });

                dialog.open();
            });
        },

        showSignatureSuccess: function(result) {
            var dialog = new Dialog(this, {
                title: _t('Signature Submitted Successfully'),
                size: 'medium',
                buttons: [
                    {
                        text: _t('OK'),
                        close: true
                    }
                ],
                $content: $(`
                    <div class="text-center">
                        <i class="fa fa-check-circle fa-3x text-success mb-3"></i>
                        <h4>Signature Submitted Successfully!</h4>
                        <p class="text-muted">
                            Your electronic signature has been recorded and verified. 
                            ${result.message || 'You will receive a confirmation email shortly.'}
                        </p>
                        ${result.reference_number ? `
                        <div class="alert alert-info mt-3">
                            <strong>Reference Number:</strong> ${result.reference_number}
                        </div>
                        ` : ''}
                    </div>
                `)
            });

            dialog.open();
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        PortalSignatureManager.init();
    });

    // Export for use in other modules
    return {
        PortalSignature: PortalSignature,
        PortalSignatureManager: PortalSignatureManager,
        signRequest: function(requestId, signType) {
            PortalSignatureManager.openSignatureDialog(requestId, signType || 'request');
        }
    };
});

/* QWeb Templates - should be included in portal templates */
/*
<template id="portal_signature_dialog">
    <div class="signature-dialog">
        <div class="request-details mb-4">
            <!-- Request details will be loaded here -->
        </div>
        
        <div class="signature-options mb-3">
            <div class="btn-group btn-group-toggle" data-toggle="buttons">
                <label class="btn btn-outline-primary active" id="signature_type_drawn">
                    <input type="radio" name="signature_type" value="drawn" checked> 
                    <i class="fa fa-pencil"></i> Draw Signature
                </label>
                <label class="btn btn-outline-primary" id="signature_type_typed">
                    <input type="radio" name="signature_type" value="typed"> 
                    <i class="fa fa-keyboard-o"></i> Type Signature
                </label>
            </div>
        </div>
        
        <div class="signature-container">
            <div id="drawn_signature_container">
                <canvas id="signature_canvas" class="signature-canvas"></canvas>
                <button type="button" id="clear_signature" class="btn btn-sm btn-outline-secondary mt-2">
                    <i class="fa fa-eraser"></i> Clear
                </button>
            </div>
            
            <div id="typed_signature_container" style="display: none;">
                <input type="text" id="typed_signature_input" class="form-control mb-2" 
                       placeholder="Type your full name">
                <canvas id="typed_signature_canvas" class="signature-canvas"></canvas>
            </div>
        </div>
        
        <div class="terms-container mt-4" style="display: none;">
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="accept_terms">
                <label class="form-check-label" for="accept_terms">
                    I accept the terms and conditions and authorize this electronic signature
                </label>
            </div>
        </div>
    </div>
</template>
*/
