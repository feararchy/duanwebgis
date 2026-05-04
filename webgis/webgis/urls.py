from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve 

urlpatterns = [
    # ĐƯA DÒNG NÀY LÊN ĐẦU TIÊN
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    
    path('admin/', admin.site.urls),
    path('', include('nhomgis.urls')),
]

# Có thể giữ thêm đoạn này để chắc chắn
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)