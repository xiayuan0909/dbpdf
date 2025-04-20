from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
import os
from django.conf import settings

urlpatterns = [
    path('', include('myapp.urls')),
    path('admin/', admin.site.urls),
    # 只保留 uploads 的文件服务
    re_path(r'^uploads/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'uploads')
    }),
    # 添加 media 文件服务
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'media')
    }),
]