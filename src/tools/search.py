from crewai.tools import BaseTool
from pydantic import Field
from src.tools.registry import register_tool


@register_tool("web_search")
class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = "Search the web for current information on any topic. Returns relevant search results."

    def _run(self, query: str) -> str:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return "No results found."

        output = []
        for r in results:
            output.append(f"**{r['title']}**\n{r['body']}\nSource: {r['href']}\n")
        return "\n".join(output)
