from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("authentication.urls")),
    path("ops-104/", include("ops_104.urls")),
    path("ops-108/", include("ops_108.urls")),
    path('erc-104/', include('erc_104.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
