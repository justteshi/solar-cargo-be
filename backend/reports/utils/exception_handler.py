from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import exception_handler
from rest_framework import status

def custom_exception_handler(exc, context):
    from rest_framework.views import exception_handler
    from rest_framework import status

    response = exception_handler(exc, context)

    if response is not None and response.status_code == status.HTTP_400_BAD_REQUEST:
        def flatten_errors(errors, prefix=""):
            messages = []
            for key, value in errors.items():
                if isinstance(value, list):
                    if len(value) == 1:
                        # Only one error -> no index
                        messages.append(f"{prefix}{key}: {value[0]}")
                    else:
                        # Multiple errors -> show index
                        for idx, msg in enumerate(value, start=1):
                            messages.append(f"{prefix}{key} {idx}: {msg}")
                elif isinstance(value, dict):
                    messages.extend(flatten_errors(value, f"{prefix}{key} "))
            return messages

        if isinstance(response.data, dict):
            flattened_messages = flatten_errors(response.data)
            response.data = {
                "message": "; ".join(flattened_messages)
            }

    return response
