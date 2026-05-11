module "sqs" {
  source      = "../../modules/sqs"
  queue_name  = var.sqs_queue_name
  environment = var.environment
}

module "eventbridge" {
  source        = "../../modules/eventbridge"
  bus_name      = var.eventbridge_bus_name
  sqs_queue_arn = module.sqs.queue_arn
  environment   = var.environment
}
