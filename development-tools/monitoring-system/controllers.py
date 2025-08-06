# -*- coding: utf-8 -*-
"""
HTTP Controller for Live Monitoring API
======================================

Provides HTTP endpoints for real-time monitoring data without affecting module loading.
This controller allows external systems to retrieve monitoring data and health status.
"""

from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)


class RecordsManagementMonitoringController(http.Controller):
    """
    HTTP Controller for monitoring endpoints
    These endpoints don't affect module loading and provide real-time data
    """

    @http.route('/records_management/monitor/health', type='http', auth='none', 
                methods=['GET'], csrf=False, cors='*')
    def health_check_endpoint(self, **kwargs):
        """
        Public health check endpoint
        Returns JSON with system health status
        """
        try:
            # Perform basic health check
            health_data = {
                'status': 'healthy',
                'timestamp': request.env['ir.fields'].datetime.now().isoformat(),
                'module': 'records_management',
                'version': '18.0.6.0.0'
            }

            # Test database connectivity
            try:
                request.env.cr.execute("SELECT 1")
                health_data['database'] = 'connected'
            except Exception as e:
                health_data['database'] = 'disconnected'
                health_data['status'] = 'unhealthy'
                health_data['error'] = str(e)

            return Response(
                json.dumps(health_data, indent=2),
                content_type='application/json',
                status=200 if health_data['status'] == 'healthy' else 500
            )

        except Exception as e:
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }
            return Response(
                json.dumps(error_response, indent=2),
                content_type='application/json',
                status=500
            )

    @http.route('/records_management/monitor/errors', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_recent_errors(self, limit=50, severity=None, **kwargs):
        """
        Get recent errors from monitoring system
        Requires user authentication
        """
        try:
            domain = [('monitor_type', '=', 'error')]

            if severity:
                domain.append(('severity', '=', severity))

            # Get recent errors
            errors = request.env['records.management.monitor'].search(
                domain, limit=int(limit), order='create_date desc'
            )

            error_data = []
            for error in errors:
                error_data.append({
                    'id': error.id,
                    'timestamp': error.create_date.isoformat(),
                    'severity': error.severity,
                    'message': error.error_message,
                    'model': error.affected_model,
                    'method': error.affected_method,
                    'user': error.user_id.name,
                    'status': error.status,
                    'occurrence_count': error.occurrence_count
                })

            response_data = {
                'status': 'success',
                'count': len(error_data),
                'errors': error_data,
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }

            return Response(
                json.dumps(response_data, indent=2),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }
            return Response(
                json.dumps(error_response, indent=2),
                content_type='application/json',
                status=500
            )

    @http.route('/records_management/monitor/performance', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_performance_data(self, hours=24, **kwargs):
        """
        Get performance monitoring data
        """
        try:
            from datetime import datetime, timedelta

            # Calculate time range
            start_time = datetime.now() - timedelta(hours=int(hours))

            # Get performance data
            performance_logs = request.env['records.management.monitor'].search([
                ('monitor_type', '=', 'performance'),
                ('create_date', '>=', start_time)
            ], order='create_date desc')

            performance_data = []
            for log in performance_logs:
                performance_data.append({
                    'id': log.id,
                    'timestamp': log.create_date.isoformat(),
                    'operation': log.name,
                    'execution_time': log.execution_time,
                    'memory_usage': log.memory_usage,
                    'cpu_usage': log.cpu_usage,
                    'severity': log.severity
                })

            # Calculate averages
            if performance_data:
                avg_execution_time = sum(p['execution_time'] for p in performance_data if p['execution_time']) / len(performance_data)
                max_execution_time = max(p['execution_time'] for p in performance_data if p['execution_time'])
            else:
                avg_execution_time = 0
                max_execution_time = 0

            response_data = {
                'status': 'success',
                'count': len(performance_data),
                'statistics': {
                    'average_execution_time': avg_execution_time,
                    'max_execution_time': max_execution_time,
                    'time_range_hours': hours
                },
                'performance_logs': performance_data,
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }

            return Response(
                json.dumps(response_data, indent=2),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            error_response = {
                'status': 'error',
                'message': str(e),
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }
            return Response(
                json.dumps(error_response, indent=2),
                content_type='application/json',
                status=500
            )

    @http.route('/records_management/monitor/webhook/receive', type='json', auth='none',
                methods=['POST'], csrf=False, cors='*')
    def receive_external_alert(self, **kwargs):
        """
        Receive alerts from external monitoring systems
        """
        try:
            data = request.jsonrequest

            # Create monitoring entry from external alert
            monitor_data = {
                'name': f"External Alert: {data.get('message', 'Unknown')}",
                'monitor_type': data.get('type', 'info'),
                'severity': data.get('severity', 'medium'),
                'error_message': data.get('message', ''),
                'error_context': json.dumps(data),
                'affected_model': data.get('source', 'external'),
            }

            request.env['records.management.monitor'].sudo().create(monitor_data)

            return {
                'status': 'success',
                'message': 'Alert received and logged',
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }

        except Exception as e:
            _logger.error(f"External alert reception failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': request.env['ir.fields'].datetime.now().isoformat()
            }

    @http.route('/records_management/monitor/stream', type='http', auth='user',
                methods=['GET'], csrf=False)
    def stream_monitoring_data(self, **kwargs):
        """
        Server-Sent Events endpoint for real-time monitoring
        """
        try:
            def event_stream():
                """Generator for SSE events"""
                while True:
                    # Get latest monitoring entries
                    latest_entries = request.env['records.management.monitor'].search([
                        ('create_date', '>=', request.env['ir.fields'].datetime.now() - timedelta(minutes=1))
                    ], order='create_date desc', limit=10)

                    for entry in latest_entries:
                        event_data = {
                            'id': entry.id,
                            'type': entry.monitor_type,
                            'severity': entry.severity,
                            'message': entry.name,
                            'timestamp': entry.create_date.isoformat()
                        }

                        yield f"data: {json.dumps(event_data)}\n\n"

                    # Wait before next check
                    import time
                    time.sleep(5)

            return Response(
                event_stream(),
                content_type='text/event-stream',
                headers=[
                    ('Cache-Control', 'no-cache'),
                    ('Connection', 'keep-alive'),
                    ('Access-Control-Allow-Origin', '*')
                ]
            )

        except Exception as e:
            _logger.error(f"Monitoring stream error: {e}")
            return Response(
                f"data: {json.dumps({'error': str(e)})}\n\n",
                content_type='text/event-stream',
                status=500
            )
