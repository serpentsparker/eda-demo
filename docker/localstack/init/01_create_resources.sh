#!/bin/bash
# Create local AWS resources in LocalStack on startup.
set -euo pipefail

REGION="${DEFAULT_REGION:-eu-central-1}"
ENDPOINT="${LOCALSTACK_ENDPOINT:-http://localhost:4566}"

# Use the standard AWS CLI with an explicit endpoint so this script works both
# inside the LocalStack init container (where awslocal is available) and in CI
# (where only the standard aws CLI is present).
AWS="aws --endpoint-url $ENDPOINT"

echo "Creating SQS queue..."
$AWS sqs create-queue \
    --queue-name demo-queue \
    --region "$REGION"

$AWS sqs create-queue \
    --queue-name demo-queue-dlq \
    --region "$REGION"

echo "Creating EventBridge event bus..."
$AWS events create-event-bus \
    --name demo-event-bus \
    --region "$REGION"

echo "Creating EventBridge rule to route JobRequested events to SQS..."
QUEUE_ARN=$($AWS sqs get-queue-attributes \
    --queue-url "$ENDPOINT/000000000000/demo-queue" \
    --attribute-names QueueArn \
    --region "$REGION" \
    --query 'Attributes.QueueArn' \
    --output text)

$AWS events put-rule \
    --name job-requested-rule \
    --event-bus-name demo-event-bus \
    --event-pattern '{"source":["eda-demo.api"],"detail-type":["JobRequested"]}' \
    --state ENABLED \
    --region "$REGION"

$AWS events put-targets \
    --rule job-requested-rule \
    --event-bus-name demo-event-bus \
    --targets "Id=sqs-target,Arn=$QUEUE_ARN" \
    --region "$REGION"

echo "LocalStack resources created successfully."
