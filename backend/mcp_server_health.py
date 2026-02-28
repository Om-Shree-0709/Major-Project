import time


class MCPServerHealthManager:

    def __init__(self):
        self.servers = {}

    def register_server(self, name, server):

        self.servers[name] = {
            "server": server,
            "last_check": None,
            "status": "unknown"
        }


    def check_server(self, name):

        server_info = self.servers[name]

        server = server_info["server"]

        try:

            if hasattr(server, "ping"):
                server.ping()

            server_info["status"] = "healthy"

        except Exception:

            server_info["status"] = "unhealthy"

        server_info["last_check"] = time.time()


    def check_all(self):

        for name in self.servers:
            self.check_server(name)


    def get_status(self):

        return {
            name: info["status"]
            for name, info in self.servers.items()
        }


health_manager = MCPServerHealthManager()