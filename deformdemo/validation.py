from pyramid import testing
from deformdemo import DeformDemo, main

config = dict()
config['deformdemo.renderer'] = 'deformdemo.zpt_renderer'
main(dict(), **config)
request = testing.DummyRequest()
demos = DeformDemo(request)

import pdb; pdb.set_trace()  # NOQA
