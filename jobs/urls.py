from django.urls import path
from . import views

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("<int:job_id>/", views.job_detail, name="job_detail"),

    # employer
    path("employer/manage/", views.employer_manage, name="employer_manage"),
    path("employer/new/", views.job_create, name="job_create"),
    path("employer/<int:job_id>/edit/", views.job_edit, name="job_edit"),
    path("employer/<int:job_id>/delete/", views.job_delete, name="job_delete"),

    # seeker
    path("<int:job_id>/apply/", views.apply_job, name="apply_job"),
    path("applications/me/", views.my_applications, name="my_applications"),

    # in-app admin panel
    path("adminpanel/", views.admin_dashboard, name="admin_dashboard"),
    path("adminpanel/users/", views.admin_users, name="admin_users"),
    path("adminpanel/users/<int:user_id>/toggle/", views.admin_toggle_user, name="admin_toggle_user"),
    path("adminpanel/jobs/", views.admin_jobs, name="admin_jobs"),
    path("adminpanel/jobs/<int:job_id>/toggle/", views.admin_toggle_job, name="admin_toggle_job"),
    path("adminpanel/jobs/<int:job_id>/delete/", views.admin_delete_job, name="admin_delete_job"),
]
