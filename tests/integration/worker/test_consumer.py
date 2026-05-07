"""Integration tests for the SQS consumer against LocalStack.

Run from the worker service directory:
    cd worker && uv run --env-file ../.env pytest ../tests/integration/worker/ -m integration -v
"""

import json
import os
from unittest.mock import patch

import boto3
import pytest

LOCALSTACK_ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-central-1")
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "http://localhost:4566/000000000000/demo-queue")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require LocalStack (deselect with '-m not integration')",
    )


@pytest.fixture()
def sqs() -> boto3.client:
    """Return a boto3 SQS client pointed at LocalStack."""
    return boto3.client(
        "sqs",
        region_name=AWS_REGION,
        endpoint_url=LOCALSTACK_ENDPOINT,
        aws_access_key_id="test",
        aws_secret_access_key="test",  # pragma: allowlist secret
    )


def _enqueue(sqs_client: boto3.client, body: dict) -> str:
    """Send a raw message to demo-queue and return its MessageId."""
    response = sqs_client.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(body),
    )
    return response["MessageId"]


@pytest.mark.integration
def test_process_message_handles_job_requested_and_deletes_message(
    sqs: boto3.client,
) -> None:
    """_process_message should invoke handle_job and delete the message on success."""
    from app.events.consumer import _process_message

    message_id = _enqueue(
        sqs,
        {
            "detail-type": "JobRequested",
            "detail": {
                "job_id": "integ-01",
                "job_type": "echo",
                "parameters": {"x": 1},
            },
        },
    )

    resp = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
    )
    messages = resp.get("Messages", [])
    assert len(messages) == 1
    assert messages[0]["MessageId"] == message_id

    with patch("app.handlers.job_handler.handle_job") as mock_handle:
        _process_message(sqs, messages[0])

    mock_handle.assert_called_once_with(
        job_id="integ-01", job_type="echo", parameters={"x": 1}
    )

    # Message must be deleted — a second receive should return nothing.
    follow_up = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=2,
    )
    assert follow_up.get("Messages", []) == [], (
        "Message should have been deleted after processing"
    )


@pytest.mark.integration
def test_process_message_leaves_message_on_failure(
    sqs: boto3.client,
) -> None:
    """_process_message should NOT delete a message when handle_job raises.

    The message remains in-flight under the SQS visibility timeout so it will
    be re-delivered for retry — this is the intended back-pressure behaviour.
    Calling _process_message must not raise even when the handler fails.
    """
    from app.events.consumer import _process_message

    _enqueue(
        sqs,
        {
            "detail-type": "JobRequested",
            "detail": {"job_id": "integ-02", "job_type": "echo", "parameters": {}},
        },
    )

    resp = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
    )
    messages = resp.get("Messages", [])
    assert len(messages) == 1

    with patch(
        "app.handlers.job_handler.handle_job", side_effect=RuntimeError("db down")
    ):
        # _process_message must swallow the exception internally — it must not propagate.
        _process_message(sqs, messages[0])
