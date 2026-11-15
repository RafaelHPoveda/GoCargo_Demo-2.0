from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.views import APIView

from apps.branches.presentation.serializers import (
    BranchDtoCreateSerializer,
    BranchDtoSerializer,
    BranchDtoUpdateSerializer,
)
from config.dependencies import build_branch_service
from core.presentation.responses import ApiResponse
from core.presentation.schema import ERROR_RESPONSES, response_schema


@extend_schema_view(
    get=extend_schema(
        operation_id="branches_list",
        responses={**ERROR_RESPONSES, 200: response_schema(BranchDtoSerializer, many=True)},
    ),
    post=extend_schema(
        request=BranchDtoCreateSerializer,
        responses={**ERROR_RESPONSES, 201: response_schema(BranchDtoSerializer)},
    ),
)
class BranchAPIView(APIView):
    def get(self, request):
        result = build_branch_service().get_all()
        return ApiResponse(BranchDtoSerializer(result, many=True).data)

    def post(self, request):
        serializer = BranchDtoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = build_branch_service().create(serializer.validated_data)
        return ApiResponse(
            BranchDtoSerializer(result).data,
            http_code=status.HTTP_201_CREATED,
            success_messages=["Registro creado correctamente."],
        )


@extend_schema_view(
    put=extend_schema(
        request=BranchDtoUpdateSerializer,
        responses={**ERROR_RESPONSES, 200: response_schema(BranchDtoSerializer)},
    ),
    patch=extend_schema(
        request=BranchDtoUpdateSerializer(partial=True),
        responses={**ERROR_RESPONSES, 200: response_schema(BranchDtoSerializer)},
    ),
)
class BranchUpdateAPIView(APIView):
    def put(self, request, branch_id):
        return self._update(request, branch_id, partial=False)

    def patch(self, request, branch_id):
        return self._update(request, branch_id, partial=True)

    def _update(self, request, branch_id, *, partial):
        serializer = BranchDtoUpdateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        result = build_branch_service().update(branch_id, serializer.validated_data)
        return ApiResponse(
            BranchDtoSerializer(result).data,
            success_messages=["Registro actualizado correctamente."],
        )
