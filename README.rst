===================
Pluggable Namespace
===================

cpns is used to express the Plugin Oriented Programming Paradigm. The Plugin
Oriented Programming Paradigm has been designed to make pluggable software
easy to write and easy to extend.

Plugin Oriented Programming presents a new way to scale development teams
and deliver complex software. This is done by making the applications entirely
out of plugins, and also making the applications themselves natively pluggable
with each other.

Using Plugin Oriented Programming it then becomes easy to have the best of both
worlds, software can be built in small pieces, making development easier to
maintain. The small pieces can then be merged and deployed in a single
binary, making code deployment easy as well.

All this using Cython, one of the world's most pnsular and powerful programming
languages.

Installation
============

First off, set up your python environment to use a gitlab repository to gather packages:

.. code-block:: toml

    # ~/.pip/pip.conf
    [global]
    extra-index-url = https://__token__:<personal_access_token>@gitlab.com/api/v4/groups/<namespace>/-/packages/pypi/simple

Now you can install ``cpns`` from pypi or gitlab repositories:

.. code-block:: bash

    pip3 install cpns

Now all it takes to create a pluggable application is a few lines of code.
This is the root of every pns project.
We create a hub, we add dynamic subsystems, and then we call them through the hub's namespace.

.. code-block:: python

    import cpns
    import asyncio

    loop = asyncio.get_event_loop()
    asyncio.run(main())


    async def main():
        async with cpns.Hub() as hub:
            await hub.my_sub.init.cli()


Configuration
=============

When creating a cpns app, we put all of the pns configuration in a config.yaml

.. code-block:: yaml

    # Every config option for your plugin
    config:
        my_namespace:
            my_opt:
                default: True

    # Options that should be exposed on the CLI when your app controls the CLI
    cli_config:
        my_namespace:
            my_opt:
                # All options that are accepted by ArgParser.add_argument are good here
                help: description of this option
                subcommands:
                    - my_subcommand
                group: My arg group

    # Subcommands to expose for your project
    subcommands:
        my_namespace:
            my_subcommand:
                help: My subcommand

    # Dynamic namespaces that your app merges onto and which folders extend those namespaces
    dyne:
        my_dyne:
        - src_dir

    # python imports that your app uses which should be added to hub.lib for your app
    import:
        - asyncio
        - importlib
        - importlib.resources
        - os
        - toml

Create a pns config file:

.. code-block:: yaml

    # The default location is in ~/.pns/config.yaml
    # But you can change that by setting the PNS_CONFIG environment variable

    pns_cli:
        # Setting this option will make your hub persist on the cli between calls
        hub_state: ~/.pns/hub.pkl
    log:
        log_plugin: async

From the above example, all arguments would be loaded onto the namespace under hub.OPT.my_namesapce.
One config.yaml can add config options to multiple namespaces.
They are all merged together in the order they are found in sys.path

Extending cpns
==============

Extending ``cpns``  is extremely easy with dynamic namespaces.
You can extend any dynamic namespace on the hub simply by adding a directory containing a "conifg.yaml" to the PYTHONPATH.
I.e.

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/path/to/my/code

Then you can add a config.yaml to that directory:

.. code-block:: yaml

    #/path/to/my/code/config.yaml
    dyne:
      namespace:
        - src

Now every python file under ``/path/to/my/code/src/`` will be added to the hub under ``hub.namespace``.


Testing
=======
Clone the repo

.. code-block:: bash

    git clone https://gitlab.com/Akm0d/cpns.git
    cd cpns

Install ``cpns`` with the testing extras

.. code-block:: bash

    pip3 install .\[test\]

Run the tests in your cloned fork of cpns:

.. code-block:: bash

    pytest tests


Documentation
=============

Check out the docs for more information:

https://pns.readthedocs.io

There is a much more in depth tutorial here, followed by documents on how to
think in Plugin Oriented Programming. Take your time to read it, it is not long
and can change how you look at writing software!
