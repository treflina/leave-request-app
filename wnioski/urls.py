from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog


urlpatterns = [
    path("admin/", admin.site.urls),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path("", include("applications.requests.urls")),
    path("", include("applications.users.urls")),
    path("", include("applications.sickleaves.urls")),
    path("", include("applications.home.urls")),
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

admin.site.site_header = "Pracownik MBP - Panel administracyjny"
admin.site.site_title = "Pracownik MBP - Panel administracyjny"
admin.site.index_title = "Panel administracyjny"
