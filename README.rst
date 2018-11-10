Deform Demo
===========

.. image:: https://travis-ci.org/Pylons/deformdemo.png?branch=master
           :target: https://travis-ci.org/Pylons/deformdemo

Demonstration application for the `Deform
<https://docs.pylonsproject.org/projects/deform/>`_ Python HTML form
library.


Online version
--------------

Visit https://deformdemo.pylonsproject.org


Docker version
--------------

Run the latest version of this application with Docker.

.. code-block:: console

    docker run -d -p 8000:8522 pylons/deformdemo:latest


Then, in your browser, visit http://localhost:8080


From source
-----------

This application supports Python versions 2.7, 3.4, 3.5, 3.6 and 3.7, but
 we strongly recommend you to use it Python >=3.5.

- Create a virtualenv::

    $ python3 -m venv /path/to/my/venv

  Hereafter ``/path/to/my/venv`` will be referred to as $VENV in steps
  below.

- Get a checkout of deformdemo::

    $ git clone git://github.com/Pylons/deformdemo.git

- ``cd`` to the newly checked out deformdemo package::

    $ cd deformdemo

- Run ``pip install -e .`` using the virtualenv's ``python`` command::

    $ $VENV/bin/pip install -e .

- While your working directory is still ``deformdemo``, start the demo
  application::

    $ $VENV/bin/pserve demo.ini

- Visit http://localhost:8000 in a browser to see the demo.


Running the Demo's Selenium Tests
---------------------------------

The ``deformdemo`` application serves as a target for functional
testing during Deform's development.  A suite of Selenium tests may be
run against a local instance of the demonstration application.  It is
wise to run these tests before submitting a patch.  Here's how:

- Start the ``deformdemo`` application as described above in "Running
  the Demo".  Leave the terminal window running this application open,
  and open another terminal window to perform the below steps.

- In the other terminal window, cd to the "deformdemo" checkout directory
  you created above in "Running the Demo"::

    $ cd /path/to/my/deformdemo/checkout

- Run ``pip install -e .`` using the virtualenv's ``python`` command, but this time install the testing requirements::

    $ $VENV/bin/pip install -e ".[testing]'

- Run the tests::

   $ $VENV/bin/nosetests

  ``$VENV`` is defined as it was in "Running the Demo" above.

- You will (hopefully) see Firefox pop up and it will begin to display in quick
  succession the loading of pages in the bottom window and some test output in
  the top window.  The tests will run for five or ten minutes.

- Test success means that the console window on which you ran
  ``nosetests`` shows a bunch of dots, a test summary, then ``OK``.  If
  it shows a traceback, ``FAILED``, or anything other than a straight
  line of dots, it means there was an error.

- Fix any errors by modifying your code or by modifying the tests to
  expect the changes you've made.


Testing an Alternate Renderer Implementation
--------------------------------------------

- Copy the ``demo.ini`` file from this demo package to your renderer's
  package.

- Change the ``deform.renderer`` key in the ``demo.ini`` copy to point at
  your renderer (it's a Python dotted name).

- Run ``pserve /path/to/your/copy/of/demo.ini``.

- Run the selenium tests as above.
