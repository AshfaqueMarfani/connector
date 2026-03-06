"""
Custom exception handler for DRF.
Provides consistent error response formatting across all API endpoints.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    """
    Custom exception handler that:
    1. Converts Django ValidationErrors to DRF ValidationErrors.
    2. Wraps all error responses in a consistent JSON format.
    3. Logs server errors for debugging.
    """
    # Convert Django ValidationError to DRF ValidationError
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            exc = DRFValidationError(detail=exc.message_dict)
        else:
            exc = DRFValidationError(detail=exc.messages)

    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            "success": False,
            "status_code": response.status_code,
            "errors": response.data,
        }
        response.data = custom_response_data
    else:
        # Unhandled exception — log it and return a generic 500
        logger.exception(
            "Unhandled exception in %s",
            context.get("view", "unknown view"),
            exc_info=exc,
        )
        response = Response(
            {
                "success": False,
                "status_code": 500,
                "errors": {"detail": "An unexpected error occurred. Please try again later."},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
