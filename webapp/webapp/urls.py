from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
import os

# Path to references directory
REFERENCES_DIR = settings.BASE_DIR / ".." / "references"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("webapp.generator.urls")),
    # Serve reference files at /ref/
    re_path(r'^ref/(?P<path>.*)$', serve, {'document_root': REFERENCES_DIR}),
]
