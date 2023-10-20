import structlog

from django.views.generic import DetailView
from django.views.generic.edit import FormMixin
from django.shortcuts import redirect
from django.contrib import messages
from itertools import groupby
from operator import attrgetter

from libraries.forms import VersionSelectionForm
from versions.models import Version

logger = structlog.get_logger(__name__)


class VersionDetail(FormMixin, DetailView):
    """Web display of list of Versions"""

    form_class = VersionSelectionForm
    model = Version
    queryset = Version.objects.active().defer("data")
    template_name = "versions/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        obj = self.get_object()

        # Handle the case where no data has been uploaded
        if not obj:
            messages.add_message(
                self.request,
                messages.WARNING,
                "No data has been imported yet. Please check back later.",
            )
            context["versions"] = None
            context["downloads"] = None
            context["current_release"] = None
            context["is_current_release"] = False
            return context

        context["versions"] = Version.objects.version_dropdown()
        downloads = obj.downloads.all().order_by("operating_system")
        context["downloads"] = {
            k: list(v)
            for k, v in groupby(downloads, key=attrgetter("operating_system"))
        }
        current_release = Version.objects.most_recent()
        context["current_release"] = current_release
        obj = self.get_object()
        is_current_release = bool(current_release == obj)
        context["is_current_release"] = is_current_release

        context["heading"] = self.get_version_heading(obj, is_current_release)

        return context

    def get_version_heading(self, obj, is_current_release):
        """Returns the heading of the versions template"""
        heading = "Release"

        if is_current_release:
            heading = f"Newest {heading}"
        elif all([not is_current_release, obj.beta]):
            heading = f"Beta {heading}"
        elif not is_current_release:
            heading = f"Prior {heading}"

        return heading

    def post(self, request, *args, **kwargs):
        """User has submitted a form and will be redirected to the right record."""
        form = self.get_form()
        if form.is_valid():
            version = form.cleaned_data["version"]
            return redirect(
                "release-detail",
                slug=version.slug,
            )
        else:
            logger.info("version_detail_invalid_version")
        return super().get(request)


class VersionCurrentReleaseDetail(VersionDetail):
    """Web display of list of Versions"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["is_current_release"] = True
        return context

    def get_object(self):
        return Version.objects.most_recent()
