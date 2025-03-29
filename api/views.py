from django.http import StreamingHttpResponse, HttpResponseForbidden
import os


def stream_log(request):
    # if not request.user.is_superuser:
    #     return HttpResponseForbidden("Not allowed.")

    log_path = os.path.join("logs", "ip_address.log")

    def read_log():
        with open(log_path, "r") as f:
            for line in f:
                yield line

    return StreamingHttpResponse(read_log(), content_type="text/plain")
