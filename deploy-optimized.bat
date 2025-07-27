@echo off
REM deploy-optimized.bat - Optimized Cloud Run Deployment for WalleteriumImperium

echo 🚀 WalleteriumImperium - Optimized Cloud Run Deployment
echo =====================================================

REM Configuration
set PROJECT_ID=walleterium
set REGION=asia-south1
set SERVICE_NAME=walleterium-imperium
set SERVICE_ACCOUNT=walleterium-sa
set GEMINI_MODEL=gemini-2.5-flash
set REPOSITORY_NAME=walleterium-repo

echo 📋 Deployment Configuration:
echo   Project ID: %PROJECT_ID%
echo   Region: %REGION% (Mumbai - as per user preference)
echo   Service Name: %SERVICE_NAME%
echo   Service Account: %SERVICE_ACCOUNT%
echo   Gemini Model: %GEMINI_MODEL%
echo.

REM Enable required APIs
echo 🔧 Enabling required Google Cloud APIs...
gcloud services enable ^
    cloudbuild.googleapis.com ^
    run.googleapis.com ^
    artifactregistry.googleapis.com ^
    aiplatform.googleapis.com ^
    firestore.googleapis.com

if %errorlevel% neq 0 (
    echo ❌ Failed to enable APIs
    exit /b 1
)

REM Create Artifact Registry repository (ignore if exists)
echo 🗃️ Creating Artifact Registry repository...
gcloud artifacts repositories create %REPOSITORY_NAME% ^
    --repository-format=docker ^
    --location=%REGION% ^
    --description="WalleteriumImperium Docker repository" 2>nul

REM Configure Docker authentication
echo 🔐 Configuring Docker authentication...
gcloud auth configure-docker %REGION%-docker.pkg.dev

REM Create service account (ignore if exists)
echo 👤 Creating service account...
gcloud iam service-accounts create %SERVICE_ACCOUNT% ^
    --display-name="WalleteriumImperium Service Account" 2>nul

REM Grant permissions
echo 🔑 Granting IAM permissions...
set SERVICE_ACCOUNT_EMAIL=%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding %PROJECT_ID% ^
    --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" ^
    --role="roles/storage.objectViewer"

REM Generate timestamp for image versioning
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%-%HH%%Min%"

set IMAGE_TAG=v%TIMESTAMP%
set IMAGE_NAME=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%SERVICE_NAME%:%IMAGE_TAG%
set IMAGE_LATEST=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%SERVICE_NAME%:latest

echo 🐳 Building optimized Docker image...
echo   Image: %IMAGE_NAME%
docker build --platform linux/amd64 --no-cache -t %IMAGE_NAME% -t %IMAGE_LATEST% .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed - check Dockerfile and dependencies
    exit /b 1
)

echo 📤 Pushing image to Artifact Registry...
docker push %IMAGE_NAME%
docker push %IMAGE_LATEST%

if %errorlevel% neq 0 (
    echo ❌ Docker push failed - check authentication and network
    exit /b 1
)

echo 🚀 Deploying to Cloud Run with optimized configuration...
gcloud run deploy %SERVICE_NAME% ^
    --image=%IMAGE_NAME% ^
    --platform=managed ^
    --region=%REGION% ^
    --service-account="%SERVICE_ACCOUNT_EMAIL%" ^
    --allow-unauthenticated ^
    --memory="1Gi" ^
    --cpu="1" ^
    --timeout="300" ^
    --concurrency="80" ^
    --min-instances="0" ^
    --max-instances="5" ^
    --port="8080" ^
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=%PROJECT_ID%,VERTEX_AI_LOCATION=%REGION%,VERTEX_AI_MODEL=%GEMINI_MODEL%,PORT=8080,LOG_LEVEL=INFO" ^
    --cpu-boost ^
    --execution-environment=gen2

if %errorlevel% neq 0 (
    echo ❌ Cloud Run deployment failed
    echo 💡 Check logs: gcloud logs read --service=%SERVICE_NAME% --limit=50
    exit /b 1
)

REM Get service URL and test endpoints
echo 📋 Getting service information...
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo.
echo ✅ Deployment successful!
echo ======================
echo 📝 Service URL: %SERVICE_URL%
echo 🏥 Health Check: %SERVICE_URL%/api/v1/health
echo 🏥 Live Check: %SERVICE_URL%/api/v1/health/live
echo 🏥 Ready Check: %SERVICE_URL%/api/v1/ready
echo 📚 API Docs: %SERVICE_URL%/docs
echo 📄 Receipt Upload: %SERVICE_URL%/api/v1/receipts/upload
echo 👤 Onboarding: %SERVICE_URL%/api/v1/onboarding
echo.

echo 🧪 Testing health endpoint...
timeout 10 curl -s "%SERVICE_URL%/api/v1/health/live" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Health check passed
) else (
    echo ⚠️  Health check failed - service may still be starting
)

echo.
echo 📊 Useful commands:
echo   View logs: gcloud logs read --service=%SERVICE_NAME% --limit=50
echo   Get service info: gcloud run services describe %SERVICE_NAME% --region=%REGION%
echo   Update traffic: gcloud run services update-traffic %SERVICE_NAME% --region=%REGION% --to-latest
echo.
echo 🎉 WalleteriumImperium is live at: %SERVICE_URL%

REM Optional: Open service URL in browser
set /p OPEN_BROWSER="Open service URL in browser? (y/n): "
if /i "%OPEN_BROWSER%"=="y" start "" "%SERVICE_URL%"

pause 