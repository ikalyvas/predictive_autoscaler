import platform
import re

node = platform.node()
print(f"node is {node}")
if not re.search(r'container', node, re.I):
    print("Running server locally")
    from .local import *
else:
    from .dev import *
