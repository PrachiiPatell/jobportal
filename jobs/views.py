from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import User
from .models import Job, Application
from .forms import JobForm, ApplyForm

def role_required(*roles):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.role not in roles:
                return HttpResponseForbidden("Forbidden")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator

def home(request):
    latest = Job.objects.filter(is_active=True).order_by("-created_at")[:8]
    return render(request, "home.html", {"jobs": latest})

def job_list(request):
    jobs = Job.objects.filter(is_active=True).order_by("-created_at")

    q = (request.GET.get("q") or "").strip()
    location = (request.GET.get("location") or "").strip()
    category = (request.GET.get("category") or "").strip()
    company = (request.GET.get("company") or "").strip()
    min_salary = (request.GET.get("min_salary") or "").strip()

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(company__icontains=q) |
            Q(location__icontains=q)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if category:
        jobs = jobs.filter(category=category)
    if company:
        jobs = jobs.filter(company__icontains=company)
    if min_salary.isdigit():
        jobs = jobs.filter(salary__isnull=False, salary__gte=int(min_salary))

    return render(request, "jobs/list.html", {"jobs": jobs})

def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id, is_active=True)
    already_applied = False

    if request.user.is_authenticated and request.user.role == User.ROLE_SEEKER:
        already_applied = Application.objects.filter(job=job, applicant=request.user).exists()

    return render(request, "jobs/detail.html", {"job": job, "already_applied": already_applied})

@login_required
@role_required(User.ROLE_EMPLOYER, User.ROLE_ADMIN)
def employer_manage(request):
    if request.user.role == User.ROLE_ADMIN:
        jobs = Job.objects.all().order_by("-created_at")
    else:
        jobs = Job.objects.filter(employer=request.user).order_by("-created_at")
    return render(request, "jobs/employer_manage.html", {"jobs": jobs})

@login_required
@role_required(User.ROLE_EMPLOYER, User.ROLE_ADMIN)
def job_create(request):
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user
        if request.user.role == User.ROLE_EMPLOYER and request.user.company_name:
            job.company = request.user.company_name
        job.save()
        messages.success(request, "Job posted successfully.")
        return redirect("employer_manage")
    return render(request, "jobs/job_form.html", {"form": form, "mode": "create"})

@login_required
@role_required(User.ROLE_EMPLOYER, User.ROLE_ADMIN)
def job_edit(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.user.role != User.ROLE_ADMIN and job.employer != request.user:
        return HttpResponseForbidden("Forbidden")

    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Job updated.")
        return redirect("employer_manage")
    return render(request, "jobs/job_form.html", {"form": form, "mode": "edit", "job": job})

@login_required
@role_required(User.ROLE_EMPLOYER, User.ROLE_ADMIN)
def job_delete(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.user.role != User.ROLE_ADMIN and job.employer != request.user:
        return HttpResponseForbidden("Forbidden")

    if request.method == "POST":
        job.delete()
        messages.info(request, "Job deleted.")
    return redirect("employer_manage")

@login_required
@role_required(User.ROLE_SEEKER)
def apply_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id, is_active=True)
    if job.is_external and job.external_url:
        messages.info(request, "This job was imported from Arbeitnow. Please apply on the source website.")
        return redirect(job.external_url)


    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, "You already applied for this job.")
        return redirect("job_detail", job_id=job.id)

    form = ApplyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        app = form.save(commit=False)
        app.job = job
        app.applicant = request.user
        app.save()
        messages.success(request, "Application submitted!")
        return redirect("my_applications")

    return render(request, "applications/apply.html", {"form": form, "job": job})

@login_required
@role_required(User.ROLE_SEEKER)
def my_applications(request):
    apps = Application.objects.filter(applicant=request.user).order_by("-created_at")
    return render(request, "applications/my_applications.html", {"applications": apps})

# -------- In-app Admin Panel (role=admin) --------
@login_required
@role_required(User.ROLE_ADMIN)
def admin_dashboard(request):
    return render(request, "adminpanel/dashboard.html", {
        "user_count": User.objects.count(),
        "job_count": Job.objects.count(),
        "active_jobs": Job.objects.filter(is_active=True).count(),
        "app_count": Application.objects.count(),
    })

@login_required
@role_required(User.ROLE_ADMIN)
def admin_users(request):
    users = User.objects.all().order_by("-date_joined")
    return render(request, "adminpanel/users.html", {"users": users})

@login_required
@role_required(User.ROLE_ADMIN)
def admin_toggle_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, pk=user_id)
        if user.id == request.user.id:
            messages.warning(request, "You cannot deactivate yourself.")
            return redirect("admin_users")
        user.is_active = not user.is_active
        user.save()
        messages.success(request, "User status updated.")
    return redirect("admin_users")

@login_required
@role_required(User.ROLE_ADMIN)
def admin_jobs(request):
    jobs = Job.objects.all().order_by("-created_at")
    return render(request, "adminpanel/jobs.html", {"jobs": jobs})

@login_required
@role_required(User.ROLE_ADMIN)
def admin_toggle_job(request, job_id):
    if request.method == "POST":
        job = get_object_or_404(Job, pk=job_id)
        job.is_active = not job.is_active
        job.save()
        messages.success(request, "Job status updated.")
    return redirect("admin_jobs")

@login_required
@role_required(User.ROLE_ADMIN)
def admin_delete_job(request, job_id):
    if request.method == "POST":
        job = get_object_or_404(Job, pk=job_id)
        job.delete()
        messages.info(request, "Job deleted.")
    return redirect("admin_jobs")
