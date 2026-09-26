from django.utils.deprecation import MiddlewareMixin


class NoCacheAuthenticatedMiddleware(MiddlewareMixin):
    def process_response(self, request, response):

        if request.user.is_authenticated:
            content_type = response.get("Content-Type", "")

            if not content_type.startswith(
                ("text/html", "application/json")
            ):
                return response

            response["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response