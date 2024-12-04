=======
Pop-cli
=======

A cli interface for pop that exposes a persistent hub on the command line.

Getting Started
===============

First off, set up your python environment to use a gitlab repository to gather packages:

.. code-block:: toml

    # ~/.pip/pip.conf
    [global]
    extra-index-url = https://__token__:<personal_access_token>@gitlab.com/api/v4/groups/<namespace>/-/packages/pypi/simple

Now you can install ``pop-cli`` from pypi or gitlab repositories:

.. code-block:: bash

    pip3 install pop-cli


You can now initialize pop from the cli:

.. code-block:: bash

    python -m hub my_sub.init.cli

or:

.. code-block:: bash

    hub my_sub.init.cli

Specify a namespace that should host the authoritative CLI by calling using --cli as the first argument:

.. code-block:: bash

    hub --cli=my_app my_sub.init.cli

If you don't specify a --cli, unknown args will be forwarded as parameters to the reference you give:


.. code-block:: bash

    hub pop.test.func arg1 arg2 --kwarg1=asdf --kwarg2 asdf


You can access anything that is on the hub, this is very useful for debugging.

Try this to see the subs that made it onto the hub:

.. code-block:: bash

    hub _subs

You can do this to see everything that made it into hub.OPT:

.. code-block:: bash

    hub OPT

Start an interactive python shell that includes a hub and allows async code to be run:

.. code-block:: bash

    hub -i
    #>>> await hub.lib.asyncio.sleep(0)


Documentation
=============

Check out the docs for more information:

https://pop.readthedocs.io

There is a much more in depth tutorial here, followed by documents on how to
think in Plugin Oriented Programming. Take your time to read it, it is not long
and can change how you look at writing software!
