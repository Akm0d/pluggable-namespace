===================
Pluggable Namespace
===================
This project is designed to facilitate the creation and management of pluggable software architectures using namespaces. The concept of pluggable namespaces enables the development of software that is modular and easy to extend.

Pluggable namespaces provide a framework for constructing applications composed entirely of interchangeable modules. This approach allows developers to scale their projects smoothly and integrate complex software components seamlessly.

Using pluggable namespaces, developers can build software in smaller, maintainable components. These components can then be combined and deployed as a single entity, simplifying the deployment process.

All of this is achieved using Python, one of the world's most popular and powerful programming languages.

Installation
============
First, configure your Python environment to use a GitLab repository to source packages:

.. code-block:: toml

    # ~/.pip/pip.conf
    [global]
    extra-index-url = https://__token__:<personal_access_token>@gitlab.com/api/v4/groups/<namespace>/-/packages/pypi/simple

You can now install ``pluggable-namespace`` from PyPI or GitLab repositories:

.. code-block:: bash

    pip3 install pluggable-namespace

Creating a pluggable application can be accomplished with just a few lines of code. The heart of every pluggable-namespace project is the creation of a hub, adding dynamic subsystems, and interacting with them through the hub's namespace.

.. code-block:: python

    import pns
    import asyncio

    loop = asyncio.get_event_loop()
    asyncio.run(main())

    async def main():
        async with pns.Hub() as hub:
            await hub.my_sub.init.cli()

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

Create a pns config file:

.. code-block:: yaml

    # Default location is ~/.pns/config.yaml
    # To change, set the PNS_CONFIG environment variable
    pns_cli:
      # Setting this will persist your hub on the CLI between calls
      hub_state: ~/.pns/hub.pkl
    log:
      log_plugin: async

From the example above, all arguments are loaded onto the namespace under hub.OPT.my_namespace. One ``config.yaml`` can add configuration options to multiple namespaces. They are merged in the order found in sys.path.

Extending Namespaces
====================
Extending ``pluggable-namespace`` is straightforward with dynamic namespaces. Extend any dynamic namespace on the hub by adding a directory containing a "config.yaml" to PYTHONPATH.

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/path/to/my/code

Add a config.yaml to that directory:

.. code-block:: yaml

    #/path/to/my/code/config.yaml
    dyne:
      namespace:
        - src

Now, every Python file in ``/path/to/my/code/src/`` will be added to the hub under ``hub.namespace``.

Testing
=======
Clone the repository:

.. code-block:: bash

    git clone https://gitlab.com/tac_tech/pluggable-namespace.git
    cd pluggable-namespace

Install ``pluggable-namespace`` with the testing extras:

.. code-block:: bash

    pip3 install .\[test\]

Run the tests in your cloned fork of Pluggable Namespace:

.. code-block:: bash

    pytest tests