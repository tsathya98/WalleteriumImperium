# Deployment

This directory contains deployment configurations and scripts for the Receipt Scanner agent.

## Deployment Options

### Local Development
```bash
# Install dependencies
poetry install

# Set environment variables
export GOOGLE_API_KEY="your-api-key"

# Run the agent
python -m receipt_scanner.agent
```

### Production Deployment
- Cloud Run deployment configurations
- Docker containerization
- Environment variable management
- Monitoring and logging setup

## Configuration Files
- `docker/`: Docker configurations
- `cloud/`: Cloud deployment scripts
- `env/`: Environment templates 