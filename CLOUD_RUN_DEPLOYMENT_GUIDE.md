# WalleteriumImperium - Cloud Run Deployment Guide

## 🚨 Issues Fixed

### Critical Issues Identified and Resolved:

1. **Health Check Service Name Mismatch** ✅ FIXED
   - **Problem**: Health endpoints were trying to access `request.app.state.firestore` but service was stored as `firestore_service`
   - **Fix**: Updated all health check endpoints to use correct service names
   - **Files**: `app/api/health.py`

2. **Resource Over-allocation** ✅ FIXED  
   - **Problem**: Original deployment used 4 Gunicorn workers with 2GB memory, causing memory pressure
   - **Fix**: Reduced to 1 worker with 4 threads, optimized for 1GB memory limit
   - **Files**: `Dockerfile`

3. **Port Configuration** ✅ FIXED
   - **Problem**: Potential port misconfiguration for Cloud Run environment
   - **Fix**: Explicit PORT environment variable handling
   - **Files**: `app/core/config.py`

4. **Health Check Dependencies** ✅ FIXED
   - **Problem**: Health checks used `psutil` which might fail in containerized environment
   - **Fix**: Simplified health checks, removed unnecessary imports
   - **Files**: `app/api/health.py`

## 🚀 Optimized Deployment Strategy

### 1. Resource Configuration
```yaml
Memory: 1Gi (reduced from 2Gi)
CPU: 1 (reduced from 2)  
Workers: 1 worker + 4 threads (reduced from 4 workers)
Concurrency: 80 (optimized for memory usage)
Max Instances: 5 (reduced from 3 for better distribution)
```

### 2. Health Check Configuration
```yaml
Startup Probe: /api/v1/health/live (30 retries, 10s interval)
Liveness Probe: /api/v1/health/live (30s interval)  
Readiness Probe: /api/v1/ready (5s interval)
```

### 3. Performance Optimizations
- **CPU Boost**: Enabled for faster startup
- **Gen2 Execution Environment**: Better performance and features
- **Non-root user**: Security improvement
- **Multi-stage Docker build**: Smaller image size
- **Health check validation**: Proper startup detection

## 📋 Deployment Options

### Option 1: Use Optimized Script (Recommended)
```bash
deploy-optimized.bat
```

This script includes:
- Automatic API enablement
- Service account creation with proper permissions
- Optimized resource configuration
- Health check validation
- Comprehensive error handling

### Option 2: Manual gcloud Command
```bash
gcloud run deploy walleterium-imperium \
  --source . \
  --region=asia-south1 \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=5 \
  --timeout=300 \
  --concurrency=80 \
  --cpu-boost \
  --execution-environment=gen2 \
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=walleterium,VERTEX_AI_LOCATION=asia-south1,VERTEX_AI_MODEL=gemini-2.5-flash,PORT=8080,LOG_LEVEL=INFO"
```

### Option 3: YAML Configuration  
```bash
gcloud run services replace service.yaml --region=asia-south1
```

## 🏥 Health Check Endpoints

After deployment, verify these endpoints:

- **Liveness**: `https://your-service-url/api/v1/health/live`
- **Readiness**: `https://your-service-url/api/v1/ready`  
- **Detailed Health**: `https://your-service-url/api/v1/health`
- **API Docs**: `https://your-service-url/docs`

## 🔧 Troubleshooting

### Common Issues and Solutions:

1. **Service Not Starting**
   ```bash
   # Check logs
   gcloud logs read --service=walleterium-imperium --limit=50
   
   # Check service status
   gcloud run services describe walleterium-imperium --region=asia-south1
   ```

2. **Health Check Failures**
   - Verify endpoints are responding
   - Check service initialization in logs
   - Ensure all dependencies are properly initialized

3. **Memory Issues**
   - Monitor memory usage in Cloud Console
   - Consider increasing memory if needed
   - Check for memory leaks in application

4. **Timeout Issues**
   - Verify startup time is under 300 seconds
   - Check service initialization performance
   - Review application startup sequence

## 📊 Monitoring

### Key Metrics to Monitor:
- **Request Latency**: Should be < 2s for most requests
- **Memory Usage**: Should stay below 800MB
- **CPU Usage**: Should be efficiently utilized
- **Error Rate**: Should be < 1%
- **Cold Start Time**: Should be < 30s

### Useful Commands:
```bash
# View recent logs
gcloud logs read --service=walleterium-imperium --limit=50

# Monitor real-time logs  
gcloud logs tail --service=walleterium-imperium

# Get service metrics
gcloud run services describe walleterium-imperium --region=asia-south1

# Update service configuration
gcloud run services update walleterium-imperium --region=asia-south1 --memory=1Gi
```

## 🎯 Best Practices Applied

1. **Resource Right-sizing**: Optimized memory and CPU for actual usage
2. **Health Check Strategy**: Multiple probe types for comprehensive monitoring
3. **Security**: Non-root user, minimal permissions
4. **Performance**: CPU boost, Gen2 environment, optimized worker configuration
5. **Reliability**: Proper error handling, graceful shutdowns
6. **Observability**: Comprehensive logging and health endpoints

## 🔄 Next Steps

1. **Deploy using optimized script**: `deploy-optimized.bat`
2. **Monitor health endpoints**: Verify all services start properly
3. **Load test**: Ensure performance meets requirements
4. **Set up monitoring**: Configure alerts for key metrics
5. **Document API endpoints**: Update documentation with new URLs

## 📞 Support

If deployment issues persist:

1. Check the comprehensive logs using provided commands
2. Verify all environment variables are set correctly  
3. Ensure Docker image builds successfully locally
4. Validate health check endpoints respond correctly
5. Review resource limits and scaling configuration 