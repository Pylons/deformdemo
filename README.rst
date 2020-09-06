Deform Demo
===========

.. image:: https://travis-ci.org/Pylons/deformdemo.png?branch=2.0-branch
           :target: https://travis-ci.org/Pylons/deformdemo

Demonstration application for the `Deform <https://docs.pylonsproject.org/projects/deform/en/latest>`_ Python HTML form library.

This application is tested on Python versions 2.7, 3.5, 3.6, 3.7, and 3.8, and PyPy and PyPy3.
It is also tested on Python 3.9-dev but allowed to fail.


Online version
--------------

Visit https://deformdemo.pylonsproject.org


Docker version
--------------

Build the Docker image for deformdemo and tag it.

.. code-block:: bash

    # docker build --tag pylons/deformdemo:<version> .
    docker build --tag pylons/deformdemo:2.0.14 .

Run the built image with Docker.

.. code-block:: bash

    docker run -d -p 8000:8522 pylons/deformdemo:2.0.14

Then in your browser, visit http://localhost:8000

To stop the docker container, find its ``NAME`` and issue the ``stop`` command.

.. code-block:: bash

    docker ps -a
    docker stop <value_from_NAMES_column>


From source
-----------

-   Create a virtual environment.

    .. code-block:: bash

        python3 -m venv /path/to/my/env

    Hereafter ``/path/to/my/env`` will be referred to as ``$VENV`` in the following steps.

-   Clone deformdemo.

    .. code-block:: bash

        git clone git://github.com/Pylons/deformdemo.git

-   ``cd`` to the newly checked out deformdemo package.

    .. code-block:: bash

        cd deformdemo

-   Run ``pip install -e .`` using the virtual environment's ``python`` command.

    .. code-block:: bash

        $VENV/bin/pip install -e .

-   While your working directory is still ``deformdemo``, start the demo application.

    .. code-block:: bash

        $VENV/bin/pserve demo.ini

-   Visit http://localhost:8522 in a browser to see the demo.


Install functional test requirements
------------------------------------

The ``deformdemo`` application serves as a target for functional testing during Deform's development.
A suite of Selenium tests may be run against a local instance of the demonstration application.
It is wise to run these tests using the following steps before submitting a pull request.

First prepare the functional test environment by installing requirements.
We will assume that you put your projects in your user directory, although you can put them anywhere.

    .. code-block:: bash

        cd ~/projects/deformdemo/


Install Python development and testing requirements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following command will install requirements for development and testing of deformdemo.
It performs editable installs of Colander and Deform into your virtual environment's ``src`` directory, and deformdemo's testing requirements into ``lib/<python.version>/site-packages`` directory.

.. code-block:: bash

    $VENV/bin/pip install -Ur requirements-dev.txt


Install Firefox latest
^^^^^^^^^^^^^^^^^^^^^^

macOS
"""""

`Download the latest version of Firefox for your platform <https://www.mozilla.org/en-US/firefox/all/>`_.

Open the ``.dmg`` (macOS), and drag the Firefox icon to:

    .. code-block:: console

        ~/projects/deformdemo/

Linux (Debian)
""""""""""""""

Use cURL or wget.
See the `Firefox download README.txt <https://ftp.mozilla.org/pub/firefox/releases/latest/README.txt>`_ for instructions.
For example on Linux:

    .. code-block:: bash

        cd ~/projects/deformdemo/
        wget -O firefox-latest.tar.bz2 \
        "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US"

Decompress the downloaded file.

    .. code-block:: bash

        tar -xjf firefox-latest.tar.bz2


geckodriver
^^^^^^^^^^^

Install the `latest release of geckodriver <https://github.com/mozilla/geckodriver/releases>`_.

.. code-block:: bash

    # macOS
    wget https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-macos.tar.gz
    tar -xzf geckodriver-v0.27.0-macos.tar.gz

    # Linux (Debian)
    wget https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz
    tar -xzf geckodriver-v0.27.0-linux64.tar.gz


gettext
^^^^^^^

The functional tests require the installation of the GNU ``gettext`` utilities, specifically ``msgmerge`` and ``msgfmt``.
Use your package manager to install these requirements.

macOS
"""""

Use `Homebrew <https://brew.sh/>`_.

.. code-block:: bash

        brew install gettext
        brew link gettext --force

If you ever have problems building packages, you can always unlink it.

.. code-block:: bash

        brew unlink gettext

Linux (Debian)
""""""""""""""

.. code-block:: bash

        apt-get install gettext
        apt-get install gettext-base


Selenium
""""""""

Selenium was already installed via ``$VENV/bin/pip install -Ur requirements-dev.txt``.


Running the Demo's Functional Tests
-----------------------------------

-   Start the ``deformdemo`` application as described above in "Running the Demo".
    Leave the terminal window running this application open, and open a second terminal window to perform the below steps.

-   In the second terminal window, go to the "deformdemo" checkout directory you created above in "Running the Demo".

    .. code-block:: bash

        cd ~/projects/deformdemo

-   Set an environment variable to add your local checkout of Deform to your ``PATH``.
    It must to be set before running tox or nosetest, otherwise Firefox or Chrome will not start and will return an error message such as ``'geckodriver' executable needs to be in PATH.``

    .. code-block:: bash

        export PATH=~/projects/deform:$PATH

-   Run the tests.

    .. code-block:: bash

        $VENV/bin/nosetests

    ``$VENV`` is defined as it was in "Running the Demo" above.

-   You will (hopefully) see Firefox pop up and it will begin to display in quick succession the loading of pages.
    The tests will run for five or ten minutes.

-   Test success means that the console window on which you ran ``nosetests`` shows a bunch of dots, a test summary, then ``OK``.
    If it shows a traceback, ``FAILED``, or anything other than a straight line of dots, it means there was an error.

-   Fix any errors by modifying your code or by modifying the tests to expect the changes you've made.


Testing an Alternate Renderer Implementation
--------------------------------------------

-   Copy the ``demo.ini`` file from this demo package to your renderer's package.

-   Change the ``deform.renderer`` key in the ``demo.ini`` copy to point at your renderer (it's a Python dotted name).

-   Run ``pserve /path/to/your/copy/of/demo.ini``.

-   Run the Selenium tests as above.
