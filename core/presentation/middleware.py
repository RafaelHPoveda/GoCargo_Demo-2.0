import json

from core.presentation.responses import ApiResponse, ApiResponseDto


class ApiErrorContractMiddleware:
    """Normaliza errores de rutas Django que no alcanzan una vista DRF."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            not request.path.startswith("/api/")
            or request.path.startswith(("/api/docs/", "/api/schema/"))
            or response.status_code < 400
            or isinstance(response, ApiResponse)
        ):
            return response
        messages = {
            400: "Solicitud invalida.",
            403: "Acceso denegado.",
            404: "Ruta no encontrada.",
            500: "Ocurrio un error interno del servidor.",
        }
        contract = ApiResponseDto(
            http_code=response.status_code,
            error_messages=[messages.get(response.status_code, response.reason_phrase)],
            meta={"errorCode": "http_error"},
        )
        response.content = json.dumps(contract.to_dict(), ensure_ascii=False).encode("utf-8")
        response["Content-Type"] = "application/json"
        response["Content-Length"] = str(len(response.content))
        return response
