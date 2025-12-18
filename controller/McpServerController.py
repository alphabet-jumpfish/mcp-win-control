from mcp.server.fastmcp import FastMCP


mcp = FastMCP("windos-mcp_win")

def register_service():
    # 直接将服务方法注册为工具
    # mcp.tool()(search_service.search_files)
    pass

@mcp.tool(
    name="search_files",
    description="搜索文件"
)
def search_files():
    # results = search_service.search_files()
    return None


if __name__ == '__main__':
    register_service()
mcp.run(transport="stdio")
