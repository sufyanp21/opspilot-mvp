variable "name" {}

resource "aws_ecr_repository" "backend" {
  name = "${var.name}-backend"
  image_tag_mutability = "IMMUTABLE"
}

resource "aws_ecr_repository" "frontend" {
  name = "${var.name}-frontend"
  image_tag_mutability = "IMMUTABLE"
}

output "backend_repo" { value = aws_ecr_repository.backend.repository_url }
output "frontend_repo" { value = aws_ecr_repository.frontend.repository_url }


