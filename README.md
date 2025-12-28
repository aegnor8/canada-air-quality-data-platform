![AWS](https://img.shields.io/badge/AWS-S3-orange?logo=amazon-aws)
![Databricks](https://img.shields.io/badge/Databricks-Unity%20Catalog-red?logo=databricks)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)

# Air Quality Data Pipeline - Canada
Real-time air quality monitoring pipeline for Ontario using OpenAQ API, Databricks Unity Catalog, and AWS S3.

## Architecture
```
OpenAQ API  --->  Databricks (Processing)  --->  AWS S3 (Data Lake)
```

## Infrastructure Setup

### AWS Resources

**Region**: `us-east-1` (N. Virginia)

| Resource | Name | Purpose |
|----------|------|---------|
| S3 Bucket | `mattia-airquality-datalake-use1` | Data lake storage (Delta Lake) |
| IAM Role | `airquality-databricks-unity-catalog-role` | Cross-account access for Databricks |
| IAM Policy | `airquality-databricks-s3-policy` | S3 read/write permissions (least privilege) |

### Databricks Unity Catalog

| Object | Name | Purpose |
|--------|------|---------|
| Storage Credential | `airquality-s3-credential` | IAM Role authentication to S3 |
| External Location | `airquality-external-location` | Maps `s3://mattia-airquality-datalake-use1` to Unity Catalog |

### Security Configuration

Cross-account access implemented using IAM Role with Trust Relationship:

- **Trust Policy**: Authorizes Databricks AWS account to assume role via STS AssumeRole
- **External ID**: Prevents confused deputy attacks
- **Self-assuming role**: Required by Unity Catalog for credential vending
- **Least privilege**: Only necessary S3 actions granted (GetObject, PutObject, DeleteObject, ListBucket, GetBucketLocation)

## Data Architecture - Planned

Medallion Architecture:

| Layer | Path | Description |
|-------|------|-------------|
| Bronze | `/bronze` | Raw data from OpenAQ API |
| Silver | `/silver` | Cleaned and validated data |
| Gold | `/gold` | Aggregated metrics for analytics |

## Tech Stack

- **Cloud**: AWS (S3, IAM)
- **Data Platform**: Databricks (Unity Catalog, Delta Lake)
- **Data Source**: OpenAQ API (Python SDK)
- **Language**: Python, SQL

## Status

- [x] AWS S3 bucket provisioned
- [x] IAM Role with cross-account trust configured
- [x] Databricks Storage Credential created
- [x] Databricks External Location configured
- [ ] Unity Catalog (Catalog/Schema) setup
- [ ] Data ingestion pipeline
- [ ] Transformations (bronze → silver → gold)
- [ ] Scheduled jobs

## Next Steps

1. Create Unity Catalog structure (Catalog, Schemas)
2. Build ingestion pipeline from OpenAQ API
3. Implement data quality checks
4. Create analytics dashboards
