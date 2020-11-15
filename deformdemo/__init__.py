# -*- coding: utf-8 -*-

""" A Pyramid app that demonstrates various Deform widgets and
capabilities and which provides a functional test suite  """

import csv
import decimal
import inspect
import logging
import pprint
import random
import sys

import colander
from pyramid.config import Configurator
from pyramid.i18n import TranslationStringFactory
from pyramid.i18n import get_locale_name
from pyramid.i18n import get_localizer
from pyramid.renderers import get_renderer
from pyramid.response import Response
from pyramid.session import SignedCookieSessionFactory
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config
from pyramid.view import view_defaults

import deform
from deform.renderer import configure_zpt_renderer
from iso8601 import iso8601
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


log = logging.getLogger(__name__)

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


PY3 = sys.version_info[0] == 3
PY38MIN = sys.version_info[0] == 3 and sys.version_info[1] >= 8

if PY3:

    def unicode(val, encoding="utf-8"):
        return val


_ = TranslationStringFactory("deformdemo")

formatter = HtmlFormatter(nowrap=True)
css = formatter.get_style_defs()

# the zpt_renderer above is referred to within the demo.ini file by dotted name


class demonstrate(object):
    def __init__(self, title):
        self.title = title

    def __call__(self, method):
        method.demo = self.title
        return method


# Py2/Py3 compat
# http://stackoverflow.com/a/16888673/315168
# eliminate u''
def my_safe_repr(obj, context, maxlevels, level, sort_dicts=True):

    if type(obj) == unicode:
        obj = obj.encode("utf-8")

    # Python 3.8 changed the call signature of pprint._safe_repr.
    # by adding sort_dicts.
    if PY38MIN:
        return pprint._safe_repr(obj, context, maxlevels, level, sort_dicts)
    else:
        return pprint._safe_repr(obj, context, maxlevels, level)


