from functools import lru_cache

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


class ApiResponseSerializer(serializers.Serializer):
    isSuccess = serializers.BooleanField()
    errorMessages = serializers.ListField(child=serializers.CharField())
    successMessages = serializers.ListField(child=serializers.CharField())
    httpCode = serializers.IntegerField()
    data = serializers.JSONField(allow_null=True)
    meta = serializers.DictField()


@lru_cache(maxsize=None)
def response_schema(serializer_class, many=False):
    name = serializer_class.__name__.removesuffix("Serializer")
    name += "ListResponseSerializer" if many else "ResponseSerializer"
    envelope = type(
        name,
        (ApiResponseSerializer,),
        {
            "__module__": __name__,
            "data": serializer_class(many=many, allow_null=True),
        },
    )
    return extend_schema_serializer(many=False)(envelope)


ERROR_RESPONSES = {
    code: ApiResponseSerializer for code in (400, 401, 403, 404, 405, 409, 415, 422, 429, 500, 503)
}
