variable "bus_name" {
  description = "Name of the EventBridge custom event bus"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS queue that receives routed events"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}
