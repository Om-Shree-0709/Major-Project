class RequestValidator:

    @staticmethod
    def validate_query_request(data):

        if not isinstance(data, dict):
            raise ValueError("Request must be JSON")

        if "query" not in data:
            raise ValueError("Missing 'query' field")

        if len(data["query"]) == 0:
            raise ValueError("Query cannot be empty")

        return True


    @staticmethod
    def validate_file_creation(data):

        required_fields = ["path", "content"]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing {field}")

        return True