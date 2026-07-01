from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.entities.urls')),
    path('sources/', include('apps.sources.urls')),
    path('documents/', include('apps.documents.urls')),
    path('extraction/', include('apps.extraction.urls')),
    path('assertions/', include('apps.assertions.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('research/', include('apps.research.urls')),
    path('exports/', include('apps.exports.urls')),
    path('government/', include('apps.government.urls')),
    path('projects/', include('apps.projects.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
