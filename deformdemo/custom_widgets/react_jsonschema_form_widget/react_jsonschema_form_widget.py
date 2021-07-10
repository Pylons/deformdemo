"""Implements a widget based on react jsonschema form."""
import json
from typing import Any, Dict, List, Tuple, Union
from uuid import uuid4

import colander
from deform.field import Field
from deform.widget import DateTimeInputWidget, ResourceRegistry
from deform.widget import Select2Widget
from deform.widget import SelectWidget
from deform.widget import Widget
from pkg_resources import resource_filename


from pathlib import Path

here = Path(__file__).parent
fname = here / 'test.txt'


class JsonWidget(Widget):
    """Json editor with schema validation.

    Based on https://github.com/josdejong/jsoneditor/
    """

    template: str = "templates/json"
    readonly_template: str = "templates/json_readonly"
    style: str = "font-family: monospace;"
    requirements: Tuple[Tuple[str, None], ...] = (("jsoneditor", None),)
    jsonschema = "{}"

    def __init__(self, jsonschema={}, **kw):
        """Initialize instance."""
        self.jsonschema = json.dumps(jsonschema)
        self.title = (jsonschema.get("title", None),)
        self.description = jsonschema.get("description", None)

    def serialize(self, field: Field, cstruct, **kw: Any) -> str:
        """Serialize."""
        try:
            cstruct = json.dumps(cstruct, indent=4)
        except TypeError:
            jsonschema = json.loads(
                kw.get("jsonschema", field.widget.jsonschema)
            )
            if jsonschema.get("type") == "array":
                cstruct = "[]"
            elif jsonschema.get("type") == "object":
                cstruct = "{}"
            else:
                cstruct = "undefined"
        readonly = kw.get("readonly", self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, uuid=uuid4(), **values)

    def deserialize(
        self, field: Field, pstruct: str
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], colander._null]:
        """Deserialize."""
        try:
            return json.loads(pstruct)
        except (TypeError, json.JSONDecodeError):
            return colander.null


class ReactJsonSchemaFormWidget(JsonWidget):
    """Use react-jsonschema-form widget."""

    template = "templates/react_jsonschema_form"
    requirements = (
        ("rjsf-react", None),
        ("rjsf-react-dom", None),
        ("rjsf", None),
    )

    @classmethod
    def register_resources(cls, resource_registry):
        resource_registry.set_js_resources(
            "rjsf-react",
            None,
            "deformdemo:custom_widgets/react_jsonschema_form_widget/static/react.js",
        )
        resource_registry.set_js_resources(
            "rjsf-react-dom",
            None,
            "deformdemo:custom_widgets/react_jsonschema_form_widget/static/react-dom.js",
        )
        resource_registry.set_js_resources(
            "rjsf",
            None,
            "deformdemo:custom_widgets/react_jsonschema_form_widget/static/react-jsonschema-form.js",
        )
        return resource_registry
        # resource_filename("deformdemo", "templates")

    def serialize(self, field: Field, cstruct, **kw: Any) -> str:
        """Serialize with conversion for rjsf."""
        self.get_template_values(field, cstruct, kw)
        kw["jsonschema"] = json.dumps(
            json.loads(kw.get("jsonschema", field.widget.jsonschema)),
            indent=2,
        )
        return super().serialize(field, cstruct, **kw)
