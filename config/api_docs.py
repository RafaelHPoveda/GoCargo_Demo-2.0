from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_safe


@require_safe
def api_docs(request):
    return render(request, "api_docs.html", {"schema_url": reverse("openapi-schema")})
