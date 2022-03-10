"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from cimp import views
urlpatterns = [
    # path('admin/', admin.site.urls),
    path('captcha', views.获取验证码),
    path('login', views.登录),
    path('account', views.用户管理),
    path('account/<int:no>', views.单用户管理),
    path('news', views.校园新闻管理),
    path('news/<int:no>', views.单新闻管理),
    path('notice', views.校园通知管理),
    path('notice/<int:no>', views.单通知管理),
    path('articles', views.列出论文),
    path('article/<int:no>', views.单论文管理),
    path('teacherlist', views.列出教师),
    path('workstream', views.工作流管理),
    path('prethemeslist', views.获取待审批主题),
    path('prearticleslist', views.获取待审批论文),
    path('echarts', views.echarts图表接口),
    path('upload', views.upload),
]
