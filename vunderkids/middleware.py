# middleware.py
import time

from django.http import HttpResponse
from logging import getLogger

logger = getLogger("ip-address")


class CheckIPAddressMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        endpoint = request.path
        if endpoint == "/api/logs/":
            return self.get_response(request)

        logger.info(f"IP Address: {ip}, Endpoint: {endpoint}")

        response = self.get_response(request)

        status_code = response.status_code
        logger.info(f"Status Code: {status_code}")

        return response
