from django.contrib import admin
from django.urls import path, include

# 2 dòng này dùng để cấu hình thư mục ảnh Media
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Nối vào các đường link trong app nhomgis của bạn
    path('', include('nhomgis.urls')), 
]

# ĐOẠN LỆNH QUAN TRỌNG NHẤT ĐỂ HIỂN THỊ ẢNH
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)