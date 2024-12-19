__virtualname__ = "yaml"


async def __init__(hub):
    hub.lib.yaml.Loader = hub.lib.yaml.CLoader
    hub.lib.yaml.Dumper = hub.lib.yaml.CDumper
    hub.lib.yaml.SafeLoader = hub.lib.yaml.CSafeLoader
    hub.lib.yaml.SafeDumper = hub.lib.yaml.CSafeDumper

    class YamlSafeLoader(hub.lib.yaml.SafeLoader):
        """
        Create a custom YAML loader that uses the custom constructor. This allows
        for the YAML loading defaults to be manipulated based on needs within rend
        to make YAML file reading more intuitive.
        """

        def __init__(self, stream, dictclass=dict):
            super().__init__(stream)
            if dictclass is not dict:
                # then assume ordered dict and use it for both !map and !omap
                self.add_constructor(
                    "tag:yaml.org,2002:map", type(self).construct_yaml_map
                )
                self.add_constructor(
                    "tag:yaml.org,2002:omap", type(self).construct_yaml_map
                )
            self.add_constructor("tag:yaml.org,2002:str", type(self).construct_yaml_str)
            self.add_constructor(
                "tag:yaml.org,2002:python/unicode", type(self).construct_unicode
            )
            self.add_constructor(
                "tag:yaml.org,2002:timestamp", type(self).construct_scalar
            )
            self.dictclass = dictclass

        def construct_yaml_map(self, node):
            data = self.dictclass()
            yield data
            value = self.construct_mapping(node)
            data.update(value)

        def construct_unicode(self, node):
            return node.value

        def construct_mapping(self, node, *, deep=False):
            """
            Build the mapping for YAML
            """
            if not isinstance(node, hub.lib.yaml.nodes.MappingNode):
                raise hub.lib.yaml.constructor.ConstructorError(
                    None,
                    None,
                    f"expected a mapping node, but found {node.id}",
                    node.start_mark,
                )

            self.flatten_mapping(node)

            context = "while constructing a mapping"
            mapping = self.dictclass()
            for key_node, value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError as e:
                    raise hub.lib.yaml.constructor.ConstructorError(
                        context,
                        node.start_mark,
                        f"found unacceptable key {key_node.value}",
                        key_node.start_mark,
                    ) from e
                value = self.construct_object(value_node, deep=deep)
                if key in mapping:
                    raise hub.lib.yaml.constructor.ConstructorError(
                        context,
                        node.start_mark,
                        f"found conflicting ID '{key}'",
                        key_node.start_mark,
                    )
                mapping[key] = value
            return mapping

        def construct_scalar(self, node):
            """
            Verify integers and pass them in correctly is they are declared
            as octal
            """
            if node.tag == "tag:yaml.org,2002:int":
                if node.value == "0":
                    pass
                elif node.value.startswith("0") and not node.value.startswith(
                    ("0b", "0x")
                ):
                    node.value = node.value.lstrip("0")
                    # If value was all zeros, node.value would have been reduced to
                    # an empty string. Change it to '0'.
                    if node.value == "":
                        node.value = "0"
            return super().construct_scalar(node)

        def construct_yaml_str(self, node):
            value = self.construct_scalar(node)
            return value

        def flatten_mapping(self, node):
            merge = []
            index = 0
            while index < len(node.value):
                key_node, value_node = node.value[index]

                if key_node.tag == "tag:yaml.org,2002:merge":
                    del node.value[index]
                    if isinstance(value_node, hub.lib.yaml.nodes.MappingNode):
                        self.flatten_mapping(value_node)
                        merge.extend(value_node.value)
                    elif isinstance(value_node, hub.lib.yaml.nodes.SequenceNode):
                        submerge = []
                        for subnode in value_node.value:
                            if not isinstance(subnode, hub.lib.yaml.nodes.MappingNode):
                                msg = "while constructing a mapping"
                                raise hub.lib.yaml.constructor.ConstructorError(
                                    msg,
                                    node.start_mark,
                                    f"expected a mapping for merging, but found {subnode.id}",
                                    subnode.start_mark,
                                )
                            self.flatten_mapping(subnode)
                            submerge.append(subnode.value)
                        submerge.reverse()
                        for value in submerge:
                            merge.extend(value)
                    else:
                        msg = "while constructing a mapping"
                        raise hub.lib.yaml.constructor.ConstructorError(
                            msg,
                            node.start_mark,
                            f"expected a mapping or list of mappings for merging, but found {value_node.id}",
                            value_node.start_mark,
                        )
                elif key_node.tag == "tag:yaml.org,2002:value":
                    key_node.tag = "tag:yaml.org,2002:str"
                    index += 1
                else:
                    index += 1
            if merge:
                # Here we need to discard any duplicate entries based on key_node
                existing_nodes = [
                    name_node.value for name_node, value_node in node.value
                ]
                mergeable_items = [x for x in merge if x[0].value not in existing_nodes]

                node.value = mergeable_items + node.value

    hub._.YamlSafeLoader = YamlSafeLoader


async def render(hub, data):
    """
    Given the data, attempt to render it as yaml
    """
    try:
        ret = hub.lib.yaml.load(data, Loader=hub._.YamlSafeLoader)
    except (
        hub.lib.yaml.parser.ParserError,
        hub.lib.yaml.constructor.ConstructorError,
        hub.lib.yaml.scanner.ScannerError,
        hub.lib.yaml.composer.ComposerError,
    ) as exc:
        problem = []
        for arg in exc.args:
            if isinstance(arg, str):
                problem.append(arg)
            elif hasattr(arg, "line") and hasattr(arg, "column"):
                problem.append(f"on line: {arg.line} column: {arg.column}")
            elif arg:
                problem.append(str(arg))
        msg = f"Yaml render error: {' '.join(problem)}"
        raise hub.exc.rend.RenderError(msg) from exc
    return ret
