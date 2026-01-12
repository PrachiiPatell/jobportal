from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
from .models import User

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = (user.email or "").lower().strip()

        # role
        user.role = form.cleaned_data["role"]
        if user.role == User.ROLE_EMPLOYER:
            user.company_name = (form.cleaned_data.get("company_name") or "").strip() or None

        user.save()
        messages.success(request, "Account created! Please login.")
        return redirect("login")

    return render(request, "auth/register.html", {"form": form})

class CustomLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = LoginForm

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, "Your account is deactivated. Contact admin.")
            return redirect("login")
        login(self.request, user)
        messages.success(self.request, "Logged in successfully.")
        return redirect("home")

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out.")
    return redirect("home")
