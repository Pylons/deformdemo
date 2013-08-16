from pyramid import testing
from deformdemo import DeformDemo

request = testing.DummyRequest()
demos = DeformDemo(request)

import pdb; pdb.set_trace()  # NOQA
