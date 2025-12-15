# Re-export EmailInvoiceFinderApp from the top-level poczta_faktury.py module.
# We load that file by path to avoid circular/import-name shadowing issues
# when both a package directory and a module file share the same name.

import importlib.util
import importlib.machinery
import os
from typing import Any

_here = os.path.dirname(__file__)
_root_module_path = os.path.abspath(os.path.join(_here, os.pardir, "poczta_faktury.py"))

if os.path.exists(_root_module_path):
    spec = importlib.util.spec_from_file_location("poczta_faktury_top_level", _root_module_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    loader = spec.loader  # type: ignore
    if loader is None:
        raise ImportError(f"Cannot load module from {_root_module_path}")
    loader.exec_module(module)  # type: ignore
    # Export the application class into the package namespace
    EmailInvoiceFinderApp = getattr(module, "EmailInvoiceFinderApp", None)
else:
    EmailInvoiceFinderApp = None

__all__ = ["EmailInvoiceFinderApp"]
