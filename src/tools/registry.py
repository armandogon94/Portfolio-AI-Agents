import logging
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

_TOOLS: dict[str, BaseTool] = {}


def register_tool(name: str):
    """Decorator to register a tool by name."""

    def decorator(cls):
        _TOOLS[name] = cls()
        logger.debug(f"Registered tool: {name}")
        return cls

    return decorator


def get_tool(name: str) -> BaseTool:
    """Get a registered tool by name."""
    if name not in _TOOLS:
        raise KeyError(f"Tool '{name}' not registered. Available: {list(_TOOLS.keys())}")
    return _TOOLS[name]


def get_all_tools() -> dict[str, BaseTool]:
    """Get all registered tools."""
    return dict(_TOOLS)


class ToolRegistry:
    """Namespace for tool registration functions."""

    register = staticmethod(register_tool)
    get = staticmethod(get_tool)
    get_all = staticmethod(get_all_tools)
