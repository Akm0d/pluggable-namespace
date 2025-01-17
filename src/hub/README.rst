=======================
pluggable-namespace cli
=======================

A cli interface for pns that exposes a persistent hub on the command line.

Getting Started
===============

You can initialize a hub from the cli:

.. code-block:: bash

    python -m hub my_sub.init.cli

or:

.. code-block:: bash

    hub my_sub.init.cli

Specify a namespace that should host the authoritative CLI by calling using --cli as the first argument:

.. code-block:: bash

    hub --cli=my_app my_sub.init.cli

If you don't specify a --cli, unknown args will be forwarded as parameters to the namespace path you give.
Try this one!

.. code-block:: bash

    hub pop.test.func arg1 arg2 --kwarg1=asdf --kwarg2 asdf


You can access anything that is on the hub, this is very useful for debugging.

Try this to see the subs that made it onto the hub:

.. code-block:: bash

    hub _nest

You can do this to see everything that made it into hub.OPT:

.. code-block:: bash

    hub OPT

Start an interactive python shell that includes a hub and allows async code to be run:

.. code-block:: bash

    hub -i
    #>>> await hub.lib.asyncio.sleep(0)
