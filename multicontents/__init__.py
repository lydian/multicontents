# flake8: noqa
try:
    import notebook.transutils
except ImportError:
    import jupyter_server.transutils
from multicontents.multicontents_manager import MultiContentsManager
