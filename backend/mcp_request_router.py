class MCPRequestRouter:

    def __init__(self):
        self.routes = {}

    def register_route(self, command, server):

        self.routes[command] = server


    def route(self, command):

        if command not in self.routes:
            raise ValueError(f"No route found for {command}")

        return self.routes[command]


    def handle_request(self, command, payload):

        server = self.route(command)

        if hasattr(server, "handle"):
            return server.handle(payload)

        raise RuntimeError("Server cannot handle request")


router = MCPRequestRouter()