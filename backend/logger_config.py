import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


class LoggerManager:
    def __init__(self):
        self.loggers = {}

    def create_logger(self, name: str):
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, f"{name}.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        self.loggers[name] = logger
        return logger


logger_manager = LoggerManager()


def get_logger(name: str):
    return logger_manager.create_logger(name)


def log_api_request(endpoint, method, payload=None):
    logger = get_logger("api")

    logger.info(
        f"API Request | endpoint={endpoint} | method={method} | payload={payload}"
    )


def log_api_response(endpoint, response_code):
    logger = get_logger("api")

    logger.info(
        f"API Response | endpoint={endpoint} | status={response_code}"
    )


def log_agent_execution(agent_name, task):
    logger = get_logger("agents")

    logger.info(
        f"Agent Execution | agent={agent_name} | task={task}"
    )


def log_error(module, error):
    logger = get_logger("errors")

    logger.error(
        f"Error in {module} | {str(error)}"
    )


def log_file_creation(file_path):
    logger = get_logger("filesystem")

    logger.info(
        f"File Created | path={file_path}"
    )


def log_github_action(action, repo, status):
    logger = get_logger("github")

    logger.info(
        f"GitHub Action | action={action} | repo={repo} | status={status}"
    )


def initialize_logging():
    get_logger("api")
    get_logger("agents")
    get_logger("errors")
    get_logger("filesystem")
    get_logger("github")

    print("Logging system initialized")


if __name__ == "__main__":
    initialize_logging()

    log_api_request("/query", "POST", {"query": "test"})
    log_api_response("/query", 200)
    log_agent_execution("research_agent", "fetch news")
    log_file_creation("test.txt")
    log_github_action("create_repo", "example", "success")