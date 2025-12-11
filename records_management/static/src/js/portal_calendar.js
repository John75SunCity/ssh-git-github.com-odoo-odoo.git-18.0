odoo.define('records_management.portal_calendar', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.PortalCalendar = publicWidget.Widget.extend({
        selector: '#portal-calendar',

        start: function () {
            var self = this;
            var calendarEl = document.getElementById('portal-calendar');
            
            if (!calendarEl) {
                console.error('Calendar element not found');
                return this._super.apply(this, arguments);
            }

            var calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,listWeek'
                },
                buttonText: {
                    today: 'Today',
                    month: 'Month',
                    week: 'Week',
                    list: 'List'
                },
                height: 'auto',
                events: function(info, successCallback, failureCallback) {
                    // Fetch events from server
                    ajax.jsonRpc('/my/calendar/events', 'call', {
                        start: info.startStr,
                        end: info.endStr
                    }).then(function(events) {
                        $('#calendar-loading').hide();
                        $('#portal-calendar').show();
                        successCallback(events);
                    }).catch(function(error) {
                        console.error('Error fetching calendar events:', error);
                        $('#calendar-loading').html(
                            '<div class="alert alert-danger">Failed to load calendar events. Please try again later.</div>'
                        );
                        failureCallback(error);
                    });
                },
                eventClick: function(info) {
                    info.jsEvent.preventDefault();
                    
                    var event = info.event;
                    var props = event.extendedProps;
                    
                    // Build modal content
                    var modalBody = '<dl class="row">';
                    modalBody += '<dt class="col-sm-4">Title:</dt><dd class="col-sm-8">' + event.title + '</dd>';
                    modalBody += '<dt class="col-sm-4">Date:</dt><dd class="col-sm-8">' + 
                        event.start.toLocaleDateString() + ' ' + 
                        (event.start.toLocaleTimeString() !== '12:00:00 AM' ? event.start.toLocaleTimeString() : '') + 
                        '</dd>';
                    
                    if (event.end) {
                        modalBody += '<dt class="col-sm-4">End:</dt><dd class="col-sm-8">' + 
                            event.end.toLocaleDateString() + ' ' + event.end.toLocaleTimeString() + 
                            '</dd>';
                    }
                    
                    // Add type-specific details
                    if (props.type === 'shredding') {
                        modalBody += '<dt class="col-sm-4">Frequency:</dt><dd class="col-sm-8">' + 
                            (props.frequency || 'N/A').charAt(0).toUpperCase() + (props.frequency || 'N/A').slice(1) + 
                            '</dd>';
                        modalBody += '<dt class="col-sm-4">Location:</dt><dd class="col-sm-8">' + (props.location || 'N/A') + '</dd>';
                    } else if (props.type === 'service') {
                        modalBody += '<dt class="col-sm-4">Type:</dt><dd class="col-sm-8">' + 
                            (props.work_order_type || 'N/A').charAt(0).toUpperCase() + (props.work_order_type || 'N/A').slice(1) + 
                            '</dd>';
                        modalBody += '<dt class="col-sm-4">Stage:</dt><dd class="col-sm-8">' + (props.stage || 'N/A') + '</dd>';
                    } else if (props.type === 'request') {
                        modalBody += '<dt class="col-sm-4">Request Type:</dt><dd class="col-sm-8">' + 
                            (props.request_type || 'N/A').charAt(0).toUpperCase() + (props.request_type || 'N/A').slice(1) + 
                            '</dd>';
                        modalBody += '<dt class="col-sm-4">Status:</dt><dd class="col-sm-8">' + (props.state || 'N/A') + '</dd>';
                    }
                    
                    modalBody += '</dl>';
                    
                    // Update modal
                    $('#eventModalTitle').text(event.title);
                    $('#eventModalBody').html(modalBody);
                    
                    // Show/hide "View Details" button
                    if (event.url) {
                        $('#eventViewDetailsBtn').attr('href', event.url).show();
                    } else {
                        $('#eventViewDetailsBtn').hide();
                    }
                    
                    // Show modal
                    $('#eventDetailsModal').modal('show');
                },
                eventDidMount: function(info) {
                    // Add tooltip
                    $(info.el).tooltip({
                        title: info.event.title,
                        placement: 'top',
                        trigger: 'hover',
                        container: 'body'
                    });
                }
            });

            calendar.render();
            
            return this._super.apply(this, arguments);
        }
    });

    return publicWidget.registry.PortalCalendar;
});
