from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import exception_handler
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call the default exception handler first
    response = exception_handler(exc, context)

    # If the exception is a validation error, modify the response format
    if response is not None and response.status_code == status.HTTP_400_BAD_REQUEST:
        # Flatten the error messages into a single string
        def flatten_errors(errors, prefix=""):
            messages = []
            for key, value in errors.items():
                if isinstance(value, list):
                    for idx, msg in enumerate(value):
                        messages.append(f"{prefix}{key+1} : {msg}")
                elif isinstance(value, dict):
                    messages.extend(flatten_errors(value, f"{prefix}{key} "))
            return messages

        if isinstance(response.data, dict):
            flattened_messages = flatten_errors(response.data)
            response.data = {
                "message": "; ".join(flattened_messages)  # Add a semicolon as the delimiter
            }

    return response