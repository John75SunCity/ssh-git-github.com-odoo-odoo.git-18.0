# -*- coding: utf-8 -*-
"""
Intelligent Search Controller for Records Management System

Provides advanced search capabilities including:
- Container auto-complete with smart filtering
- File search with container recommendations
- Customer portal search integration
- Performance monitoring and optimization
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.tools import config, safe_eval

_logger = logging.getLogger(__name__)


class SearchPerformanceMonitor:
    """Monitor and log search performance metrics"""

    def __init__(self):
        self.query_times = defaultdict(list)
        self.slow_queries = []

    def log_query(self, query_type, duration_ms, query_params=None):
        """Log query performance metrics"""
        self.query_times[query_type].append(duration_ms)

        # Get slow query threshold from config
        threshold = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("records_management.search.slow_query_threshold_ms", 1000)
        )

        if duration_ms > threshold:
            self.slow_queries.append(
                {
                    "type": query_type,
                    "duration": duration_ms,
                    "params": query_params,
                    "timestamp": datetime.now(),
                }
            )
            _logger.warning(
                f"Slow search query detected: {query_type} took {duration_ms}ms "
                f"(threshold: {threshold}ms)"
            )


# Global performance monitor instance
search_monitor = SearchPerformanceMonitor()


class IntelligentSearchController(http.Controller):
    """
    Controller for intelligent search functionality

    Handles container auto-complete, file search recommendations,
    and portal search integration with performance monitoring.
    """

    # ============================================================================
    # CONTAINER NUMBER AUTO-SUGGESTION
    # ============================================================================

    @http.route(
        ["/records/search/containers"], type="json", auth="user", methods=["POST"]
    )
    def search_containers_autocomplete(self, query="", limit=10, customer_id=None):
        """
        Auto-suggest containers based on partial box number input

        Example: query="45" returns containers 4511, 4512, 4589, etc.
        """
        if not query or len(query) < 1:
            return {"suggestions": []}

        domain = [
            ("name", "ilike", f"{query}%"),  # Starts with query
            ("active", "=", True),
            ("state", "in", ["active", "stored"]),
        ]

        # Filter by customer if specified
        if customer_id:
            domain.append(("partner_id", "=", int(customer_id)))

        # Apply department security if applicable
        domain = self._apply_department_security(domain)

        containers = request.env["records.container"].search(
            domain, limit=limit, order="name asc"
        )

        suggestions = []
        for container in containers:
            suggestions.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "description": container.content_description or "",
                    "location": (
                        container.location_id.name if container.location_id else ""
                    ),
                    "alpha_range": container.alpha_range_display or "",
                    "date_range": container.content_date_range_display or "",
                    "content_type": container.primary_content_type or "",
                    "document_count": container.document_count,
                }
            )

        return {"suggestions": suggestions, "total": len(suggestions)}

    # ============================================================================
    # INTELLIGENT FILE SEARCH WITH CONTAINER RECOMMENDATIONS
    # ============================================================================

    @http.route(
        ["/records/search/recommend_containers"],
        type="json",
        auth="user",
        methods=["POST"],
    )
    def recommend_containers_for_file(self, **kwargs):
        """
        Smart container recommendations based on file search criteria

        Parameters:
        - file_name: Name to search for (e.g., "John Doe")
        - date_of_birth: DOB for alphabetical matching
        - service_date: Date to match against container date ranges
        - customer_id: Customer ID for filtering
        - content_type: Type of document being searched
        """
        recommendations = []

        # Extract search parameters
        file_name = kwargs.get("file_name", "").strip()
        date_of_birth = kwargs.get("date_of_birth")
        service_date = kwargs.get("service_date")
        customer_id = kwargs.get("customer_id")
        content_type = kwargs.get("content_type", "")

        if not file_name and not service_date:
            return {
                "recommendations": [],
                "message": "Please provide file name or service date",
            }

        # Build base domain
        domain = [("active", "=", True), ("state", "in", ["active", "stored"])]

        if customer_id:
            domain.append(("partner_id", "=", int(customer_id)))

        # Apply department security
        domain = self._apply_department_security(domain)

        # Search containers using different criteria
        containers = request.env["records.container"].search(domain)

        for container in containers:
            score = 0
            reasons = []

            # 1. Alphabetical range matching
            if file_name and container.alpha_range_start and container.alpha_range_end:
                name_start = file_name[0].upper() if file_name else ""
                if name_start:
                    alpha_start = container.alpha_range_start.upper()
                    alpha_end = container.alpha_range_end.upper()

                    # Check if name falls within alphabetical range
                    if alpha_start <= name_start <= alpha_end:
                        score += 50
                        reasons.append(
                            f"Name '{file_name}' fits alphabetical range {container.alpha_range_display}"
                        )

            # 2. Date range matching
            if (
                service_date
                and container.content_date_from
                and container.content_date_to
            ):
                try:
                    if isinstance(service_date, str):
                        search_date = datetime.strptime(service_date, "%Y-%m-%d").date()
                    else:
                        search_date = service_date

                    if (
                        container.content_date_from
                        <= search_date
                        <= container.content_date_to
                    ):
                        score += 40
                        reasons.append(
                            f"Service date {search_date.strftime('%m/%d/%Y')} falls within container date range"
                        )
                except Exception:
                    pass

            # 3. Content type matching (case-insensitive)
            if (
                content_type
                and container.primary_content_type
                and container.primary_content_type.lower() == content_type.lower()
            ):
                score += 30
                reasons.append(f"Content type matches: {content_type}")

            # 4. Keyword matching in search_keywords
            if file_name and container.search_keywords:
                keywords = container.search_keywords.lower()
                if file_name.lower() in keywords:
                    score += 25
                    reasons.append(f"File name found in container keywords")

            # 5. Content description matching
            if file_name and container.content_description:
                if file_name.lower() in container.content_description.lower():
                    score += 20
                    reasons.append(f"File name found in content description")

            # Only include containers with reasonable match scores
            if score >= 20:
                recommendations.append(
                    {
                        "id": container.id,
                        "name": container.name,
                        "score": score,
                        "confidence": min(score, 95),  # Use score directly, cap at 95%
                        "reasons": reasons,
                        "location": (
                            container.location_id.name
                            if container.location_id
                            else "Unknown"
                        ),
                        "alpha_range": container.alpha_range_display,
                        "date_range": container.content_date_range_display,
                        "content_type": container.primary_content_type,
                        "document_count": container.document_count,
                        "description": container.content_description or "",
                    }
                )

        # Sort by score (highest first) and limit results
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "recommendations": recommendations[:15],  # Limit to top 15 suggestions
            "total": len(recommendations),
            "search_criteria": {
                "file_name": file_name,
                "service_date": service_date,
                "content_type": content_type,
            },
        }

    # ============================================================================
    # PORTAL SEARCH INTEGRATION
    # ============================================================================

    @http.route(
        ["/my/records/search"], type="json", auth="user", website=True, methods=["POST"]
    )
    def portal_search_containers(self, **kwargs):
        """
        Portal search for customers to find their containers and files
        Includes the same intelligent matching as backend search
        """
        if not request.env.user.partner_id:
            return {"error": "Access denied"}

        # Use customer's partner_id for filtering
        customer_id = request.env.user.partner_id.id
        kwargs["customer_id"] = customer_id

        # Check if searching by container number or file criteria
        query = kwargs.get("query", "").strip()

        if query and query.replace("-", "").replace(" ", "").isdigit():
            # Looks like a container number search
            return self.search_containers_autocomplete(
                query=query, customer_id=customer_id, limit=20
            )
        else:
            # File/content search - use intelligent recommendations
            kwargs["file_name"] = query
            return self.recommend_containers_for_file(**kwargs)

    # ============================================================================
    # FULL-TEXT SEARCH ACROSS CONTAINERS
    # ============================================================================

    @http.route(
        ["/records/search/fulltext"], type="json", auth="user", methods=["POST"]
    )
    def fulltext_search_containers(self, query="", customer_id=None, limit=20):
        """
        Full-text search across container contents, descriptions, and keywords
        """
        if not query or len(query) < 2:
            return {"results": [], "message": "Please enter at least 2 characters"}

        domain = [
            ("active", "=", True),
            ("state", "in", ["active", "stored"]),
            "|",
            "|",
            "|",
            ("name", "ilike", query),
            ("content_description", "ilike", query),
            ("search_keywords", "ilike", query),
            ("alpha_range_display", "ilike", query),
        ]

        if customer_id:
            domain.append(("partner_id", "=", int(customer_id)))

        # Apply department security
        domain = self._apply_department_security(domain)

        containers = request.env["records.container"].search(
            domain, limit=limit, order="name asc"
        )

        results = []
        for container in containers:
            # Calculate relevance score based on where match was found
            relevance_score = 0
            match_locations = []

            query_lower = query.lower()

            if query_lower in container.name.lower():
                relevance_score += 100
                match_locations.append("Container Number")

            if (
                container.content_description
                and query_lower in container.content_description.lower()
            ):
                relevance_score += 80
                match_locations.append("Content Description")

            if (
                container.search_keywords
                and query_lower in container.search_keywords.lower()
            ):
                relevance_score += 60
                match_locations.append("Keywords")

            if (
                container.alpha_range_display
                and query_lower in container.alpha_range_display.lower()
            ):
                relevance_score += 40
                match_locations.append("Alphabetical Range")

            results.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "description": container.content_description or "",
                    "location": (
                        container.location_id.name if container.location_id else ""
                    ),
                    "alpha_range": container.alpha_range_display,
                    "date_range": container.content_date_range_display,
                    "content_type": container.primary_content_type,
                    "document_count": container.document_count,
                    "relevance_score": relevance_score,
                    "match_locations": match_locations,
                }
            )

        # Sort by relevance score
        # Limit results before sorting for performance
        results = results[:limit]
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {"results": results, "total": len(results), "query": query}

    # ============================================================================
    # SECURITY & UTILITY METHODS
    def _apply_department_security(self, domain):
        """
        Apply department-level security filtering if applicable.

        Parameters:
            domain (list): The search domain to be filtered.

        Returns:
            list: The updated domain with department-level security applied if needed.
        """
        user = request.env.user

        # Check if user has department restrictions
        if user.has_group("records_management.group_department_restricted"):
            # Get user's allowed department IDs
            allowed_departments = user.department_ids.ids

            if allowed_departments:
                # Restrict search to allowed departments
                domain += [
                    "|",
                    ("department_id", "in", allowed_departments),
                    ("department_id", "=", False),  # Include records with no department
                ]

        return domain

    @http.route(
        ["/records/search/suggestions/config"],
        type="json",
        auth="user",
        methods=["GET"],
    )
    def get_search_config(self):
        """
        Return configuration for search suggestions (content types, etc.).

        Returns:
            dict: {
                "content_types": list of available content type selections,
                "max_suggestions": int, maximum number of suggestions to return,
                "min_query_length": int, minimum query length for suggestions,
                "search_delay_ms": int, debounce delay in milliseconds for auto-suggest
            }
        """
        container_model = request.env["records.container"]

        # Get content type options
        content_types = []
        if (
            hasattr(container_model, "_fields")
            and "primary_content_type" in container_model._fields
        ):
            field = container_model._fields["primary_content_type"]
            if hasattr(field, "selection"):
                content_types = field.selection

        return {
            "content_types": content_types,
            "max_suggestions": 15,
            "min_query_length": 1,
            "search_delay_ms": 300,  # Debounce delay for auto-suggest
        }
