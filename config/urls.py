from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from django.urls import include, path
from templates.views import dashboard

from lecturers.views import landing_page

urlpatterns = [

    path(
        '',
        landing_page,
        name='landing_page'),
        
    path('admin/', admin.site.urls),

    path('', dashboard, name='dashboard'),

    path(
        'assignments/',
        include('assignments.urls')
    ),

    path(
        'assessment/',
        include('assessment.urls')
    ),

    path(
        'lecturer/',
        include('lecturers.urls')
    ),

    path(
        'students/',
        include('students.urls')
    ),

    path(
        'reports/',
        include('reports.urls')
    ),

]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )