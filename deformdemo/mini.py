"""Self-contained Deform demo example."""
from __future__ import print_function

import colander
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from deformdemo.custom_widgets.react_jsonschema_form_widget import (
    ReactJsonSchemaFormWidget,
)
import jsonschema as JsonSchema
import deform
from deform.widget import ResourceRegistry
from pkg_resources import resource_filename

search_path = [resource_filename("deform", "templates")]

resource_registry = ResourceRegistry(use_defaults=True)

resource_registry = ReactJsonSchemaFormWidget.register_resources(
    resource_registry
)

search_path.append(
    # resource_filename(
    #     "deformdemo", "custom_widgets/react_jsonschema_form_widget"
    # )
    # "/home/thijs/projects/deformdemo/deformdemo/custom_widgets/react_jsonschema_form_widget"
    "/home/thijs/projects/deformdemo/deformdemo/custom_widgets/react_jsonschema_form_widget"
)
print(search_path)
deform.Form.set_zpt_renderer(tuple(search_path))


def mini_example(request):
    """Sample Deform form with validation."""

    jsonschema = {
        "title": "A registration form",
        "description": "A simple form example.",
        "type": "object",
        "required": ["firstName", "lastName"],
        "properties": {
            "firstName": {
                "type": "string",
                "title": "First name",
                "default": "Chuck",
            },
            "lastName": {"type": "string", "title": "Last name"},
            "telephone": {
                "type": "string",
                "title": "Telephone",
                "minLength": 10,
            },
        },
    }

    class Schema(colander.Schema):

        registration = colander.SchemaNode(
            colander.Mapping(unknown="preserve"),
            widget=ReactJsonSchemaFormWidget(jsonschema=jsonschema),
        )

    def validator(form, value):
        try:
            JsonSchema.validate(value['registration'], jsonschema)
        except JsonSchema.exceptions.ValidationError as exc:
            raise colander.Invalid(form, exc.message) from exc

    schema = Schema(validator=validator)

    # Create a styled button with some extra Bootstrap 3 CSS classes
    process_btn = deform.form.Button(name="process", title="Process")
    form = deform.Form(
        schema, buttons=(process_btn,), resource_registry=resource_registry
    )
    print(
        request.static_url(
            'custom_widgets/react_jsonschema_form_widget/static/react.js'
        )
    )
    # User submitted this form
    if request.method == "POST":
        if "process" in request.POST:

            try:
                appstruct = form.validate(request.POST.items())

                # Save form data from appstruct
                print("Your name:", appstruct["name"])
                print("Your age:", appstruct["age"])

                # Thank user and take him/her to the next page
                request.session.flash("Thank you for the submission.")

                # Redirect to the page shows after succesful form submission
                return HTTPFound("/")

            except deform.exception.ValidationFailure as e:
                # Render a form version where errors are visible next to the
                # fields and the submitted values are posted back.
                rendered_form = e.render()
    else:
        # Render a form with initial default values
        rendered_form = form.render()
    reqts = form.get_widget_resources()

    return {
        # This is just rendered HTML in a string
        # and can be embedded in any template language
        "rendered_form": rendered_form,
        "css_links": reqts["css"],
        "js_links": reqts["js"],
    }


def main(global_config, **settings):
    """pserve entry point"""
    session_factory = UnencryptedCookieSessionFactoryConfig("seekrit!")
    config = Configurator(settings=settings, session_factory=session_factory)
    config.include("pyramid_chameleon")
    # deform.renderer.configure_zpt_renderer(("deformdemo:custom_widgets",))

    config.add_static_view(
        "static_rjsf",
        "deformdemo:custom_widgets/react_jsonschema_form_widget/static",
    )

    # config.add_static_view("static", "static")
    config.add_static_view("static_deform", "deform:static")
    config.add_route("mini_example", path="/")
    config.add_view(
        mini_example, route_name="mini_example", renderer="templates/mini.pt"
    )
    return config.make_wsgi_app()
