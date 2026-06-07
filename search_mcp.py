from fastmcp import FastMCP
from ddgs import DDGS

mcp = FastMCP("search")

@mcp.tool()
def search(title: str = "", description: str = "", max_results: int = 5) -> str:
    """
    搜索工具，根据标题和视频说明进行搜索
    搜索结果返回当作翻译的时候的上下文信息，帮助翻译工具更好地理解视频内容，从而生成更准确的字幕文本
    
    Args:
        title (str): 视频标题
        description (str): 视频说明
        max_results (int): 搜索结果数量，默认 5
    
    Returns:
        str: 搜索结果字符串
    """
    query = (title or description or "").strip()
    if not query:
        return ""

    max_results = max(1, min(max_results, 10))
    lines = []
    with DDGS() as ddgs:
        for index, item in enumerate(ddgs.text(query, max_results=max_results), start=1):
            result_title = item.get("title") or ""
            result_body = item.get("body") or ""
            lines.append(f"{index}. {result_title}\n{result_body}")

    return "\n\n".join(lines) if lines else "没有找到相关搜索结果。"


if __name__ == "__main__":
    mcp.run(transport="stdio")
