"""
URL configuration for scoring_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add a URL to urlpatterns:  path('', Home.as_view, name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import re

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('scoring.urls')),
]

# 开发环境下提供媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # 生产环境下也提供媒体文件服务（为了兼容性）
    # 注意：生产环境建议使用 Nginx 或其他 Web 服务器直接提供静态/媒体文件
    urlpatterns += [
        path(f'{settings.MEDIA_URL.lstrip("/")}<path:path>', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
