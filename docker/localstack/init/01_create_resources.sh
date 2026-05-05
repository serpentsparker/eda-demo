#!/bin/bash
# Create local AWS resources in LocalStack on startup.
set -euo pipefail

REGION="${DEFAULT_REGION:-eu-central-1}"
ENDPOINT="http://localhost:4566"

echo "Creating SQS queue..."
awslocal sqs create-queue \
    --queue-name demo-queue \
    --region "$REGION"

awslocal sqs create-queue \
    --queue-name demo-queue-dlq \
    --region "$REGION"

echo "Creating EventBridge event bus..."
awslocal events create-event-bus \
    --name demo-event-bus \
    --region "$REGION"

echo "Creating EventBridge rule to route JobRequested events to SQS..."
QUEUE_ARN=$(awslocal sqs get-queue-attributes \
    --queue-url "$ENDPOINT/000000000000/demo-queue" \
    --attribute-names QueueArn \
    --region "$REGION" \
    --query 'Attributes.QueueArn' \
    --output text)

awslocal events put-rule \
    --name job-requested-rule \
    --event-bus-name demo-event-bus \
    --event-pattern '{"source":["eda-demo.api"],"detail-type":["JobRequested"]}' \
    --state ENABLED \
    --region "$REGION"

awslocal events put-targets \
    --rule job-requested-rule \
    --event-bus-name demo-event-bus \
    --targets "Id=sqs-target,Arn=$QUEUE_ARN" \
    --region "$REGION"

echo "LocalStack resources created successfully."
