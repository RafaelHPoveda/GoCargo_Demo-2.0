from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.views import APIView

from apps.shipments.presentation.serializers import (
    ShipmentDtoCreateSerializer,
    ShipmentDtoSerializer,
)
from config.dependencies import build_shipment_service
from core.presentation.responses import ApiResponse
from core.presentation.schema import ERROR_RESPONSES, response_schema


@extend_schema_view(
    get=extend_schema(
        operation_id="shipments_list",
        responses={**ERROR_RESPONSES, 200: response_schema(ShipmentDtoSerializer, many=True)},
    ),
    post=extend_schema(
        request=ShipmentDtoCreateSerializer,
        responses={**ERROR_RESPONSES, 201: response_schema(ShipmentDtoSerializer)},
    ),
)
class ShipmentAPIView(APIView):
    def get(self, request):
        result = build_shipment_service().get_all()
        return ApiResponse(ShipmentDtoSerializer(result, many=True).data)

    def post(self, request):
        serializer = ShipmentDtoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = build_shipment_service().create(serializer.validated_data)
        return ApiResponse(
            ShipmentDtoSerializer(result).data,
            http_code=status.HTTP_201_CREATED,
            success_messages=["Registro creado correctamente."],
        )


@extend_schema_view(
    get=extend_schema(responses={**ERROR_RESPONSES, 200: response_schema(ShipmentDtoSerializer)}),
)
class ShipmentDetailAPIView(APIView):
    def get(self, request, shipment_id):
        result = build_shipment_service().get_by_id(shipment_id)
        return ApiResponse(ShipmentDtoSerializer(result).data)
