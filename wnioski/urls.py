from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from two_factor import urls as two_factor_urls
from two_factor.admin import AdminSiteOTPRequired


otp_admin_site = AdminSiteOTPRequired(name="admin")
for model, model_admin in admin.site._registry.items():
    otp_admin_site.register(model, model_admin.__class__)

otp_admin_site.site_header = "Pracownik MBP - Panel administracyjny"
otp_admin_site.site_title = "Pracownik MBP - Panel administracyjny"
otp_admin_site.index_title = "Panel administracyjny"


urlpatterns = [
    path("admin/", otp_admin_site.urls),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path(
        "",
        include(
            (two_factor_urls.urlpatterns[0], "two_factor"),
            namespace="two_factor",
        ),
    ),
    path("", include("applications.requests.urls")),
    path("", include("applications.users.urls")),
    path("", include("applications.sickleaves.urls")),
    path("", include("applications.home.urls")),
    path("", include("applications.inbox.urls")),
    path(
        "reset_password/",
        auth_views.PasswordResetView.as_view(
            template_name="users/reset_password.html"
            ),
        name="reset_password",
    ),
    path(
        "reset_password_sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/reset_password_sent.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/reset.html"
            ),
        name="password_reset_confirm",
    ),
    path(
        "reset_password_complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/reset_password_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "manifest.json",
        TemplateView.as_view(
            template_name="manifest.json", content_type="application/json"
        ),
        name="manifest.json",
    ),
    path("webpush/", include("webpush.urls")),
    path(
        "sw.js",
        (
            TemplateView.as_view(
                template_name="sw.js",
                content_type="application/javascript",
            )
        ),
        name="serviceworker",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