@view_defaults(route_name="deformdemo")
class DeformDemo(object):
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

        if submitted in self.request.POST:
            # the request represents a form submission
            try:
                # try to validate the submitted values
                controls = self.request.POST.items()
                captured = form.validate(controls)
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

        printer = pprint.PrettyPrinter()
        printer.format = my_safe_repr
        output = printer.pformat(captured)
        captured = highlight(output, PythonLexer(), formatter)

        # values passed to template for rendering
        return {
            "form": html,
            "captured": captured,
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
        if not PY3:
            code = unicode(code, "utf-8")
        return highlight(code, PythonLexer(), formatter), start, end

    @view_config(name="thanks.html")
    def thanks(self):
        return Response(
            "<html><body><p>Thanks!</p><small>"
            '<a href="..">Up</a></small></body></html>'
        )

    @view_config(name="allcode", renderer="templates/code.pt")
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

    @view_config(name="pygments.css")
    def cssview(self):
        response = Response(body=css, content_type="text/css")
        response.cache_expires = 360
        return response

    @view_config(renderer="templates/index.pt")
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
                self.request.root, name, route_name="deformdemo"
            )
            L.append((method.demo, url))
        L.sort()
        return L

    @view_config(renderer="templates/form.pt", name="textinput")
    @demonstrate("Text Input Widget")
    def textinput(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextInputWidget(),
                description="Enter some text",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="textinput_with_html5")
    @demonstrate("Text Input Widget (with arbitrary HTML5 attributes)")
    def textinput_with_html5(self):
        class Schema(colander.Schema):
            hours_worked = colander.SchemaNode(
                colander.Decimal(),
                description="Enter number of hours worked",
                default=30.00,
                validator=colander.Range(min=0, max=decimal.Decimal("99.99")),
                widget=deform.widget.TextInputWidget(
                    attributes={
                        "type": "number",
                        "inputmode": "decimal",
                        "step": "0.01",
                        "min": "0",
                        "max": "99.99",
                    }
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="textinput_with_css_class")
    @demonstrate("Text Input Widget (with CSS class)")
    def textinput_with_css_class(self):

        css_widget = deform.widget.TextInputWidget(
            css_class="deform-widget-with-style"
        )

        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=css_widget,
                description="Enter some text",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="textinput_readonly")
    @demonstrate("Text Input Widget (read-only)")
    def textinput_readonly(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"text": "text"})

    @view_config(renderer="templates/form.pt", name="money_input")
    @demonstrate("Money Input")
    def money_input(self):

        widget = deform.widget.MoneyInputWidget(options={"allowZero": True})

        class Schema(colander.Schema):
            greenbacks = colander.SchemaNode(
                colander.Decimal(),
                widget=widget,
                description="Enter some money",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="autocomplete_input")
    @demonstrate("Autocomplete Input Widget")
    def autocomplete_input(self):
        choices = ["bar", "baz", "two", "three", "foo & bar", "one < two"]
        widget = deform.widget.AutocompleteInputWidget(
            values=choices, min_length=1
        )

        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=widget,
                description='Enter some text (Hint: try "b" or "t")',
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="autocomplete_remote_input"
    )
    @demonstrate("Autocomplete Input Widget (with Remote Data Source)")
    def autocomplete_remote_input(self):

        widget = deform.widget.AutocompleteInputWidget(
            min_length=1,
            values=self.request.route_path(
                "deformdemo", traverse=("autocomplete_input_values",)
            ),
        )

        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=widget,
                description='Enter some text (Hint: try "b" or "t")',
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="json", name="autocomplete_input_values")
    def autocomplete_input_values(self):
        text = self.request.params.get("term", "")
        return [
            x
            for x in ["bar", "baz", "two", "three", "foo & bar", "one < two"]
            if x.startswith(text)
        ]

    @view_config(renderer="templates/form.pt", name="textarea")
    @demonstrate("Text Area Widget")
    def textarea(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextAreaWidget(rows=10, cols=60),
                description="Enter some text",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="textarea_readonly")
    @demonstrate("Text Area Widget (read-only)")
    def textarea_readonly(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextAreaWidget(readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"text": "text"})

    @view_config(renderer="templates/form.pt", name="richtext")
    @demonstrate("Rich Text Widget (TinyMCE)")
    def richtext(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                # These options are directly passed to underylying TinyMCE as
                # browser_spellcheck : true
                # See https://www.tinymce.com/docs/configure/
                widget=deform.widget.RichTextWidget(
                    options=(("browser_spellcheck", True),)
                ),
                description="Enter some text",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="richtext_i18n")
    @demonstrate("Rich Text Widget (internationalized)")
    def richtext_i18n(self):

        locale_name = get_locale_name(self.request)

        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RichTextWidget(),
                description=_("Enter some text"),
            )
            _LOCALE_ = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget(),
                default=locale_name,
            )

        schema = Schema()
        form = deform.Form(
            schema, buttons=[deform.Button("submit", _("Submit"))]
        )
        return self.render_form(form, is_i18n=True)

    @view_config(renderer="templates/form.pt", name="delayed_richtext")
    @demonstrate("Rich Text Widget (delayed)")
    def delayed_richtext(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RichTextWidget(delayed_load=True),
                description="Enter some text",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="richtext_readonly")
    @demonstrate("Rich Text Widget (read-only)")
    def richtext_readonly(self):
        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RichTextWidget(readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"text": "<p>Hi!</p>"})

    @view_config(renderer="templates/form.pt", name="password")
    @demonstrate("Password Widget")
    def password(self):
        class Schema(colander.Schema):
            password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5, max=100),
                widget=deform.widget.PasswordWidget(),
                description="Enter a password",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="password_redisplay")
    @demonstrate("Password Widget (redisplay on validation failure)")
    def password_redisplay(self):
        class Schema(colander.Schema):
            password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5, max=100),
                widget=deform.widget.PasswordWidget(redisplay=True),
                description="Enter a password",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkbox")
    @demonstrate("Checkbox Widget")
    def checkbox(self):
        class Schema(colander.Schema):
            want = colander.SchemaNode(
                colander.Boolean(),
                description="Check this box!",
                widget=deform.widget.CheckboxWidget(),
                title="I Want It!",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/popup_example.pt", name="popup")
    @demonstrate("Popup and retail rendering")
    def popup(self):
        """Render a page (``popup_example.pt``) that contains
        a specially styled form (``modal.pt``).

        .. note ::

            Pop up form templates are NOT supplied with Deform core.
            They are in the deformdemo package for demostration purposes.
            You can copy them to your own project and configure
            widget template paths.

        popup_example.pt contains the page HTML template.

        Javascript: The JavaScript logic to show and hide the pop up is
        in ``poup_example.pt``.
        We need to automatically open the pop up on a validation error.

        Template registration: See ``deformdemo.main`` how we register a
        template path ``custom_widgets`` where the custom form template lies.
        See also :ref:`templates` in Deform documentation for more information.

        Source code:

        https://github.com/Pylons/deformdemo/blob/master/deformdemo/templates/popup_example.pt

        https://github.com/Pylons/deformdemo/blob/master/deformdemo/custom_widgets/modal.pt
        """

        class Schema(colander.Schema):

            title = "Pop up example title"

            # Override default form.pt for rendering <form>
            widget = deform.widget.FormWidget(template="modal.pt")

            name = colander.SchemaNode(
                colander.String(), description="Enter your name (required)"
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        # CSS is used in <button> opener and JS code
        form.formid = "my-pop-up"

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkbox_with_label")
    @demonstrate("Checkbox Widget (with Label)")
    def checkbox_with_label(self):
        class Schema(colander.Schema):
            want = colander.SchemaNode(
                colander.Boolean(),
                description="Check this box!",
                widget=deform.widget.CheckboxWidget(),
                label="Really",
                title="I Want It!",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkbox_readonly")
    @demonstrate("Checkbox Widget (read-only)")
    def checkbox_readonly(self):
        class Schema(colander.Schema):
            want = colander.SchemaNode(
                colander.Boolean(),
                description="Check this box!",
                widget=deform.widget.CheckboxWidget(readonly=True),
                title="I Want It!",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"want": True})

    @view_config(renderer="templates/form.pt", name="radiochoice")
    @demonstrate("Radio Choice Widget")
    def radiochoice(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                title="Choose your pepper",
                description="Select a Pepper",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="radiochoice_inline")
    @demonstrate("Radio Choice Widget (inline)")
    def radiochoice_inline(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.RadioChoiceWidget(
                    values=choices, inline=True
                ),
                title="Choose your pepper",
                description="Select a Pepper",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="radiochoice_int")
    @demonstrate("Radio Choice Widget (with int values)")
    def radiochoice_int(self):
        choices = ((0, "Habanero"), (1, "Jalapeno"), (2, "Chipotle"))

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Int(),
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                title="Choose your pepper",
                description="Select a Pepper",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="radiochoice_readonly")
    @demonstrate("Radio Choice Widget (read-only)")
    def radiochoice_readonly(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RadioChoiceWidget(
                    values=choices, readonly=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"pepper": "jalapeno"})

    @view_config(renderer="templates/form.pt", name="checkedinput")
    @demonstrate("Checked Input Widget")
    def checkedinput(self):

        widget = deform.widget.CheckedInputWidget(
            subject="Email", confirm_subject="Confirm Email"
        )

        class Schema(colander.Schema):
            email = colander.SchemaNode(
                colander.String(),
                title="Email Address",
                description="Type your email address and confirm it",
                validator=colander.Email(),
                widget=widget,
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkedinput_readonly")
    @demonstrate("Checked Input Widget (read-only)")
    def checkedinput_readonly(self):

        widget = deform.widget.CheckedInputWidget(
            subject="Email", confirm_subject="Confirm Email", readonly=True
        )

        class Schema(colander.Schema):
            email = colander.SchemaNode(
                colander.String(),
                title="Email Address",
                description="Type your email address and confirm it",
                validator=colander.Email(),
                widget=widget,
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"email": "ww@graymatter.com"})

    @view_config(renderer="templates/form.pt", name="checkedpassword")
    @demonstrate("Checked Password Widget")
    def checkedpassword(self):
        class Schema(colander.Schema):
            password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5),
                widget=deform.widget.CheckedPasswordWidget(),
                description="Type your password and confirm it",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="checkedpassword_redisplay"
    )
    @demonstrate("Checked Password Widget (redisplay on validation failure)")
    def checkedpassword_redisplay(self):
        class Schema(colander.Schema):
            password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5),
                widget=deform.widget.CheckedPasswordWidget(redisplay=True),
                description="Type your password and confirm it",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkedpassword_readonly")
    @demonstrate("Checked Password Widget (read-only)")
    def checkedpassword_readonly(self):
        class Schema(colander.Schema):
            password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5),
                widget=deform.widget.CheckedPasswordWidget(readonly=True),
                description="Type your password and confirm it",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"password": "foo"})

    @view_config(renderer="templates/form.pt", name="checkedinput_withmask")
    @demonstrate("Checked Input Widget (with Input Mask)")
    def checkedinput_withmask(self):

        widget = deform.widget.CheckedInputWidget(
            subject="SSN",
            confirm_subject="Confirm SSN",
            mask="999-99-9999",
            mask_placeholder="#",
        )

        class Schema(colander.Schema):
            ssn = colander.SchemaNode(
                colander.String(),
                widget=widget,
                title="Social Security Number",
                description="Type your Social Security Number and confirm it",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="dynamic_field")
    @demonstrate("Dynamic fields: add and remove")
    def dynamic_field(self):
        class Schema(colander.Schema):

            field1 = colander.SchemaNode(
                colander.String(),
                title="Field 1",
                description="Add ?nofield1 to URL to delete this field",
            )

            field2 = colander.SchemaNode(
                colander.String(),
                title="Field 2",
                description="May or may not appear. Hit refresh.",
            )

            def after_bind(self, schema, kwargs):

                # after_bind() can be used as subclass method
                # or a parameter passed to schema constructor.
                #
                # When schema is bound you are free to post-process any fields:
                # Hide fields, change widgets or dynamically add more fields.
                # You can read request, request.session and other variables
                # here to fulfill conditions.
                #
                # More abount binding:
                #
                # http://docs.pylonsproject.org/projects/colander/en/latest/binding.html
                #
                # http://docs.pylonsproject.org/projects/colander/en/latest/binding.html#after-bind
                #

                request = kwargs["request"]

                if "nofield1" in request.params:
                    del self["field1"]

                if random.random() < 0.5:
                    del self["field2"]

                # Dynamically add new field
                self["field3"] = colander.SchemaNode(
                    colander.String(),
                    title="Field 3",
                    description="Dynamically created",
                )

        schema = Schema()
        schema = schema.bind(request=self.request)

        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="mapping")
    @demonstrate("Mapping Widget")
    def mapping(self):
        class Mapping(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                description="Content date",
            )

        class Schema(colander.Schema):
            number = colander.SchemaNode(colander.Integer())
            mapping = Mapping()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="mapping_accordion")
    @demonstrate("Accordion")
    def mapping_accordion(self):
        """A section of form can be hidden by using Bootstrap 3 accordions.

        On field errors accordions are always forced to open.

        See ``deform/static/form.css`` for chevron styling.

        http://getbootstrap.com/javascript/#collapse
        """

        class Mapping(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                description="Content date",
            )

        class Schema(colander.Schema):
            number = colander.SchemaNode(colander.Integer())

            mapping = Mapping(
                title="Open by default",
                widget=deform.widget.MappingWidget(
                    template="mapping_accordion", open=True
                ),
            )

            mapping2 = Mapping(
                title="Closed by default",
                widget=deform.widget.MappingWidget(
                    template="mapping_accordion", open=False
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="ajaxform")
    @demonstrate("AJAX form submission (inline success)")
    def ajaxform(self):
        class Mapping(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                description="Content date",
            )

        class Schema(colander.Schema):
            number = colander.SchemaNode(colander.Integer())
            mapping = Mapping()
            richtext = colander.SchemaNode(
                colander.String(), widget=deform.widget.RichTextWidget()
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",), use_ajax=True)

        def succeed():
            return Response('<div id="thanks">Thanks!</div>')

        return self.render_form(form, success=succeed)

    @view_config(renderer="templates/form.pt", name="ajaxform_redirect")
    @demonstrate("AJAX form submission (redirect on success)")
    def ajaxform_redirect(self):
        class Mapping(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                description="Content date",
            )

        class Schema(colander.Schema):
            number = colander.SchemaNode(colander.Integer())
            mapping = Mapping()

        schema = Schema()
        options = """
        {success:
          function (rText, sText, xhr, form) {
            var loc = xhr.getResponseHeader('X-Relocate');
            if (loc) {
              document.location = loc;
            };
           }
        }
        """

        def succeed():
            location = self.request.resource_url(
                self.request.root, "thanks.html", route_name="deformdemo"
            )
            # To appease jquery 1.6+, we need to return something that smells
            # like HTML, or we get a "Node cannot be inserted at the
            # specified point in the hierarchy" Javascript error.  This didn't
            # used to be required under JQuery 1.4.
            return Response(
                "<div>hurr</div>",
                headers=[
                    ("X-Relocate", location),
                    ("Content-Type", "text/html"),
                ],
            )

        form = deform.Form(
            schema, buttons=("submit",), use_ajax=True, ajax_options=options
        )

        return self.render_form(form, success=succeed)

    @view_config(renderer="templates/form.pt", name="sequence_of_radiochoices")
    @demonstrate("Sequence of Radio Choice Widgets")
    def sequence_of_radiochoices(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Peppers(colander.SequenceSchema):
            pepper = colander.SchemaNode(
                colander.String(),
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.RadioChoiceWidget(values=choices),
                title="Pepper Chooser",
                description="Select a Pepper",
            )

        class Schema(colander.Schema):
            peppers = Peppers()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="sequence_of_autocompletes"
    )
    @demonstrate("Sequence of Autocomplete Widgets")
    def sequence_of_autocompletes(self):
        choices = ["bar", "baz", "two", "three"]

        widget = deform.widget.AutocompleteInputWidget(values=choices)

        class Sequence(colander.SequenceSchema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=widget,
                description='Enter some text (Hint: try "b" or "t")',
            )

        class Schema(colander.Schema):
            texts = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="sequence_of_dateinputs")
    @demonstrate("Sequence of Date Inputs")
    def sequence_of_dateinputs(self):
        import datetime

        class Sequence(colander.SequenceSchema):
            date = colander.SchemaNode(
                colander.Date(),
                validator=colander.Range(
                    min=datetime.date(2010, 5, 5),
                    min_err=_("${val} is earlier than earliest date ${min}"),
                ),
            )

        class Schema(colander.Schema):
            dates = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="sequence_of_i18n")
    @demonstrate("Sequence of I18N")
    def sequence_of_i18n(self):
        import datetime

        locale_name = get_locale_name(self.request)

        class Sequence(colander.SequenceSchema):
            date = colander.SchemaNode(
                colander.Date(),
                title=_("Event date"),
                validator=colander.Range(
                    min=datetime.date(2010, 5, 5),
                    min_err=_("${val} is earlier than earliest date ${min}"),
                ),
            )

        class Schema(colander.Schema):
            dates = Sequence(title=_("Dates"))
            _LOCALE_ = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget(),
                default=locale_name,
            )

        schema = Schema()
        form = deform.Form(
            schema, buttons=[deform.Button("submit", _("Submit"))]
        )

        return self.render_form(form, is_i18n=True)

    @view_config(renderer="templates/form.pt", name="sequence_of_richtext")
    @demonstrate("Sequence of Rich Text Widgets")
    def sequence_of_richtext(self):
        class Sequence(colander.SequenceSchema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RichTextWidget(),
                description="Enter some text",
            )

        class Schema(colander.Schema):
            texts = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="sequence_of_masked_textinputs"
    )
    @demonstrate("Sequence of Masked Text Inputs")
    def sequence_of_masked_textinputs(self):
        class Sequence(colander.SequenceSchema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(mask="999-99-9999"),
            )

        class Schema(colander.Schema):
            texts = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="sequence_of_fileuploads")
    @demonstrate("Sequence of File Upload Widgets")
    def sequence_of_fileuploads(self):
        class Sequence(colander.SequenceSchema):
            upload = colander.SchemaNode(
                deform.FileData(),
                widget=deform.widget.FileUploadWidget(tmpstore),
            )

        class Schema(colander.Schema):
            uploads = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, success=tmpstore.clear)

    @view_config(
        renderer="templates/form.pt",
        name="sequence_of_fileuploads_with_initial_item",
    )
    @demonstrate("Sequence of File Upload Widgets (with Initial Item)")
    def sequence_of_fileuploads_with_initial_item(self):
        class Sequence(colander.SequenceSchema):
            upload = colander.SchemaNode(
                deform.FileData(),
                widget=deform.widget.FileUploadWidget(tmpstore),
            )

        class Schema(colander.Schema):
            uploads = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        form["uploads"].widget = deform.widget.SequenceWidget(min_len=1)

        return self.render_form(form, success=tmpstore.clear)

    @view_config(renderer="templates/form.pt", name="sequence_of_mappings")
    @demonstrate("Sequence of Mapping Widgets")
    def sequence_of_mappings(self):
        class Person(colander.Schema):
            name = colander.SchemaNode(colander.String())
            age = colander.SchemaNode(
                colander.Integer(), validator=colander.Range(0, 200)
            )

        class People(colander.SequenceSchema):
            person = Person()

        class Schema(colander.Schema):
            people = People()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt",
        name="sequence_of_mappings_with_initial_item",
    )
    @demonstrate("Sequence of Mapping Widgets (with Initial Item)")
    def sequence_of_mappings_with_initial_item(self):
        class Person(colander.Schema):
            name = colander.SchemaNode(colander.String())
            age = colander.SchemaNode(
                colander.Integer(), validator=colander.Range(0, 200)
            )

        class People(colander.SequenceSchema):
            person = Person()

        class Schema(colander.Schema):
            people = People()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        form["people"].widget = deform.widget.SequenceWidget(min_len=1)

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="readonly_sequence_of_mappings"
    )
    @demonstrate("Sequence of Mappings (read-only)")
    def readonly_sequence_of_mappings(self):
        class Person(colander.Schema):
            name = colander.SchemaNode(colander.String())
            age = colander.SchemaNode(
                colander.Integer(), validator=colander.Range(0, 200)
            )

        class People(colander.SequenceSchema):
            person = Person()

        class Schema(colander.Schema):
            people = People()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(
            form,
            appstruct={
                "people": [
                    {"name": "name1", "age": 23},
                    {"name": "name2", "age": 25},
                ]
            },
            readonly=True,
        )

    @view_config(renderer="templates/form.pt", name="sequence_of_sequences")
    @demonstrate("Sequence of Sequence Widgets")
    def sequence_of_sequences(self):
        class NameAndTitle(colander.Schema):
            name = colander.SchemaNode(colander.String())
            title = colander.SchemaNode(colander.String())

        class NamesAndTitles(colander.SequenceSchema):
            name_and_title = NameAndTitle(title="Name and Title")

        class NamesAndTitlesSequences(colander.SequenceSchema):
            names_and_titles = NamesAndTitles(title="Names and Titles")

        class Schema(colander.Schema):
            names_and_titles_sequence = NamesAndTitlesSequences(
                title="Sequence of Sequences of Names and Titles"
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        outer = form["names_and_titles_sequence"]
        outer.widget = deform.widget.SequenceWidget(min_len=1)
        outer["names_and_titles"].widget = deform.widget.SequenceWidget(
            min_len=1
        )

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="sequence_of_defaulted_selects"
    )
    @demonstrate("Sequence of Defaulted Selects")
    def sequence_of_defaulted_selects(self):
        # See https://github.com/Pylons/deform/pull/79
        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Peppers(colander.SequenceSchema):
            pepper = colander.SchemaNode(
                colander.String(),
                default="jalapeno",  # <--- raison d'etre
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.SelectWidget(values=choices),
                title="Pepper Chooser",
                description="Select a Pepper",
            )

        class Schema(colander.Schema):
            peppers = Peppers()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt",
        name="sequence_of_defaulted_selects_with_initial_item",
    )
    @demonstrate("Sequence of Defaulted Selects (with Initial Item)")
    def sequence_of_defaulted_selects_with_initial_item(self):
        # See https://github.com/Pylons/deformdemo/pull/15
        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Peppers(colander.SequenceSchema):
            pepper = colander.SchemaNode(
                colander.String(),
                default="jalapeno",
                validator=colander.OneOf([x[0] for x in choices]),
                widget=deform.widget.SelectWidget(values=choices),
                title="Pepper Chooser",
                description="Select a Pepper",
            )

        class Schema(colander.Schema):
            peppers = Peppers()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        # raison d'etre below (1-length sequence widget means initial item
        # rendered)
        form["peppers"].widget = deform.widget.SequenceWidget(min_len=1)

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="sequence_of_constrained_len"
    )
    @demonstrate("Sequence of Constrained Min and Max Lengths")
    def sequence_of_constrained_len(self):
        class Names(colander.SequenceSchema):
            name = colander.SchemaNode(colander.String())

        class Schema(colander.Schema):
            names = Names(
                validator=colander.Length(2, 4),
                title="At Least 2 At Most 4 Names",
                widget=deform.widget.SequenceWidget(min_len=2, max_len=4),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="sequence_orderable")
    @demonstrate("Sequence (of Mappings) with Ordering Enabled")
    def sequence_orderable(self):
        class Person(colander.Schema):
            name = colander.SchemaNode(colander.String())
            age = colander.SchemaNode(
                colander.Integer(), validator=colander.Range(0, 200)
            )

        class People(colander.SequenceSchema):
            person = Person()

        class Schema(colander.Schema):
            people = People(
                widget=deform.widget.SequenceWidget(orderable=True)
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="file")
    @demonstrate("File Upload Widget")
    def file(self):
        class Schema(colander.Schema):
            upload = colander.SchemaNode(
                deform.FileData(),
                widget=deform.widget.FileUploadWidget(tmpstore),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, success=tmpstore.clear)

    @view_config(renderer="templates/form.pt", name="file_readonly")
    @demonstrate("File Upload Widget (read-only)")
    def file_readonly(self):
        class Schema(colander.Schema):
            upload = colander.SchemaNode(
                deform.FileData(),
                widget=deform.widget.FileUploadWidget(tmpstore, readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        appstruct = {"upload": {"uid": "123", "filename": "leavesofgrass.png"}}

        return self.render_form(
            form, appstruct=appstruct, success=tmpstore.clear
        )

    @view_config(renderer="templates/form.pt", name="dateparts")
    @demonstrate("Date Parts Widget")
    def dateparts(self):
        import datetime

        class Schema(colander.Schema):
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                validator=colander.Range(
                    min=datetime.date(2010, 1, 1),
                    min_err=_("${val} is earlier than earliest date ${min}"),
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="dateparts_readonly")
    @demonstrate("Date Parts Widget (read-only)")
    def dateparts_readonly(self):
        import datetime

        class Schema(colander.Schema):
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(
            form, appstruct={"date": datetime.date(2010, 5, 5)}
        )

    @view_config(renderer="templates/form.pt", name="dateinput")
    @demonstrate("Date Input Widget")
    def dateinput(self):
        import datetime

        class Schema(colander.Schema):
            somedate = colander.SchemaNode(
                colander.Date(),
                validator=colander.Range(
                    min=datetime.date(datetime.date.today().year, 1, 1),
                    min_err=_("${val} is earlier than earliest date ${min}"),
                ),
                title="Date",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="timeinput")
    @demonstrate("Time Input")
    def timeinput(self):
        import datetime

        class Schema(colander.Schema):
            sometime = colander.SchemaNode(
                colander.Time(),
                validator=colander.Range(
                    min=datetime.time(12, 16),
                    min_err=_("${val} is earlier than earliest time ${min}"),
                ),
                title="Time",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="datetimeinput")
    @demonstrate("DateTime Input Widget")
    def datetimeinput(self):
        import datetime

        class Schema(colander.Schema):
            date_time = colander.SchemaNode(
                colander.DateTime(),
                validator=colander.Range(
                    min=datetime.datetime(
                        datetime.date.today().year,
                        1,
                        1,
                        12,
                        30,
                        tzinfo=iso8601.UTC,
                    ),
                    min_err=_(
                        "${val} is earlier than earliest datetime ${min}"
                    ),
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="datetimeinput_readonly")
    @demonstrate("DateTime Input Widget (read-only)")
    def datetimeinput_readonly(self):
        import datetime

        then = datetime.datetime(2011, 5, 5, 1, 2)

        class Schema(colander.Schema):
            date_time = colander.SchemaNode(
                colander.DateTime(),
                widget=deform.widget.DateTimeInputWidget(readonly=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct={"date_time": then})

    @view_config(renderer="templates/form.pt", name="edit")
    @demonstrate("Edit Form")
    def edit(self):
        import datetime

        class Mapping(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DatePartsWidget(),
                description="Content date",
            )

        class Schema(colander.Schema):
            number = colander.SchemaNode(colander.Integer())
            mapping = Mapping()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        # We don't need to supply all the values required by the schema
        # for an initial rendering, only the ones the app actually has
        # values for.  Notice below that we don't pass the ``name``
        # value specified by the ``Mapping`` schema.
        appstruct = {
            "number": 42,
            "mapping": {"date": datetime.date(2010, 4, 9)},
        }

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="interfield")
    @demonstrate("Inter-Field Validation")
    def interfield(self):
        class Schema(colander.Schema):
            name = colander.SchemaNode(
                colander.String(), description="Content name"
            )
            title = colander.SchemaNode(
                colander.String(),
                description="Content title (must start with content name)",
            )

        def validator(form, value):
            if not value["title"].startswith(value["name"]):
                exc = colander.Invalid(form, "Title must start with name")
                exc["title"] = "Must start with name %s" % value["name"]
                raise exc

        schema = Schema(validator=validator)
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="fielddefaults")
    @demonstrate("Field Defaults")
    def fielddefaults(self):
        class Schema(colander.Schema):
            artist = colander.SchemaNode(
                colander.String(), default="Grandaddy", description="Song name"
            )
            album = colander.SchemaNode(
                colander.String(), default="Just Like the Fambly Cat"
            )
            song = colander.SchemaNode(
                colander.String(), description="Song name"
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="nonrequiredfields")
    @demonstrate("Non-Required Fields")
    def nonrequiredfields(self):
        class Schema(colander.Schema):
            required = colander.SchemaNode(
                colander.String(), description="Required Field"
            )
            notrequired = colander.SchemaNode(
                colander.String(),
                missing=unicode(""),
                description="Unrequired Field",
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="nonrequired_number_fields"
    )
    @demonstrate("Non-Required Number Fields")
    def nonrequired_number_fields(self):
        class Schema(colander.Schema):
            required = colander.SchemaNode(
                colander.Int(), description="Required Field"
            )
            notrequired = colander.SchemaNode(
                colander.Float(), missing=0, description="Unrequired Field"
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="unicodeeverywhere")
    @demonstrate("Unicode Everywhere")
    def unicodeeverywhere(self):
        class Schema(colander.Schema):
            field = colander.SchemaNode(
                colander.String(),
                title=unicode("По оживлённым берегам", "utf-8"),
                description=unicode(
                    "子曰：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎？ " "人不知而不慍，不亦君子乎？」", "utf-8"
                ),
                default=unicode("☃", "utf-8"),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select")
    @demonstrate("Select Widget")
    def select(self):

        choices = (
            ("", "- Select -"),
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_size")
    @demonstrate("Select Widget (with size)")
    def select_with_size(self):

        choices = (
            ("", "- Select -"),
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(values=choices, size=2),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_unicode")
    @demonstrate("Select Widget (with unicode)")
    def select_with_unicode(self):

        choices = (
            ("", "- Select -"),
            (unicode("ハバネロ", "utf-8"), "Habanero"),
            (unicode("ハラペーニョ", "utf-8"), "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_default")
    @demonstrate("Select Widget (with default)")
    def select_with_default(self):

        choices = (
            ("", "- Select -"),
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                default="jalapeno",
                widget=deform.widget.SelectWidget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_multiple")
    @demonstrate("Select Widget (with multiple)")
    def select_with_multiple(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.SelectWidget(
                    values=choices, multiple=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt",
        name="select_with_multiple_default_integers",
    )
    @demonstrate("Select Widget (with multiple default integers)")
    def select_with_multiple_default_integers(self):

        choices = ((1, "Habanero"), (2, "Jalapeno"), (3, "Chipotle"))

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                default=[1, 2],
                widget=deform.widget.SelectWidget(
                    values=choices, multiple=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_deferred")
    @demonstrate("Select Widget (with deferred choices and default)")
    def select_with_deferred(self):
        @colander.deferred
        def deferred_choices_widget(node, kw):
            choices = kw.get("choices")
            return deform.widget.SelectWidget(values=choices)

        @colander.deferred
        def deferred_default(node, kw):
            return kw["default"]

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                default=deferred_default,
                widget=deferred_choices_widget,
            )

        choices = (
            ("", "- Select -"),
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        schema = Schema().bind(choices=choices, default="jalapeno")
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_integer")
    @demonstrate("Select Widget (with Integer values)")
    def select_integer(self):

        choices = (("", "- Select -"), (0, "Zero"), (1, "One"), (2, "Two"))

        class Schema(colander.Schema):
            number = colander.SchemaNode(
                colander.Integer(),
                widget=deform.widget.SelectWidget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_with_optgroup")
    @demonstrate("Select Widget (with optgroup)")
    def select_with_optgroup(self):
        from deform.widget import OptGroup

        choices = (
            ("", "Select your favorite musician"),
            OptGroup(
                "Guitarists",
                ("page", "Jimmy Page"),
                ("hendrix", "Jimi Hendrix"),
            ),
            OptGroup(
                "Drummers",
                ("cobham", "Billy Cobham"),
                ("bonham", "John Bonham"),
            ),
        )

        class Schema(colander.Schema):
            musician = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt",
        name="select_with_optgroup_and_label_attributes",
    )
    @demonstrate("Select Widget (with optgroup and label attributes)")
    def select_with_optgroup_and_label_attributes(self):

        # One may or may not notice any difference with
        # 'select_with_optgroup' above, depending on the browser being
        # used. See widget's documentation for further details.
        from deform.widget import OptGroup

        choices = (
            ("", "Select your favorite musician"),
            OptGroup(
                "Guitarists",
                ("page", "Jimmy Page"),
                ("hendrix", "Jimi Hendrix"),
            ),
            OptGroup(
                "Drummers",
                ("cobham", "Billy Cobham"),
                ("bonham", "John Bonham"),
            ),
        )

        long_label_gener = lambda group, label: " - ".join(  # noQA
            (group, label)
        )

        class Schema(colander.Schema):
            musician = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(
                    values=choices, long_label_generator=long_label_gener
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select_readonly")
    @demonstrate("Select Widget (read-only)")
    def select_readonly(self):
        from deform.widget import OptGroup

        choices = (
            ("", "Select your favorite musician"),
            OptGroup(
                "Guitarists",
                ("page", "Jimmy Page"),
                ("hendrix", "Jimi Hendrix"),
            ),
            OptGroup(
                "Drummers",
                ("cobham", "Billy Cobham"),
                ("bonham", "John Bonham"),
            ),
        )

        class Schema(colander.Schema):
            musician = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(
                    values=choices, readonly=True
                ),
            )
            multiple_musicians = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.SelectWidget(
                    values=choices, multiple=True, readonly=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        appstruct = {
            "musician": "cobham",
            "multiple_musicians": ["cobham", "page"],
        }

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="select2")
    @demonstrate("Select2 Widget")
    def select2(self):

        choices = (
            ("", "- Select -"),
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.Select2Widget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select2_with_multiple")
    @demonstrate("Select2 Widget (with multiple)")
    def select2_with_multiple(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.Select2Widget(
                    values=choices, multiple=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select2_with_optgroup")
    @demonstrate("Select2 Widget (with optgroup)")
    def select2_with_optgroup(self):
        from deform.widget import OptGroup

        choices = (
            ("", "Select your favorite musician"),
            OptGroup(
                "Guitarists",
                ("page", "Jimmy Page"),
                ("hendrix", "Jimi Hendrix"),
            ),
            OptGroup(
                "Drummers",
                ("cobham", "Billy Cobham"),
                ("bonham", "John Bonham"),
            ),
        )

        class Schema(colander.Schema):
            musician = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.Select2Widget(values=choices),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="select2_with_tags")
    @demonstrate("Select2 Widget (with tags)")
    def select2_with_tags(self):

        choices = ()

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.Select2Widget(values=choices, tags=True),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="select2_with_tags_and_multiple"
    )
    @demonstrate("Select2 Widget (with tags and multiple)")
    def select2_with_tags_and_multiple(self):

        choices = ()

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.Select2Widget(
                    values=choices, multiple=True, tags=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkboxchoice")
    @demonstrate("Checkbox Choice Widget")
    def checkboxchoice(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.CheckboxChoiceWidget(values=choices),
                validator=colander.Length(min=1),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkboxchoice_inline")
    @demonstrate("Checkbox Choice Widget (inline)")
    def checkboxchoice_inline(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.CheckboxChoiceWidget(
                    values=choices, inline=True
                ),
                validator=colander.Length(min=1),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkboxchoice2")
    @demonstrate("Checkbox Choice Widget (with required field)")
    def checkboxchoice2(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        @colander.deferred
        def deferred_checkbox_widget(node, kw):
            return deform.widget.CheckboxChoiceWidget(values=choices)

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(), widget=deferred_checkbox_widget
            )
            required = colander.SchemaNode(colander.String())

        schema = Schema()
        schema = schema.bind()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="checkboxchoice_readonly")
    @demonstrate("Checkbox Choice Widget (read-only)")
    def checkboxchoice_readonly(self):

        choices = (
            ("habanero", "Habanero"),
            ("jalapeno", "Jalapeno"),
            ("chipotle", "Chipotle"),
        )

        class Schema(colander.Schema):
            pepper = colander.SchemaNode(
                colander.Set(),
                widget=deform.widget.CheckboxChoiceWidget(
                    values=choices, readonly=True
                ),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(
            form, appstruct={"pepper": ["chipotle", "jalapeno"]}
        )

    @view_config(renderer="templates/form.pt", name="i18n")
    @demonstrate("Internationalization")
    def i18n(self):

        minmax = {"min": 1, "max": 10}
        locale_name = get_locale_name(self.request)

        class Schema(colander.Schema):
            number = colander.SchemaNode(
                colander.Integer(),
                title=_("A number between ${min} and ${max}", mapping=minmax),
                description=_(
                    "A number between ${min} and ${max}", mapping=minmax
                ),
                validator=colander.Range(1, 10),
            )
            _LOCALE_ = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.HiddenWidget(),
                default=locale_name,
            )

        schema = Schema()
        form = deform.Form(
            schema, buttons=[deform.Button("submit", _("Submit"))]
        )

        return self.render_form(form, is_i18n=True)

    @view_config(renderer="templates/form.pt", name="hidden_field")
    @demonstrate("Hidden Widget")
    def hidden_field(self):
        class Schema(colander.Schema):
            sneaky = colander.SchemaNode(
                colander.Boolean(),
                widget=deform.widget.HiddenWidget(),
                default=True,
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="hiddenmissing")
    @demonstrate("Hidden Widget (missing, representing an Integer)")
    def hiddenmissing(self):
        class Schema(colander.Schema):
            title = colander.SchemaNode(colander.String())
            number = colander.SchemaNode(
                colander.Integer(),
                widget=deform.widget.HiddenWidget(),
                missing=colander.null,
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="text_input_masks")
    @demonstrate("Text Input Masks")
    def text_input_masks(self):
        class Schema(colander.Schema):
            ssn = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(mask="999-99-9999"),
            )
            date = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(mask="99/99/9999"),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="textareacsv")
    @demonstrate("Text Area CSV Widget")
    def textareacsv(self):
        class Row(colander.TupleSchema):
            first = colander.SchemaNode(colander.Integer())
            second = colander.SchemaNode(colander.String())
            third = colander.SchemaNode(colander.Decimal())

        class Rows(colander.SequenceSchema):
            row = Row()

        class Schema(colander.Schema):
            csv = Rows()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        form["csv"].widget = deform.widget.TextAreaCSVWidget(rows=10, cols=60)
        appstruct = {"csv": [(1, "hello", 4.5), (2, "goodbye", 5.5)]}

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="textinputcsv")
    @demonstrate("Text Input CSV Widget")
    def textinputcsv(self):
        class Row(colander.TupleSchema):
            first = colander.SchemaNode(colander.Integer())
            second = colander.SchemaNode(colander.String())
            third = colander.SchemaNode(colander.Decimal())

        class Schema(colander.Schema):
            csv = Row()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        # we don't need to assign a widget; the text input csv widget is the
        # default widget for tuples
        appstruct = {"csv": (1, "hello", 4.5)}

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="require_one_or_another")
    @demonstrate("Require One Field or Another")
    def require_one_or_another(self):
        class Schema(colander.Schema):
            one = colander.SchemaNode(
                colander.String(),
                missing=unicode(""),
                title="One (required if Two is not supplied)",
            )
            two = colander.SchemaNode(
                colander.String(),
                missing=unicode(""),
                title="Two (required if One is not supplied)",
            )

        def validator(form, value):
            if not value["one"] and not value["two"]:
                exc = colander.Invalid(
                    form, 'A value for either "one" or "two" is required'
                )
                exc["one"] = "Required if two is not supplied"
                exc["two"] = "Required if one is not supplied"
                raise exc

        schema = Schema(validator=validator)
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="multiple_error_messages_mapping"
    )
    @demonstrate("Multiple Error Messages For a Single Widget (Mapping)")
    def multiple_error_messages_mapping(self):
        def v1(node, value):
            msg = _("Error ${num}", mapping=dict(num=1))
            raise colander.Invalid(node, msg)

        def v2(node, value):
            msg = _("Error ${num}", mapping=dict(num=2))
            raise colander.Invalid(node, msg)

        def v3(node, value):
            msg = _("Error ${num}", mapping=dict(num=3))
            raise colander.Invalid(node, msg)

        class Schema(colander.Schema):
            field = colander.SchemaNode(
                colander.String(),
                title="Fill in a value and submit to see multiple errors",
                validator=colander.All(v1, v2, v3),
            )

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="multiple_error_messages_seq"
    )
    @demonstrate("Multiple Error Messages For a Single Widget (Sequence)")
    def multiple_error_messages_seq(self):
        def v1(node, value):
            msg = _("Error ${num}", mapping=dict(num=1))
            raise colander.Invalid(node, msg)

        def v2(node, value):
            msg = _("Error ${num}", mapping=dict(num=2))
            raise colander.Invalid(node, msg)

        def v3(node, value):
            msg = _("Error ${num}", mapping=dict(num=3))
            raise colander.Invalid(node, msg)

        class Sequence(colander.SequenceSchema):
            field = colander.SchemaNode(
                colander.String(),
                title="Fill in a value and submit to see multiple errors",
                validator=colander.All(v1, v2, v3),
            )

        class Schema(colander.Schema):
            fields = Sequence()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="multiple_forms")
    @demonstrate("Multiple Forms on the Same Page")
    def multiple_forms(self):
        import itertools

        # We need to make sure the form field identifiers for the two
        # forms do not overlap so accessibility features continue to work,
        # such as focusing the field related to a legend when the
        # legend is clicked on.
        # We do so by creating an ``itertools.count`` object and
        # passing that object as the ``counter`` keyword argument to
        # the constructor of both forms.  As a result, the second
        # form's element identifiers will not overlap the first
        # form's.

        counter = itertools.count()

        class Schema1(colander.Schema):
            name1 = colander.SchemaNode(colander.String())

        schema1 = Schema1()
        form1 = deform.Form(
            schema1, buttons=("submit",), formid="form1", counter=counter
        )

        class Schema2(colander.Schema):
            name2 = colander.SchemaNode(colander.String())

        schema2 = Schema2()
        form2 = deform.Form(
            schema2, buttons=("submit",), formid="form2", counter=counter
        )

        html = []
        captured = None

        if "submit" in self.request.POST:
            posted_formid = self.request.POST["__formid__"]
            for (formid, form) in [("form1", form1), ("form2", form2)]:
                if formid == posted_formid:
                    try:
                        controls = self.request.POST.items()
                        captured = form.validate(controls)

                        html.append(form.render(captured))
                    except deform.ValidationFailure as e:
                        # the submitted values could not be validated
                        html.append(e.render())
                else:
                    html.append(form.render())
        else:
            for form in form1, form2:
                html.append(form.render())

        html = "".join(html)

        code, start, end = self.get_code(1)

        # values passed to template for rendering
        return {
            "form": html,
            "captured": repr(captured),
            "code": code,
            "start": start,
            "demos": self.get_demos(),
            "end": end,
            "title": "Multiple Forms on the Same Page",
        }

    @view_config(renderer="templates/form.pt", name="widget_adapter")
    @demonstrate("Widget Adapter")
    def widget_adapter(self):
        # Formish allows you to pair a widget against a type that
        # doesn't "natively" lend itself to being representable by the
        # widget. For example, it allows you to use a textarea widget
        # against a sequence type.  To provide this feature, Formish
        # uses an adapter to convert the sequence data to text during
        # serialization and from text back to a sequence during
        # deserialization.
        #
        # Deform doesn't have such a feature out of the box.  This is
        # on purpose: the feature is really too complicated and
        # magical for civilians.  However, if you really want or need
        # it, you can add yourself as necessary using an adapter
        # pattern.
        #
        # In the demo method below, we adapt a "normal" textarea
        # widget for use against a sequence.  The resulting browser UI
        # is the same as if we had used a TextAreaCSVWidget against
        # the sequence as in the "textareacsv" test method.
        #
        # N.B.: we haven't automated the lookup of the widget adapter
        # based on the type of the field and the type of the widget.
        # Instead, we just construct an adapter manually.  Adding an
        # abstraction to the lookup based on the widget and schema
        # types being adapted is easy enough, but trying to follow the
        # code path of the abstraction becomes brain bending.
        # Therefore, we don't bother to show it.

        class Row(colander.TupleSchema):
            first = colander.SchemaNode(colander.Integer())
            second = colander.SchemaNode(colander.String())
            third = colander.SchemaNode(colander.Decimal())

        class Rows(colander.SequenceSchema):
            row = Row()

        class Schema(colander.Schema):
            csv = Rows()

        schema = Schema()
        form = deform.Form(schema, buttons=("submit",))
        inner_widget = deform.widget.TextAreaWidget(rows=10, cols=60)
        widget = SequenceToTextWidgetAdapter(inner_widget)
        form["csv"].widget = widget
        appstruct = {"csv": [(1, "hello", 4.5), (2, "goodbye", 5.5)]}

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="deferred_schema_bindings")
    @demonstrate("Deferred Schema Bindings")
    def deferred_schema_bindings(self):
        import datetime

        import colander

        @colander.deferred
        def deferred_date_validator(node, kw):
            max_date = kw.get("max_date")
            if max_date is None:
                max_date = datetime.date.today()
            return colander.Range(min=datetime.date.min, max=max_date)

        @colander.deferred
        def deferred_date_description(node, kw):
            max_date = kw.get("max_date")
            if max_date is None:
                max_date = datetime.date.today()
            return "Blog post date (no earlier than %s)" % max_date.ctime()

        @colander.deferred
        def deferred_date_missing(node, kw):
            default_date = kw.get("default_date")
            if default_date is None:
                default_date = datetime.date.today()
            return default_date

        @colander.deferred
        def deferred_body_validator(node, kw):
            max_bodylen = kw.get("max_bodylen")
            if max_bodylen is None:
                max_bodylen = 1 << 18
            return colander.Length(max=max_bodylen)

        @colander.deferred
        def deferred_body_description(node, kw):
            max_bodylen = kw.get("max_bodylen")
            if max_bodylen is None:
                max_bodylen = 1 << 18
            return "Blog post body (no longer than %s bytes)" % max_bodylen

        @colander.deferred
        def deferred_body_widget(node, kw):
            body_type = kw.get("body_type")
            if body_type == "richtext":
                widget = deform.widget.RichTextWidget()
            else:
                widget = deform.widget.TextAreaWidget()
            return widget

        @colander.deferred
        def deferred_category_validator(node, kw):
            categories = kw.get("categories", [])
            return colander.OneOf([x[0] for x in categories])

        @colander.deferred
        def deferred_category_widget(node, kw):
            categories = kw.get("categories", [])
            return deform.widget.RadioChoiceWidget(values=categories)

        class BlogPostSchema(colander.Schema):
            title = colander.SchemaNode(
                colander.String(),
                title="Title",
                description="Blog post title",
                validator=colander.Length(min=5, max=100),
                widget=deform.widget.TextInputWidget(),
            )
            date = colander.SchemaNode(
                colander.Date(),
                title="Date",
                missing=deferred_date_missing,
                description=deferred_date_description,
                validator=deferred_date_validator,
                widget=deform.widget.DateInputWidget(),
            )
            body = colander.SchemaNode(
                colander.String(),
                title="Body",
                description=deferred_body_description,
                validator=deferred_body_validator,
                widget=deferred_body_widget,
            )
            category = colander.SchemaNode(
                colander.String(),
                title="Category",
                description="Blog post category",
                validator=deferred_category_validator,
                widget=deferred_category_widget,
            )

        schema = BlogPostSchema().bind(
            max_date=datetime.date.max,
            max_bodylen=5000,
            body_type="richtext",
            default_date=datetime.date.today(),
            categories=[("one", "One"), ("two", "Two")],
        )

        form = deform.Form(schema, buttons=("submit",))
        return self.render_form(form)

    @view_config(renderer="templates/form.pt", name="pyramid_csrf_demo")
    @demonstrate("Pyramid CSRF Demo (using schema binding)")
    def pyramid_csrf_demo(self):
        @colander.deferred
        def deferred_csrf_default(node, kw):
            request = kw.get("request")
            csrf_token = request.session.get_csrf_token()
            return csrf_token

        @colander.deferred
        def deferred_csrf_validator(node, kw):
            def validate_csrf(node, value):
                request = kw.get("request")
                csrf_token = request.session.get_csrf_token()
                if value != csrf_token:
                    raise ValueError("Bad CSRF token")

            return validate_csrf

        class CSRFSchema(colander.Schema):
            csrf = colander.SchemaNode(
                colander.String(),
                default=deferred_csrf_default,
                validator=deferred_csrf_validator,
                widget=deform.widget.HiddenWidget(),
            )

        # subclass from CSRFSchema everywhere to get CSRF validation
        class MySchema(CSRFSchema):
            text = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextInputWidget(),
                description="Enter some text",
            )

        schema = MySchema().bind(request=self.request)
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt",
        name="sequence_with_prototype_that_has_no_name",
    )
    @demonstrate("Sequence With Prototype that Has No Name")
    def sequence_with_prototype_that_has_no_name(self):
        class EmailMessage(colander.Schema):
            subject = colander.SchemaNode(colander.String())
            to = colander.SchemaNode(
                colander.Sequence(),
                colander.SchemaNode(colander.String(), name="foo"),
            )

        schema = EmailMessage()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form)

    @view_config(
        renderer="templates/form.pt", name="readonly_value_nonvalidation"
    )
    @demonstrate("Dont Validate Readonly Fields")
    def readonly_value_nonvalidation(self):
        @colander.deferred
        def deferred_missing(node, kw):
            return appstruct["readonly"]

        class Values(colander.Schema):
            readonly = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(readonly=True),
                missing=deferred_missing,
            )
            readwrite = colander.SchemaNode(colander.String())

        appstruct = {"readonly": "Read Only", "readwrite": "Read and Write"}
        schema = Values().bind()
        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct=appstruct)

    @view_config(renderer="templates/form.pt", name="readonly_fields")
    @demonstrate("Read-Only Fields")
    def readonly_fields(self):
        import datetime

        class Schema(colander.Schema):
            textinput = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(readonly=True),
                missing=colander.null,
                description="Text in a text input",
            )
            textarea = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextAreaWidget(readonly=True),
                missing=colander.null,
                description="Text in a textarea",
            )
            single_select = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(
                    values=[("a", "The letter a"), ("b", "The letter b")],
                    readonly=True,
                ),
                missing=colander.null,
                description="A letter",
            )
            multi_select = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.SelectWidget(
                    values=[("a", "The letter a"), ("b", "The letter b")],
                    multiple=True,
                    readonly=True,
                ),
                missing=colander.null,
                description="Some letters",
            )
            richtext = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.RichTextWidget(readonly=True),
                description="Some text",
                missing=colander.null,
            )
            money = colander.SchemaNode(
                colander.Decimal(),
                widget=deform.widget.MoneyInputWidget(readonly=True),
                description="Some money",
                missing=colander.null,
            )
            date = colander.SchemaNode(
                colander.Date(),
                widget=deform.widget.DateInputWidget(readonly=True),
                description="Some date",
                missing=colander.null,
            )

        appstruct = {
            "textinput": "readonly text input",
            "textarea": "readonly text area",
            "single_select": "a",
            "multi_select": ("a", "b"),
            "richtext": "<p>Yo!</p>",
            "money": decimal.Decimal(1),
            "date": datetime.date(2010, 5, 5),
        }

        schema = Schema()

        form = deform.Form(schema, buttons=("submit",))

        return self.render_form(form, appstruct=appstruct)

    @view_config(
        renderer="templates/form.pt",
        name="custom_classes_on_outermost_html_element",
    )
    @demonstrate("Custom classes on outermost html element of Widgets")
    def custom_classes_on_outermost_html_element(self):
        import datetime

        class Mapping(colander.Schema):
            upload = colander.SchemaNode(
                deform.FileData(),
                widget=deform.widget.FileUploadWidget(
                    tmpstore, item_css_class="mapped_widget_custom_class"
                ),
            )

        class Schema(colander.Schema):
            text = colander.SchemaNode(
                colander.String(),
                widget=deform.widget.TextInputWidget(
                    item_css_class="top_level_mapping_widget_custom_class"
                ),
            )
            sequence = colander.SchemaNode(
                colander.Sequence(),
                colander.SchemaNode(
                    colander.Date(),
                    name="Sequence Item",
                    widget=deform.widget.DatePartsWidget(
                        item_css_class="sequenced_widget_custom_class"
                    ),
                ),
                default=[datetime.date.today()],
                description="SequenceWidget",
            )
            mapping = Mapping(description="MappingWidget")

        return self.render_form(deform.Form(Schema(), buttons=("submit",)))


class MemoryTmpStore(dict):
    """Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""

    def preview_url(self, uid):
        return None


tmpstore = MemoryTmpStore()


class SequenceToTextWidgetAdapter(object):
    def __init__(self, widget):
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)

    def serialize(self, field, cstruct, readonly=False):
        if cstruct is colander.null:
            cstruct = []
        textrows = getattr(field, "unparseable", None)
        if textrows is None:
            outfile = StringIO()
            writer = csv.writer(outfile)
            writer.writerows(cstruct)
            textrows = outfile.getvalue()
        return self.widget.serialize(
            field, cstruct=textrows, readonly=readonly
        )

    def deserialize(self, field, pstruct):
        text = self.widget.deserialize(field, pstruct)
        if text is colander.null:
            return text
        if not text.strip():
            return colander.null
        try:
            infile = StringIO(text)
            reader = csv.reader(infile)
            rows = list(reader)
        except Exception as e:
            field.unparseable = pstruct
            raise colander.Invalid(field.schema, str(e))
        return rows

    def handle_error(self, field, error):
        msgs = []
        if error.msg:
            field.error = error
        else:
            for e in error.children:
                msgs.append("line %s: %s" % (e.pos + 1, e))
            field.error = colander.Invalid(field.schema, "\n".join(msgs))


def main(global_config, **settings):
    # paster serve entry point
    settings["debug_templates"] = "true"

    session_factory = SignedCookieSessionFactory("seekrit!")
    config = Configurator(settings=settings, session_factory=session_factory)
    config.add_translation_dirs(
        "colander:locale", "deform:locale", "deformdemo:locale"
    )

    config.include("pyramid_chameleon")

    # Set up Chameleon templates (ZTP) rendering paths

    def translator(term):
        # i18n localizing function
        return get_localizer(get_current_request()).translate(term)

    # Configure renderer
    configure_zpt_renderer(
        ("deformdemo:custom_widgets", "unofficial-deformdemo:custom_widgets"),
        translator,
    )
    config.add_static_view("static_deform", "deform:static")
    config.add_route(
        "unofficial-deformdemo", "/unofficial-deformdemo*traverse"
    )
    config.add_route("deformdemo", "*traverse")

    def onerror(*arg):
        pass

    config.scan("deformdemo", onerror=onerror)
    config.include("..unofficial-deformdemo")
    return config.make_wsgi_app()
