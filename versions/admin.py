from django.contrib import admin
from django.core.management import call_command

from django.http import HttpResponseRedirect
from django.urls import path

from . import models


class VersionFileInline(admin.StackedInline):
    model = models.VersionFile
    autocomplete_fields = ("version",)
    verbose_name = "VersionFile"
    verbose_name_plural = "VersionFiles"
    extra = 0


@admin.register(models.Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ["name", "release_date", "active"]
    list_filter = ["active"]
    ordering = ["-release_date", "-name"]
    search_fields = ["name", "description"]
    date_hierarchy = "release_date"
    inlines = [VersionFileInline]
    change_list_template = "admin/version_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("new_versions/", self.import_new_releases, name="import_new_releases"),
        ]
        return my_urls + urls

    def import_new_releases(self, request):
        call_command("import_versions", "--new")
        self.message_user(
            request,
            """
            New releases are being imported. If you don't see any new releases,
            please refresh this page or check the logs.
        """,
        )
        return HttpResponseRedirect("../")
