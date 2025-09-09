import os
import logging
from typing import Dict, Optional
from dotenv import load_dotenv
from infisical_sdk import InfisicalSDKClient

logger = logging.getLogger(__name__)


class InfisicalSecretManager:
    def __init__(self, host: str, project_id: str, server_token: str, environment_slug: str, secret_path: str):
        self.project_id = project_id
        self.environment_slug = environment_slug
        self.secret_path = secret_path
        self.client = InfisicalSDKClient(host=host, token=server_token)

    def get_secret(self, secret_name: str) -> str:
        secret = self.client.secrets.get_secret_by_name(
            secret_name=secret_name,
            project_id=self.project_id,
            environment_slug=self.environment_slug,
            secret_path=self.secret_path,
        )
        return secret.secretValue

    def get_secrets(self, secret_names: list[str]) -> Dict[str, str]:
        return {name: self.get_secret(name) for name in secret_names}


def create_infisical_manager() -> InfisicalSecretManager:
    load_dotenv()
    server_token = os.getenv("INFISICAL_SERVER_TOKEN")
    project_id = os.getenv("INFISICAL_PROJECT_ID")
    host = os.getenv("INFISICAL_HOST")
    environment_slug = os.getenv("INFISICAL_ENVIRONMENT")
    secret_path = os.getenv("INFISICAL_SECRET_PATH")

    if not server_token:
        raise ValueError("INFISICAL_SERVER_TOKEN environment variable is required")
    if not project_id:
        raise ValueError("INFISICAL_PROJECT_ID environment variable is required")
    if not host:
        raise ValueError("INFISICAL_HOST environment variable is required")
    if not environment_slug:
        raise ValueError("INFISICAL_ENVIRONMENT environment variable is required")
    if not secret_path:
        raise ValueError("INFISICAL_SECRET_PATH environment variable is required")

    return InfisicalSecretManager(
        host=host,
        project_id=project_id,
        server_token=server_token,
        environment_slug=environment_slug,
        secret_path=secret_path,
    )
