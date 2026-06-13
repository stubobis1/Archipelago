import sys
import os

# Ensure the Archipelago root is on sys.path so that both
# `test.bases` and `worlds.*` are importable in any pytest invocation,
# regardless of which directory pytest is launched from.
root = os.path.dirname(__file__)
if root not in sys.path:
    sys.path.insert(0, root)
