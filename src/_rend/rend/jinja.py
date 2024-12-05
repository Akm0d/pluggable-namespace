"""
Render jinja data
"""
async def __virtual__(hub):
    return "jinja2" in hub.lib, "Jinja is not available"

async def __init__(hub):
    class RenderSandboxedEnvironment(hub.lib.jinja2.sandbox.SandboxedEnvironment):
        """
        Jinja sandboxed environment that hide portion of hub
        """

        def __init__(self, safe_hub_refs: list[str], *args, **kwargs) -> None:
            self._safe_hub_refs = [hub.lib.re.compile(i) for i in safe_hub_refs]
            super().__init__(*args, **kwargs)

        def is_safe_attribute(self, obj: object, attr: str, value: object) -> bool:
            # Only allow safe hub references in Jinja environment
            return super().is_safe_attribute(obj, attr, value)

    hub._.RenderSandboxedEnvironment = RenderSandboxedEnvironment


async def render(hub, data):
    """
    Render the given data through Jinja2
    """
    env_args = {
        "extensions": [],
        "loader": hub.lib.jinja2.FileSystemLoader(hub.lib.os.getcwd()),
        "undefined": hub.lib.jinja2.StrictUndefined,
        "enable_async": True,
    }

    if hasattr(hub.lib.jinja2.ext, "do"):
        env_args["extensions"].append("jinja2.ext.do")
    if hasattr(hub.lib.jinja2.ext, "loopcontrols"):
        env_args["extensions"].append("jinja2.ext.loopcontrols")

    if hub.OPT.jinja.enable_sandbox:
        jinja_env = hub._.RenderSandboxedEnvironment(  # nosec
            safe_hub_refs=hub.OPT.jinja.sandbox_safe_hub_refs or [],
            **env_args,
        )
    else:
        jinja_env = hub.lib.jinja2.Environment(  # nosec
            **env_args,
        )

    def _base64encode(string):
        if string is None:
            return ""
        return hub.lib.base64.b64encode(string.encode()).decode()

    def _base64decode(string):
        if string is None:
            return ""
        return hub.lib.base64.b64decode(string.encode()).decode()

    jinja_env.filters["b64encode"] = _base64encode
    jinja_env.filters["b64decode"] = _base64decode

    if isinstance(data, bytes):
        data = data.decode("utf-8")

    try:
        template = jinja_env.from_string(data)
        ret = await template.render_async(hub=hub)
    except hub.lib.jinja2.exceptions.UndefinedError as exc:
        msg = f"Jinja variable: {exc.message}"
        raise hub.exc.rend.RenderError(msg) from exc
    except hub.lib.jinja2.exceptions.TemplateSyntaxError as exc:
        problem = []
        for arg in exc.args:
            if isinstance(arg, str):
                problem.append(arg)
            else:
                problem.append(str(arg))

        msg = f"Jinja syntax error: {' '.join(problem)}"
        raise hub.exc.rend.RenderError(msg) from exc
    return ret
