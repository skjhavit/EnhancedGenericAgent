"""
Azure Credential Manager
Centralized authentication management for Azure AD and Microsoft Graph API.
"""
import os
from typing import Optional
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from msgraph import GraphServiceClient
import logging

logger = logging.getLogger(__name__)


class AzureCredentialManager:
    """
    Singleton credential manager for Azure authentication.

    Supports:
    - Service Principal authentication (ClientSecretCredential)
    - Default Azure credential chain (for Azure-hosted environments)

    Environment Variables Required:
    - AZURE_TENANT_ID: Azure AD tenant ID
    - AZURE_CLIENT_ID: Service principal application (client) ID
    - AZURE_CLIENT_SECRET: Service principal client secret
    """

    _graph_client: Optional[GraphServiceClient] = None
    _credential: Optional[ClientSecretCredential] = None

    @classmethod
    def get_credential(cls) -> ClientSecretCredential:
        """
        Get or create Azure credential.

        Returns:
            ClientSecretCredential: Azure credential for authentication

        Raises:
            ValueError: If required environment variables are not set
        """
        if cls._credential is None:
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")

            if not all([tenant_id, client_id, client_secret]):
                raise ValueError(
                    "Azure credentials not configured. Please set environment variables: "
                    "AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET"
                )

            cls._credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            logger.info(
                f"Azure credential initialized for tenant: {tenant_id[:8]}... "
                f"(client: {client_id[:8]}...)"
            )

        return cls._credential

    @classmethod
    def get_graph_client(cls) -> GraphServiceClient:
        """
        Get or create Microsoft Graph API client.

        Returns:
            GraphServiceClient: Authenticated Graph API client

        Raises:
            ValueError: If credentials are not configured
        """
        if cls._graph_client is None:
            credential = cls.get_credential()

            # Microsoft Graph API requires specific scopes
            # .default scope includes all permissions granted to the service principal
            scopes = ["https://graph.microsoft.com/.default"]

            cls._graph_client = GraphServiceClient(
                credentials=credential,
                scopes=scopes
            )

            logger.info("Microsoft Graph client initialized successfully")

        return cls._graph_client

    @classmethod
    def is_configured(cls) -> bool:
        """
        Check if Azure credentials are configured in environment.

        Returns:
            bool: True if all required environment variables are set
        """
        return all([
            os.getenv("AZURE_TENANT_ID"),
            os.getenv("AZURE_CLIENT_ID"),
            os.getenv("AZURE_CLIENT_SECRET")
        ])

    @classmethod
    def reset(cls):
        """
        Reset cached credentials and clients.
        Useful for testing or credential rotation.
        """
        cls._credential = None
        cls._graph_client = None
        logger.info("Azure credentials reset")
