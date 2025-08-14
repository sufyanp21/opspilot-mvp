variable "name" {}

resource "aws_kms_key" "default" {
  description             = "KMS key for ${var.name}"
  deletion_window_in_days = 7
}

output "kms_key_id" { value = aws_kms_key.default.id }


