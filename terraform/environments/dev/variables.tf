variable "aws_profile" {
  description = "AWS credentials profile to use for authentication"
  type        = string
  default     = "default"
}

variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "sqs_queue_name" {
  description = "Name of the SQS queue"
  type        = string
  default     = "demo-queue"
}

variable "eventbridge_bus_name" {
  description = "Name of the EventBridge custom event bus"
  type        = string
  default     = "demo-event-bus"
}
