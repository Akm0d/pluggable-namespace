===================
Pluggable Namespace
===================
This project is designed to facilitate the creation and management of pluggable software architectures using namespaces. The concept of pluggable namespaces enables the development of software that is modular and easy to extend.

Pluggable namespaces provide a framework for constructing applications composed entirely of interchangeable modules. This approach allows developers to scale their projects smoothly and integrate complex software components seamlessly.

Using pluggable namespaces, developers can build software in smaller, maintainable components. These components can then be combined and deployed as a single entity, simplifying the deployment process.

All of this is achieved using Python, one of the world's most popular and powerful programming languages.

Installation
============

You can install ``pluggable-namespace`` from PyPI:

.. code-block:: bash

    pip3 install pluggable-namespace

Quick Start
===========
Creating a pluggable application can be accomplished with just a few lines of code.
The heart of every pluggable-namespace project is the creation of a hub, adding dynamic subsystems,
and interacting with them through the hub's namespace.

However, you can use the hub simply by adding it to your function's headers on a single python file:

.. code-block:: python


    # my_file.py

    async def func(Hub):
        print("Hello World!")

    async def main(hub):
        # Call a function in your python file from the hub!
        await hub._.func()


Then you can run your script from the cli with the hub:

.. code-block:: bash

    hub -f my_file.py my_file.main


This will execute the `main` function in `my_file.py`, and you will see "Hello World!" printed to the console.
This is the simplest way to get started with pluggable namespaces.


Configuration
=============
When building a pluggable-namespace app, all configuration settings are stored in a ``config.yaml`` file.

.. code-block:: yaml

    # Each configuration option for your module
    config:
      my_namespace:
        my_opt:
          default: True

    # Options exposed on the CLI when your app controls the CLI
    cli_config:
      my_namespace:
        my_opt:
          help: Description of this option
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

    # Python imports that your app uses, to be added to hub.lib for your app
    import:
      - asyncio
      - importlib
      - importlib.resources
      - os
      - toml


From the example above, all parsed arguments are loaded onto the namespace under hub.OPT.my_namespace.
One ``config.yaml`` can add configuration options to multiple namespaces.
They are merged in the order found in sys.path.

If you have added files individually with ``hub -f`` then a ``config.yaml`` will be loaded from the directory of that file.

Extending Namespaces
====================

locally
-------

Extending ``pluggable-namespace`` is straightforward with dynamic namespaces.
Extend any dynamic namespace on the hub by adding a directory containing a "config.yaml" to PYTHONPATH.

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/path/to/project_root

Add a config.yaml to that directory:

.. code-block:: yaml

    # project_root/config.yaml
    dyne:
      namespace:
        # This references the directory project_root/foo
        - foo

Now, every Python file in ``project_root/foo`` will be added to the hub under ``hub.namespace``.


With PyPI
---------

You can use the ``seed`` command to create all the boiler-plate code you need for a pluggable-namespace project.

.. code-block:: bash

    hub seed.init.cli /path/to/project_root name=my_project


Now you can add all your code to /path/to/project_root/src/my_project
