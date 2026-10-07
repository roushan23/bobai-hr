"""Run through manage.py shell; verify the local foundation without retaining HR data."""

import json
import re
import secrets
from urllib.request import urlopen

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.db import connection, transaction
from django.test import Client
from django.urls import get_resolver, reverse

from base.models import Company, Department, JobPosition
from employee.models import Employee


def require(condition, description):
    if not condition:
        raise AssertionError(description)
    print("PASS:", description)


require(connection.vendor == "postgresql", "Django uses PostgreSQL")
require(settings.SETTINGS_MODULE == "bobai.settings", "BOBAI settings are active")
require(finders.find(settings.BRAND_LOGO), "Supplied logo is discoverable")
require(apps.is_installed("geofencing") and apps.is_installed("facedetection"),
        "Upstream API integration apps remain installed")
# Load URL registrations just as the real web server does.
get_resolver().url_patterns
processors = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
require(all(name in processors for name in (
    "payroll.context_processors.default_currency",
    "biometric.context_processors.biometric_is_installed",
    "horilla_audit.context_processors.history_form",
)), "Upstream payroll, biometric and audit context processors remain registered")

for endpoint in ("health", "ready"):
    with urlopen(f"http://localhost:8000/{endpoint}/", timeout=20) as response:
        payload = json.load(response)
    require(payload["status"] == "ok", f"HTTP /{endpoint}/ is healthy")
    if endpoint == "ready":
        require(all(payload.get(name) == "ok" for name in ("database", "cache", "scheduler")),
                "PostgreSQL, Redis and scheduler are ready")

with urlopen("http://localhost:8000/static/bobai/images/logo.png", timeout=20) as response:
    require(response.read(8) == b"\x89PNG\r\n\x1a\n", "Logo is served as PNG over HTTP")
with urlopen("http://localhost:8000/static/bobai/manifest.json", timeout=20) as response:
    require(json.load(response)["name"] == "BOBAI HR", "Application manifest is branded")

# The transaction covers users, employees, company data, sessions and any signals.
# Roll back even on an assertion failure. Existing local HR data is untouched.
with transaction.atomic():
    try:
        client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
        response = client.get(reverse("login"))
        require(response.status_code == 200 and b"BOBAI HR" in response.content,
                "Login page renders BOBAI HR")
        require(b"/static/bobai/images/logo.png" in response.content,
                "Login page references supplied logo")
        reset = client.get(reverse("reset-send-success"))
        require(reset.status_code == 200 and b"BOBAI HR" in reset.content,
                "Password reset confirmation is branded")
        csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)
        blocked = client.post(reverse("login"), {"username": "csrf-probe", "password": "unused"})
        require(blocked.status_code == 403, "Login still enforces CSRF protection")

        if not get_user_model().objects.exists():
            setup = client.get(reverse("initialize-database"))
            require(setup.status_code == 200 and b"BOBAI HR" in setup.content,
                    "Empty database setup wizard renders BOBAI HR")
            verified = client.post(reverse("initialize-database"),
                                   {"password": settings.DB_INIT_PASSWORD, "csrfmiddlewaretoken": csrf})
            require(verified.status_code == 302 and client.session.get("db_init_verified"),
                    "Existing database setup password flow works")
            signup = client.get(reverse("initialize-database-user"), HTTP_HX_REQUEST="true")
            require(signup.status_code == 200 and b"BOBAI HR" in signup.content,
                    "Administrator signup step renders")

        suffix = secrets.token_hex(5)
        username = "foundation-check-" + suffix
        password = secrets.token_urlsafe(24)
        user = get_user_model().objects.create_superuser(username=username,
                                                        email=username + "@example.test", password=password)
        company = Company.objects.create(company="Foundation Check " + suffix, hq=True,
                                         address="Local verification", country="India", state="Delhi",
                                         city="Delhi", zip="110001")
        department = Department.objects.create(department="Foundation Check " + suffix)
        department.company_id.set([company])
        position = JobPosition.objects.create(job_position="Foundation Check " + suffix, department_id=department)
        employee = Employee.objects.create(employee_user_id=user, employee_first_name="Foundation",
                                           employee_last_name="Check", email=user.email, phone="9999999999",
                                           badge_id="VERIFY-" + suffix)
        work_info = employee.employee_work_info
        work_info.company_id = company
        work_info.department_id = department
        work_info.job_position_id = position
        work_info.save()

        response = client.get(reverse("login"))
        csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)
        response = client.post(reverse("login"), {"username": username, "password": password,
                                                  "csrfmiddlewaretoken": csrf})
        require(response.status_code == 302 and client.session.get("_auth_user_id") == str(user.pk),
                "Administrator can sign in through the real login view")

        for name in ("home-page", "employee-view", "attendance-view", "recruitment-view", "asset-category-view", "view-contract", "type-view"):
            response = client.get(reverse(name), follow=True)
            require(response.status_code == 200, f"Authenticated core page {name} renders")
            require(response.wsgi_request.user.is_authenticated,
                    f"Core page {name} remains authenticated")
        response = client.get(reverse("admin:index"))
        require(response.status_code == 200 and b"BOBAI HR" in response.content,
                "Django admin renders BOBAI HR")
    finally:
        transaction.set_rollback(True)

require(not get_user_model().objects.filter(username=username).exists(),
        "Temporary verification account was rolled back")
print("BOBAI HR foundation verification passed.")
