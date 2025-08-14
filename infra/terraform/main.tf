terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { default = "us-east-1" }
variable "project" { default = "opspilot" }
variable "env" { default = "dev" }

locals {
  name = "${var.project}-${var.env}"
}

module "s3" {
  source = "./modules/s3"
  name   = local.name
}

module "kms" {
  source = "./modules/kms"
  name   = local.name
}

module "sqs" {
  source = "./modules/sqs"
  name   = local.name
}

module "ecr" {
  source = "./modules/ecr"
  name   = local.name
}


