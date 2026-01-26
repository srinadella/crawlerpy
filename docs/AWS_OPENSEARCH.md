# AWS OpenSearch Configuration

## Overview

The web crawler application has been configured to use AWS OpenSearch for document indexing. This guide explains the setup and how to configure AWS credentials.

## AWS OpenSearch Endpoint

```
https://search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com
```

**Region:** us-east-1
**Port:** 443 (HTTPS)

## Configuration

### 1. Environment Variables

The application automatically reads AWS credentials from your environment. No additional credentials need to be stored in `.env`.

**Updated Configuration:**
```env
OPENSEARCH_HOST=search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_SCHEME=https
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_USER=          # Leave empty for AWS authentication
OPENSEARCH_PASSWORD=      # Leave empty for AWS authentication
```

### 2. AWS Credentials Setup

The application uses AWS Signature Version 4 authentication automatically. Credentials are obtained from (in order):

1. **Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_SESSION_TOKEN=your_session_token  # Optional, for temporary credentials
   ```

2. **AWS Credentials File** (`~/.aws/credentials`)
   ```ini
   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
   ```

3. **AWS Config File** (`~/.aws/config`)
   ```ini
   [default]
   region = us-east-1
   ```

4. **IAM Role** (if running on EC2 or ECS)
   - Automatically uses the attached IAM role
   - No manual credential configuration needed

### 3. IAM Permissions Required

Your AWS user or role needs the following permissions for OpenSearch:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "es:ESHttpPut",
        "es:ESHttpPost",
        "es:ESHttpGet",
        "es:ESHttpDelete",
        "es:ESHttpHead"
      ],
      "Resource": "arn:aws:es:us-east-1:*:domain/srisearch/*"
    }
  ]
}
```

## Installation

### Step 1: Install Dependencies

The required packages have been added to `requirements.txt`:
- `boto3` - AWS SDK for Python
- `opensearch-py` - OpenSearch Python client

```bash
cd /Users/sri/data/crawler
pip install -r requirements.txt
```

Or install just the AWS packages:
```bash
pip install boto3==1.28.0 opensearch-py==2.2.0
```

### Step 2: Configure AWS Credentials

Choose one of the methods above to set up your AWS credentials.

### Step 3: Start the Application

```bash
bash run.sh
```

The application will automatically:
1. Detect the AWS OpenSearch endpoint
2. Use AWS Signature Version 4 signing
3. Connect to the AWS OpenSearch domain

## How It Works

### Connection Flow

```
Application
    ↓
OpenSearch Client (opensearch_client.py)
    ↓
Detect AWS endpoint (contains "search-" and ".es.amazonaws.com")
    ↓
Load AWS credentials via boto3
    ↓
Create AWSV4SignerAuth
    ↓
Sign all HTTP requests with AWS Signature Version 4
    ↓
AWS OpenSearch Domain
```

### Code Implementation

The `OpenSearchClient` class automatically:

1. **Detects AWS OpenSearch:**
   ```python
   use_aws_auth = (
       'search-' in settings.OPENSEARCH_HOST and 
       '.es.amazonaws.com' in settings.OPENSEARCH_HOST
   )
   ```

2. **Extracts AWS Region from Hostname:**
   ```python
   region = settings.OPENSEARCH_HOST.split('.')[2]  # us-east-1
   ```

3. **Uses boto3 for Credentials:**
   ```python
   from opensearchpy import AWSV4SignerAuth
   import boto3
   
   credentials = boto3.Session().get_credentials()
   auth = AWSV4SignerAuth(credentials, region, 'es')
   ```

4. **Falls Back to Basic Auth if Needed:**
   - If AWS auth is unavailable, uses basic auth (for development)
   - If neither is available, connects without authentication

## Switching Between Local and AWS OpenSearch

### To Use Local OpenSearch:

1. Update `.env`:
   ```env
   OPENSEARCH_HOST=localhost
   OPENSEARCH_PORT=9200
   OPENSEARCH_SCHEME=http
   OPENSEARCH_VERIFY_CERTS=false
   ```

2. Restart the application

### To Use AWS OpenSearch:

1. Update `.env`:
   ```env
   OPENSEARCH_HOST=search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com
   OPENSEARCH_PORT=443
   OPENSEARCH_SCHEME=https
   OPENSEARCH_VERIFY_CERTS=true
   ```

2. Ensure AWS credentials are configured

3. Restart the application

## Testing the Connection

### Using the CLI

```bash
python3 << 'EOF'
from app.opensearch_client import get_opensearch_client

client = get_opensearch_client()
health = client.info()
print(f"✓ Connected to AWS OpenSearch")
print(f"  Cluster: {health['cluster_name']}")
print(f"  Version: {health['version']['number']}")
EOF
```

### Using the Web API

```bash
# Get OpenSearch health (after logging in)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/opensearch/health

# List indices
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/search/indices
```

## Troubleshooting

### Connection Refused

**Error:** `ConnectionError: Failed to establish a new connection`

**Solutions:**
1. Verify AWS OpenSearch domain is accessible:
   ```bash
   curl https://search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com/
   ```
2. Check AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```
3. Verify IAM permissions include OpenSearch actions

### AuthenticationException

**Error:** `AuthenticationException: {"message":"User: arn:aws:iam::... is not authorized"}`

**Solutions:**
1. Verify IAM user/role has OpenSearch permissions
2. Check AWS credentials are not expired
3. Add required IAM policy (see above)

### SSL Certificate Verification Failed

**Error:** `SSLError: ("Bad certificate",)`

**Solutions:**
1. Verify `OPENSEARCH_VERIFY_CERTS=true` in environment
2. Update CA certificates:
   ```bash
   pip install --upgrade certifi
   ```
3. For testing only (not recommended):
   ```
   OPENSEARCH_VERIFY_CERTS=false
   ```

## Performance Notes

- AWS OpenSearch automatically handles scalability and failover
- Request signing adds minimal overhead (microseconds)
- boto3 credentials are cached in memory and refreshed automatically
- All OpenSearch operations use HTTPS (encrypted in transit)

## Security Best Practices

1. **Use IAM Roles (Recommended)**
   - Run application on EC2/ECS with attached IAM role
   - No credential storage needed

2. **Use Temporary Credentials**
   - Prefer `AWS_SESSION_TOKEN` for short-lived access
   - Rotate credentials regularly

3. **Restrict Permissions**
   - Only grant OpenSearch permissions needed
   - Use resource-based policies when possible

4. **Encrypt at Rest**
   - AWS OpenSearch supports encryption at rest
   - Enable via AWS console for the domain

5. **Network Security**
   - Consider using VPC endpoint for private access
   - Restrict security group rules appropriately

## Switching Back to Local OpenSearch

If you want to switch back to local OpenSearch for development:

```bash
# Start local OpenSearch in Docker
docker run -d \
  -p 9200:9200 \
  -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:latest

# Update .env
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_SCHEME=http
OPENSEARCH_VERIFY_CERTS=false

# Restart application
bash run.sh
```

## Monitoring AWS OpenSearch

### Via AWS Console

1. Go to AWS OpenSearch Dashboard
2. Select "srisearch" domain
3. View:
   - Cluster health and status
   - Index management
   - Application logs
   - Index statistics

### Via API

```bash
# Get cluster health
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/admin/opensearch/health
```

## Documentation Links

- [AWS OpenSearch User Guide](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [OpenSearch Python Client](https://opensearch-py.readthedocs.io/)
- [AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/sigv4_signing.html)

