from odoo import http
from odoo.http import request


class RecordsManagementController(http.Controller):
    @http.route("/records/dashboard", type="http", auth="user", website=True)
    def records_dashboard(self):
        containers = request.env["records.container"].search([])
        documents = request.env["records.document"].search([])
        locations = request.env["records.location"].search([])

        return request.render(
            "records_management.dashboard",
            {
                "containers": containers,
                "documents": documents,
                "locations": locations,
            },
        )
