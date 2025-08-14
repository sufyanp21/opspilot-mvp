variable "name" {}

resource "aws_sqs_queue" "ingestion" {
  name = "${var.name}-ingestion"
}

output "queue_url" { value = aws_sqs_queue.ingestion.id }


