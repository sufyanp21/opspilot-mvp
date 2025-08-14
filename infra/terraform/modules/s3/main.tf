variable "name" {}

resource "aws_s3_bucket" "raw" {
  bucket = "${var.name}-raw"
}

resource "aws_s3_bucket" "processed" {
  bucket = "${var.name}-processed"
}

output "raw_bucket" { value = aws_s3_bucket.raw.id }
output "processed_bucket" { value = aws_s3_bucket.processed.id }


