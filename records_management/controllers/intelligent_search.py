# -*- coding: utf-8 -*-
"""
Intelligent Search Controller for Records Management System

Provides advanced search capabilities including:
- Container auto-complete with smart filtering
- File search with container recommendations
- Customer portal search integration
- Performance monitoring and optimization
"""

import logging
import time
from datetime import datetime
from odoo.http import request

from odoo import http

from collections import defaultdict



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
                "Slow search query detected: %s took %sms (threshold: %sms)",
                query_type, duration_ms, threshold
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
        ["/records/search/containers"], type="jsonrpc", auth="user", methods=["POST"]
    )
    def _search_containers_autocomplete(self, query="", limit=10, customer_id=None):
        """
        Auto-suggest containers based on partial box number input

        Example: query="45" returns containers 4511, 4512, 4589, etc.
        """
        start_time = time.time()

        try:
            if not query or not query.strip():
                return {"suggestions": [], "total": 0}

            # Sanitize query input
            query = query.strip()
            if not query:
                return {"suggestions": [], "total": 0}

            domain = [
                ("name", "ilike", "%s%%" % query),  # Starts with query
                ("active", "=", True),
                ("state", "in", ["active", "stored"]),
            ]

            # Filter by customer if specified
            if customer_id:
                try:
                    customer_id = int(customer_id)
                    domain.append(("partner_id", "=", customer_id))
                except (ValueError, TypeError):
                    _logger.warning("Invalid customer_id provided: %s", customer_id)
                    return {"error": "Invalid customer ID", "suggestions": []}

            # Apply department security if applicable
            domain = self._apply_department_security(domain)

            containers = request.env["records.container"].search(
                domain, limit=int(limit), order="name asc"
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
                        "document_count": container.document_count or 0,
                    }
                )

            # Log performance metrics
            duration_ms = (time.time() - start_time) * 1000
            search_monitor.log_query("container_autocomplete", duration_ms, {"query": query, "limit": limit})

            return {"suggestions": suggestions, "total": len(suggestions)}

        except Exception as e:
            _logger.error("Error in container autocomplete search: %s", str(e))
            return {"error": "Search failed", "suggestions": []}

    # ============================================================================
    # INTELLIGENT FILE SEARCH WITH CONTAINER RECOMMENDATIONS
    # ============================================================================

    @http.route(
        ["/records/search/recommend_containers"],
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def _search_recommend_containers_for_file(self, **kwargs):
        """
        Smart container recommendations based on file search criteria

        Parameters:
        - file_name: Name to search for (e.g., "John Doe")
        - service_date: Date to match against container date ranges
        - customer_id: Customer ID for filtering
        - content_type: Type of document being searched
        """
        start_time = time.time()
        recommendations = []

        try:
            # Extract and sanitize search parameters
            file_name = kwargs.get("file_name", "").strip()
            service_date = kwargs.get("service_date")
            customer_id = kwargs.get("customer_id")
            content_type = kwargs.get("content_type", "").strip()

            if not file_name and not service_date:
                return {
                    "recommendations": [],
                    "message": "Please provide file name or service date",
                    "total": 0
                }

            # Build base domain with better error handling
            domain = [("active", "=", True), ("state", "in", ["active", "stored"])]

            if customer_id:
                try:
                    customer_id = int(customer_id)
                    domain.append(("partner_id", "=", customer_id))
                except (ValueError, TypeError):
                    _logger.warning("Invalid customer_id in file search: %s", customer_id)
                    return {"error": "Invalid customer ID", "recommendations": []}

            # Apply department security
            domain = self._apply_department_security(domain)

            # Search containers using different criteria
            containers = request.env["records.container"].search(domain, limit=100)  # Reasonable limit for processing

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
                                "Name '%s' fits alphabetical range %s" % (
                                    file_name, container.alpha_range_display
                                )
                            )

                # 2. Date range matching with improved error handling
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
                                "Service date %s falls within container date range" %
                                search_date.strftime('%m/%d/%Y')
                            )
                    except (ValueError, TypeError) as e:
                        _logger.debug("Date parsing error in container search: %s", e)

                # 3. Content type matching (case-insensitive)
                if (
                    content_type
                    and container.primary_content_type
                    and container.primary_content_type.lower() == content_type.lower()
                ):
                    score += 30
                    reasons.append("Content type matches: %s" % content_type)

                # 4. Keyword matching in search_keywords - FIXED LOGIC
                if file_name and container.search_keywords:
                    keywords = container.search_keywords.lower()
                    file_name_lower = file_name.lower()

                    # Check for exact word matches (more precise than substring)
                    file_words = file_name_lower.split()
                    keyword_words = keywords.split()

                    matches = 0
                    for word in file_words:
                        if len(word) >= 3 and word in keyword_words:  # Only count words 3+ chars
                            matches += 1

                    if matches > 0:
                        score += 25 + (matches * 5)  # Bonus for multiple word matches
                        reasons.append("Found %d matching keywords in container" % matches)

                # 5. Content description matching with word boundary logic
                if file_name and container.content_description:
                    description_lower = container.content_description.lower()
                    file_name_lower = file_name.lower()

                    # Check for whole word matches first
                    file_words = file_name_lower.split()
                    desc_words = description_lower.split()

                    word_matches = sum(1 for word in file_words if len(word) >= 3 and word in desc_words)

                    if word_matches > 0:
                        score += 20 + (word_matches * 5)
                        reasons.append("Found %d matching words in description" % word_matches)
                    elif file_name_lower in description_lower:  # Fallback to substring
                        score += 15
                        reasons.append("File name found in content description")

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
                            "alpha_range": container.alpha_range_display or "",
                            "date_range": container.content_date_range_display or "",
                            "content_type": container.primary_content_type or "",
                            "document_count": container.document_count or 0,
                            "description": container.content_description or "",
                        }
                    )

            # Sort by score (highest first) and limit results
            recommendations.sort(key=lambda x: x["score"], reverse=True)

            # Log performance metrics
            duration_ms = (time.time() - start_time) * 1000
            search_monitor.log_query("container_recommendations", duration_ms, kwargs)

            return {
                "recommendations": recommendations[:15],  # Limit to top 15 suggestions
                "total": len(recommendations),
                "search_criteria": {
                    "file_name": file_name,
                    "service_date": service_date,
                    "content_type": content_type,
                },
            }

        except Exception as e:
            _logger.error("Error in container recommendations: %s", str(e))
            return {"error": "Recommendation search failed", "recommendations": []}

    # ============================================================================
    # PORTAL SEARCH INTEGRATION
    # ============================================================================

    @http.route(
        ["/my/records/search"], type="jsonrpc", auth="user", website=True, methods=["POST"]
    )
    def _search_portal_containers(self, **kwargs):
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
            return self._search_containers_autocomplete(
                query=query, customer_id=customer_id, limit=20
            )

        # File/content search - use intelligent recommendations
        kwargs["file_name"] = query
        return self._search_recommend_containers_for_file(**kwargs)

    # ============================================================================
    # FULL-TEXT SEARCH ACROSS CONTAINERS
    # ============================================================================

    @http.route(
        ["/records/search/fulltext"], type="jsonrpc", auth="user", methods=["POST"]
    )
    def _search_fulltext_containers(self, query="", customer_id=None, limit=20):
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
    # ============================================================================

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
        type="jsonrpc",
        auth="user",
        methods=["GET"],
    )
    def _search_config(self):
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
