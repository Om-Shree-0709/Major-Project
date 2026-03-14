class MCPToolRegistry:
    """
    Registry for MCP tools across different servers.
    """

    def __init__(self):
        self.tools = {}

    def register_tool(self, server_name, tool_name, handler):

        if server_name not in self.tools:
            self.tools[server_name] = {}

        self.tools[server_name][tool_name] = handler


    def get_tool(self, server_name, tool_name):

        if server_name not in self.tools:
            raise ValueError(f"Server {server_name} not registered")

        if tool_name not in self.tools[server_name]:
            raise ValueError(f"Tool {tool_name} not found")

        return self.tools[server_name][tool_name]


    def list_servers(self):
        return list(self.tools.keys())


    def list_tools(self, server_name):

        if server_name not in self.tools:
            return []

        return list(self.tools[server_name].keys())


    def execute(self, server_name, tool_name, *args, **kwargs):

        tool = self.get_tool(server_name, tool_name)
        return tool(*args, **kwargs)


registry = MCPToolRegistry()