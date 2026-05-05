"""Integration test fixtures — require LocalStack to be running."""

import os
from typing import TYPE_CHECKING


import pytest

if TYPE_CHECKING:
    import boto3

LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-central-1")


def pytest_configure(config: "pytest.Config") -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require LocalStack (deselect with '-m not integration')",
    )


@pytest.fixture(scope="session")
def sqs_client() -> "boto3.client":
    """Return a boto3 SQS client pointed at LocalStack."""
    import boto3

    return boto3.client(
        "sqs",
        region_name=AWS_REGION,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",  # pragma: allowlist secret
    )


@pytest.fixture(scope="session")
def events_client() -> "boto3.client":
    """Return a boto3 EventBridge client pointed at LocalStack."""
    import boto3

    return boto3.client(
        "events",
        region_name=AWS_REGION,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",  # pragma: allowlist secret
    )
