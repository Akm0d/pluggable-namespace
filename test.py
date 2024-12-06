from pathlib import Path
import sys
import pns.hub

hub = pns.hub.Hub()

for path in map(Path, sys.path):
    if path.is_dir():
        pns.hub.scan_filesystem_for_plugins(hub, path)

# Accessing component information with parent info
component_namespace = 'example.subsystem.example_module'
component = hub.get_component(component_namespace)
component_parent = hub.get_component_parent(component_namespace)

if component:
    print(f"Component '{component_namespace}' has parent '{component_parent}'")
