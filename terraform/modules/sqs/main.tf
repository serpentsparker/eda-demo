resource "aws_sqs_queue" "dlq" {
  name = "${var.queue_name}-dlq"

  tags = {
    Environment = var.environment
  }
}

resource "aws_sqs_queue" "main" {
  name = var.queue_name

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.main.id
  policy    = data.aws_iam_policy_document.eventbridge_send.json
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "eventbridge_send" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.main.arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}
