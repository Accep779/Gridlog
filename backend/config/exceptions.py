from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Custom exception handler that standardizes error response format.
    All errors return: {"error": "message", "status_code": xxx}
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Get the error message
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                error_message = response.data['detail']
            else:
                # Validation errors - return the first error as string or the whole dict
                # E.g. {"email": ["This field is required."]} -> "Email: This field is required"
                error_message = response.data
        else:
            error_message = response.data

        # Standardize response format
        status_code = response.status_code
        code_map = {
            400: 'VALIDATION_ERROR',
            401: 'AUTHENTICATION_FAILED',
            403: 'PERMISSION_DENIED',
            404: 'NOT_FOUND',
            405: 'METHOD_NOT_ALLOWED',
            409: 'CONFLICT',
            429: 'THROTTLED',
            500: 'INTERNAL_ERROR',
        }
        response.data = {
            'error': error_message,
            'code': code_map.get(status_code, 'ERROR'),
            'status_code': status_code
        }

    return response
