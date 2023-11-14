# -*- coding: utf-8 -*-

""" A Pyramid app that demonstrates various Deform widgets and
capabilities and which provides a functional test suite  """

import inspect
import logging
import sys

import colander
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_locale_name
from pyramid.renderers import get_renderer
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.view import view_defaults

import deform
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


log = logging.getLogger(__name__)
_ = TranslationStringFactory("unofficial-deformdemo")

formatter = HtmlFormatter(nowrap=True)
css = formatter.get_style_defs()

# the zpt_renderer above is referred to within the demo.ini file by dotted name


class demonstrate(object):
    def __init__(self, title):
        self.title = title

    def __call__(self, method):
        method.demo = self.title
        return method


@view_defaults(route_name="unofficial-deformdemo")
class UnofficialDeformDemo(object):
    def __init__(self, request):
        self.request = request
        self.macros = get_renderer("templates/main.pt").implementation().macros

    def render_form(
        self,
        form,
        appstruct=colander.null,
        submitted="submit",
        success=None,
        readonly=False,
        is_i18n=False,
    ):

        captured = None
        output = None

        if submitted in self.request.POST:
            # the request represents a form submission
            try:
                # try to validate the submitted values
                controls = self.request.POST.items()
                captured = form.validate(controls)
                output = captured["text"]
                output = highlight(output, PythonLexer(), formatter)

                if success:
                    response = success()
                    if response is not None:
                        return response
                html = form.render(captured)
            except deform.ValidationFailure as e:
                # the submitted values could not be validated
                html = e.render()

        else:
            # the request requires a simple form rendering
            html = form.render(appstruct, readonly=readonly)

        if self.request.is_xhr:
            return Response(html)

        code, start, end = self.get_code(2)
        locale_name = get_locale_name(self.request)

        reqts = form.get_widget_resources()

        # values passed to template for rendering
        return {
            "form": html,
            "captured": output,
            "code": code,
            "start": start,
            "end": end,
            "is_i18n": is_i18n,
            "locale": locale_name,
            "demos": self.get_demos(),
            "title": self.get_title(),
            "css_links": reqts["css"],
            "js_links": reqts["js"],
        }

    def get_code(self, level):
        frame = sys._getframe(level)
        lines, start = inspect.getsourcelines(frame.f_code)
        end = start + len(lines)
        code = "".join(lines)
        return highlight(code, PythonLexer(), formatter), start, end

    @view_config(name="allcode",
                 renderer="templates/code.pt",
                 route_name="unofficial-deformdemo")
    def allcode(self):
        params = self.request.params
        start = params.get("start")
        end = params.get("end")
        hl_lines = None
        if start and end:
            start = int(start)
            end = int(end)
            hl_lines = list(range(start, end))
        code = open(inspect.getsourcefile(self.__class__), "r").read()
        code = code.encode("utf-8")
        formatter = HtmlFormatter(
            linenos="table",
            lineanchors="line",
            cssclass="hightlight ",
            hl_lines=hl_lines,
        )
        html = highlight(code, PythonLexer(), formatter)
        return {"code": html, "demos": self.get_demos()}

    def get_title(self):
        # gross hack; avert your eyes
        frame = sys._getframe(3)
        attr = frame.f_locals["attr"]
        inst = frame.f_locals["inst"]
        method = getattr(inst, attr)
        return method.demo

    @view_config(name="pygments.css", route_name="unofficial-deformdemo")
    def cssview(self):
        response = Response(body=css, content_type="text/css")
        response.cache_expires = 360
        return response

    @view_config(renderer="templates/index.pt",
                 route_name="unofficial-deformdemo")
    def index(self):
        return {"demos": self.get_demos()}

    def get_demos(self):
        def predicate(value):
            if getattr(value, "demo", None) is not None:
                return True

        demos = inspect.getmembers(self, predicate)
        L = []
        for name, method in demos:
            url = self.request.resource_url(
                self.request.root, name, route_name="unofficial-deformdemo"
            )
            L.append((method.demo, url))
        L.sort()
        return L

    # Unofficial Deform Demo Forms Start Here.

    @view_config(name="textinput",
                 renderer="templates/form.pt",
                 route_name="unofficial-deformdemo")
    @demonstrate("Text Input Widget")
    def textinput(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextInputWidget(),
                description="Enter some text (python will be highlighted)",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)


def includeme(config):

    config.scan("unofficial-deformdemo")
