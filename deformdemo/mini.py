"""Self-contained Deform demo example."""
from __future__ import print_function

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.httpexceptions import HTTPFound

import colander
import deform


class ExampleSchema(deform.schema.CSRFSchema):

    name = colander.SchemaNode(
        colander.String(),
        title="Name")

    age = colander.SchemaNode(
        colander.Int(),
        default=18,
        title="Age",
        help_text="Your age in years")


def mini_example(request):
    """Sample Deform form with validation."""

    schema = ExampleSchema().bind(request=request)

    # Create a styled button with some extra Bootstrap 3 CSS classes
    process_btn = deform.form.Button(name='process', title="Process")
    form = deform.form.Form(schema, buttons=(process_btn,))

    # User submitted this form
    if request.method == "POST":
        if 'process' in request.POST:

            try:
                appstruct = form.validate(request.POST.items())

                # Save form data from appstruct
                print("Your name:", appstruct["name"])
                print("Your age:", appstruct["age"])

                # Thank user and take him/her to the next page
                request.session.flash('Thank you for the submission.')

                # Redirect to the page shows after succesful form submission
                return HTTPFound("/")

            except deform.exception.ValidationFailure as e:
                # Render a form version where errors are visible next to the fields,
                # and the submitted values are posted back
                rendered_form = e.render()
    else:
        # Render a form with initial default values
        rendered_form = form.render()

    return {
        "rendered_form": rendered_form,
    }


def main(global_config, **settings):
    """pserve entry point"""
    session_factory = UnencryptedCookieSessionFactoryConfig('seekrit!')
    config = Configurator(settings=settings, session_factory=session_factory)
    config.include('pyramid_chameleon')
    deform.renderer.configure_zpt_renderer()
    config.add_static_view('static_deform', 'deform:static')
    config.add_route('mini_example', path='/')
    config.add_view(mini_example, route_name="mini_example", renderer="templates/mini.pt")
    return config.make_wsgi_app()
