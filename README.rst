Pluggable Namespace
===================

**Pluggable Namespace** is a lightweight, modular framework for building pluggable software architectures with namespaces.
It empowers you to build applications that are easily extendable, with seamless integration of multiple modules.
Whether you're creating quick one-off scripts or a fully-fledged modular application, this framework provides the flexibility you need.

Installation
============

You can install ``pluggable-namespace`` from PyPI:

.. code-block:: bash

    pip install pluggable-namespace

Quick Start
===========

With **Pluggable Namespace**, you can write a single Python file and start building immediately.

Create a Python file called `my_file.py` with the following content:

.. code-block:: python

    def main(hub):
        print("Hello World!")

Then you can run your script from the CLI with the hub:

.. code-block:: bash

    hub my_file.py

That's it! This will execute the `main` function in `my_file.py`, and you will see "Hello World!" printed to the console.
This is the simplest way to get started with Pluggable Namespaces.


The Hub
========

The hub is the core of the pluggable namespace framework.
It provides a unified interface to access all the modules and functions in your application.
The hub is implicitly passed to every function in your application, allowing you to access all the modules and functions in your application.
You can use the hub to access any module or function in your application, as well as any external modules you have imported.
The hub is a singleton, meaning that there is only one instance of the hub in your application.
You can access the hub from anywhere in your application, and it will always be the same instance.

Configuration
=============

When building a pluggable-namespace app, all configuration settings are stored in a ``config.yaml`` file.

Here’s an example of what a `config.yaml` might look like:

.. code-block:: yaml

    # App configuration options for your namespaces that will show up under hub.OPT.my_namespace
    config:
      my_namespace:
        my_opt:
          os: MY_OPT_ENVIRONMENT_VARIABLE_NAME
          default: True

    # Python imports that your app uses, to be added to the hub.lib namespace for your app
    import:
      - asyncio
      - os
      - toml

The `config.yaml` file provides a way to manage configuration, subcommands, and imports for your app.
It will be automatically loaded based on the location of your Python files when running the hub.

Extending Namespaces
====================

You can extend **Pluggable Namespace** with local files or via a packaged python module on PyPI.

Locally
-------

Extending ``pluggable-namespace`` is straightforward with dynamic namespaces.
Extend any dynamic namespace on the hub by adding a directory containing a `config.yaml` to `PYTHONPATH`.

For example:

1. Add a `config.yaml` to a directory:

.. code-block:: yaml

    # /path/to/project_root/config.yaml
    dyne:
      namespace:
        - foo

2. Update your `PYTHONPATH`:

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/path/to/project_root

Now, every Python file in `/path/to/project_root/foo` will be added to the hub under `hub.namespace`.

With PyPI
---------

To jump-start your project, you can use the `seed` command to generate all the necessary boilerplate code for a pluggable namespace application:

.. code-block:: bash

    hub seed.init.cli /path/to/project_root name=my_project

Then, add your Python code to `/path/to/project_root/src/my_project`.
This will set up all the boilerplate code for your project in a way that will make it merge automatically onto the hub when installed from PyPi.

Example of Using the Hub
========================

After setting up your project, you can make use of the hub to call functions and access modules easily.

Here’s a more complex example showing how you can use the hub to access functions, shell commands, and configuration options:

.. code-block:: python

    #!/usr/bin/env hub

    # This tells the hub which function to use as an entrypoint when running the script
    __main__ = "my_main"

    # my_file.py
    async def func(Hub):
        print("Hello World!")

    async def my_main(hub):
        # Call a function in your python file from the hub
        await hub._.func()

        # Access a python module
        print(hub.lib.os.name)

        # Shell out
        await hub.sh.ls("-l")
        await hub.sh["ls"]("-l")

        # If you specified another file with "-f other_file.py" on the CLI, you can access its members like this
        await hub["other_file"].func()

        # Access a config option
        print(hub.OPT.my_namespace.my_opt)

Then you can run your script from the CLI with the hub:

.. code-block:: bash

    hub -f other_file.py my_file.py

This will execute the `main` function, calling functions from other files, accessing Python modules, and using configuration options set in `config.yaml`.

Classes
=======
In general, you should use plugins and contracts in place of classes.
Pluggable namespaces eliminate the need for objects, inheritence, and polymorphism.
Instead, you define an interface with contracts and implement it with plugins.
In pluggable-namespace, classes are for types -- plugin modules are for interfaces.

However, if you need to use classes, you can still do so.

When a python module is loaded onto the hub, it is scanned for functions, variables,and classes.
When a class is added to the hub, it is given the `hub` attrbiute, which is a reference to the main hub instance.
This allows you to access the hub from within your class methods, enabling you to call other functions, access configuration options, and use the hub's features seamlessly.

I.e.

.. code-block:: python

    class MyClass:
        def my_method(self):
            print(self.hub.lib.os.name)

Builtins
========
Once a hub is created, it adds itself to python's builtins, making it available globally as `__hub__`.
This is helpful for top-level actions such as type hinting and decorators:

.. code-block:: python

    @__hub__.lib.contexxtlib.asynccontextmanager
    async def my_async_context_manager(hub, var: __hub__.lib.typing.Any):
        print("Entering context")
        yield
        print("Exiting context")

Logging
=======
A logger is automatically created for each plugin module and is accessible via `hub.log`.
Logs are passed through an internal asyncio Queue on `hub.log.QUEUE`, allowing for easy unit tests on log messages.
Logging calls are non-blocking async tasks, but they can be awaited or ran synchronously without any problem.
The only difference between awaiting a log call and not awaiting is that awaiting it will free up a cycle for the event loop to process the log message sooner.

.. code-block:: python

    __hub__.log.debug("Top-level debug message")

    async def my_function(hub):
        await hub.log.info("This is an info message")
        hub.log.info("This is a synchronous message")


Summary
=======

**Pluggable Namespace** gives you the power to create modular, easily extendable applications without the bizarrely unnecessary complexity of other pluggable frameworks.

1. **Start Simple**: Create one Python file with minimal boilerplate, add `hub` to your functions, and run it directly from the command line.
2. **Add Flexibility**: Use `config.yaml` to scale your project with configuration settings, subcommands, and dynamic namespaces.
3. **Extend Easily**: Whether you're extending locally or developing for PyPI release, it's easy to integrate new modules and expand your app's functionality.

There are further READMEs in the projects that give more details on how to use advanced features of `pluggable-namespace`.
There are `contracts` which can be used to define an interface for dynamic namespaces (making it possible for others to easily extend your app's functionality).
There's config merging -- which allows multiple projects to seamlessly extend the same CLI interface.
And so much more!  If you have any questions, feel free to reach out or open an issue on GitHub.
