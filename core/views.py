import os.path
import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import TemplateView, View

from .boostrenderer import get_content_from_s3
from .markdown import process_md


class MarkdownTemplateView(TemplateView):
    template_name = "markdown_template.html"
    content_dir = settings.BASE_CONTENT

    def build_path(self):
        """
        Builds the path from URL kwargs
        """
        content_path = self.kwargs.get("content_path")

        if not content_path:
            return

        # If the request includes the file extension, return that
        if content_path[-5:] == ".html" or content_path[-3:] == ".md":
            return f"{self.content_dir}/{content_path}"

        # Trim any trailing slashes
        if content_path[-1] == "/":
            content_path = content_path[:-1]

        # Can we find a markdown file with this path?
        path = f"{self.content_dir}/{content_path}.md"

        # Note: The get() method also checks isfile(), but since we need to try multiple
        # paths/extensions, we need to call it here as well.
        if os.path.isfile(path):
            return path

        # Can we find an HTML file with this path?
        path = f"{self.content_dir}/{content_path}.html"
        if os.path.isfile(path):
            return path

        # Can we find an index file with this path?
        path = f"{self.content_dir}/{content_path}/index.html"
        if os.path.isfile(path):
            return path

        # If we get here, there is nothing else for us to try.
        return

    def get(self, request, *args, **kwargs):
        """
        Verifies the file and returns the frontmatter and content
        """
        path = self.build_path()

        # Avoids a TypeError from os.path.isfile if there is no path
        if not path:
            raise Http404("Page not found")

        if not os.path.isfile(path):
            raise Http404("Post not found")

        context = {}
        context["frontmatter"], context["content"] = process_md(path)
        return self.render_to_response(context)


class StaticContentTemplateView(View):
    def get(self, request, *args, **kwargs):
        """
        Verifies the file and returns the raw static content from S3
        mangling paths using the stage_static_config.json settings
        """
        print(kwargs.get("content_path"))
        result = get_content_from_s3(key=kwargs.get("content_path"))
        if not result:
            raise Http404("Page not found")

        content, content_type = result

        response = HttpResponse(content, content_type=content_type)
        return response
