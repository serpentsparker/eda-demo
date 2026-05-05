"""Integration tests for the EventBridge → SQS event flow."""

import json
import time

import pytest

QUEUE_URL = "http://localhost:4566/000000000000/demo-queue"


@pytest.mark.integration
def test_job_requested_event_reaches_sqs(events_client, sqs_client) -> None:
    """Publishing a JobRequested event should result in a message in the SQS queue."""
    events_client.put_events(
        Entries=[
            {
                "Source": "eda-demo.api",
                "DetailType": "JobRequested",
                "Detail": json.dumps(
                    {"job_id": "test-01", "job_type": "echo", "parameters": {}}
                ),
                "EventBusName": "demo-event-bus",
            }
        ]
    )

    # Allow propagation time.
    time.sleep(1)

    response = sqs_client.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
    )
    messages = response.get("Messages", [])
    assert len(messages) == 1, "Expected exactly one message in the queue"

    body = json.loads(messages[0]["Body"])
    detail = json.loads(body["detail"])
    assert detail["job_id"] == "test-01"
