"""Read-only catalog projection for XRefKit repositories."""

from .catalog import XRefCatalog
from .client_cache import DocumentCacheProtocolError, XidDocumentCache
from .context_registry import PromptContextAssembler, SessionXidContextRegistry

__version__ = "0.1.5"


def main(argv: list[str] | None = None) -> int:
    from .server import main as server_main

    args = list(argv or [])
    if args and args[0] == "setup":
        from .setup import main as setup_main

        if len(args) > 1 and args[1] == "apply":
            return setup_main(["setup-apply", *args[2:]])
        return setup_main(args)
    if args and args[0] == "setup-apply":
        from .setup import main as setup_main

        return setup_main(args)
    if args and args[0] == "serve":
        args = args[1:]
    return server_main(args)

__all__ = [
    "DocumentCacheProtocolError",
    "PromptContextAssembler",
    "SessionXidContextRegistry",
    "XRefCatalog",
    "XidDocumentCache",
    "main",
    "__version__",
]
