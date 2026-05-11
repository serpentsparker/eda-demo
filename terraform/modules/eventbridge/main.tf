resource "aws_cloudwatch_event_bus" "main" {
  name = var.bus_name

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_rule" "job_requested" {
  name           = "job-requested-rule"
  event_bus_name = aws_cloudwatch_event_bus.main.name
  event_pattern = jsonencode({
    source      = ["eda-demo.api"]
    detail-type = ["JobRequested"]
  })

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "sqs" {
  rule           = aws_cloudwatch_event_rule.job_requested.name
  event_bus_name = aws_cloudwatch_event_bus.main.name
  target_id      = "sqs-target"
  arn            = var.sqs_queue_arn
}
