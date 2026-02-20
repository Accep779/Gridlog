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
                error_message = str(response.data['detail'])
            else:
                # Validation errors - return as string
                error_message = str(response.data)
        else:
            error_message = str(response.data)

        # Standardize response format
        response.data = {
            'error': error_message,
            'status_code': response.status_code
        }

    return response
