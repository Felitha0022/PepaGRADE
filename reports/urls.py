from django.urls import path

from .views import (
    report_list,
    student_reports,
    report_detail,
    download_report,
)


urlpatterns = [

    # All reports
    path(
        '',
        report_list,
        name='report_list'
    ),

    # Reports belonging to one student
    path(
        'student/<int:student_id>/',
        student_reports,
        name='student_reports'
    ),

    # View one report
    path(
        '<int:report_id>/',
        report_detail,
        name='report_detail'
    ),

    # Download one report as PDF
    path(
        '<int:report_id>/download/',
        download_report,
        name='download_report'
    ),

]