## Infra Scaffold

Terraform stubs to provision core resources. No credentials required at this stage.

### Resources
- S3 buckets: raw and processed
- KMS keys for bucket encryption
- SQS ingestion queue
- IAM roles (least-privilege placeholders)
- ECR repositories for backend/frontend images

### Deploy Notes
- Configure backend/API to stream uploads directly to S3 Raw
- Use SQS + Step Functions/Batch for scalable normalization/recon
- Tag resources with `Tenant`, `Env`, and `Owner`


