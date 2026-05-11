output "sqs_queue_url" {
  description = "URL of the SQS queue"
  value       = module.sqs.queue_url
}

output "sqs_queue_arn" {
  description = "ARN of the SQS queue"
  value       = module.sqs.queue_arn
}

output "eventbridge_bus_arn" {
  description = "ARN of the EventBridge event bus"
  value       = module.eventbridge.bus_arn
}
