@echo off
REM deploy-windows.bat - Deploy WalleteriumImperium to Cloud Run on Windows

echo 🚀 WalleteriumImperium - Cloud Run Deployment for Windows
echo ====================================================

REM Check if PROJECT_ID is set
if "%PROJECT_ID%"=="" (
    echo ❌ Please set PROJECT_ID environment variable
    echo Example: set PROJECT_ID=your-project-id
    pause
    exit /b 1
)

REM Check if REGION is set
if "%REGION%"=="" (
    echo ❌ Please set REGION environment variable
    echo Example: set REGION=us-central1
    pause
    exit /b 1
)

REM Set default values
if "%SERVICE_NAME%"=="" set SERVICE_NAME=walleterium-receipt-scanner
if "%SERVICE_ACCOUNT%"=="" set SERVICE_ACCOUNT=walleterium-sa
if "%GEMINI_MODEL%"=="" set GEMINI_MODEL=gemini-2.5-flash
if "%REPOSITORY_NAME%"=="" set REPOSITORY_NAME=walleterium-repo

echo 📋 Configuration:
echo   Project ID: %PROJECT_ID%
echo   Region: %REGION%
echo   Service Name: %SERVICE_NAME%
echo   Service Account: %SERVICE_ACCOUNT%
echo   Gemini Model: %GEMINI_MODEL%

REM Enable APIs
echo 🔧 Enabling required APIs...
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com firestore.googleapis.com

REM Create Artifact Registry repository
echo 🗃️ Creating Artifact Registry repository...
gcloud artifacts repositories create %REPOSITORY_NAME% --repository-format=docker --location=%REGION% --description="WalleteriumImperium Docker repository"

REM Configure Docker authentication
echo 🔐 Configuring Docker authentication...
gcloud auth configure-docker %REGION%-docker.pkg.dev

REM Create service account
echo 👤 Creating service account...
gcloud iam service-accounts create %SERVICE_ACCOUNT% --display-name="WalleteriumImperium Service Account"

REM Grant permissions
echo 🔑 Granting permissions...
set SERVICE_ACCOUNT_EMAIL=%SERVICE_ACCOUNT%@%PROJECT_ID%.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" --role="roles/datastore.user"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:%SERVICE_ACCOUNT_EMAIL%" --role="roles/run.invoker"

REM Generate timestamp for image tag
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%-%HH%%Min%%Sec%"

set IMAGE_TAG=v%TIMESTAMP%
set IMAGE_NAME=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%SERVICE_NAME%:%IMAGE_TAG%
set IMAGE_LATEST=%REGION%-docker.pkg.dev/%PROJECT_ID%/%REPOSITORY_NAME%/%SERVICE_NAME%:latest

echo 🐳 Building Docker image...
docker build --platform linux/amd64 -t %IMAGE_NAME% -t %IMAGE_LATEST% .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    pause
    exit /b 1
)

echo 📤 Pushing image to Artifact Registry...
docker push %IMAGE_NAME%
docker push %IMAGE_LATEST%

if %errorlevel% neq 0 (
    echo ❌ Docker push failed
    pause
    exit /b 1
)

echo 🚀 Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% ^
    --image=%IMAGE_NAME% ^
    --platform=managed ^
    --region=%REGION% ^
    --service-account="%SERVICE_ACCOUNT_EMAIL%" ^
    --allow-unauthenticated ^
    --memory="2Gi" ^
    --cpu="1" ^
    --timeout="300" ^
    --concurrency="10" ^
    --min-instances="0" ^
    --max-instances="10" ^
    --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT_ID=%PROJECT_ID%,VERTEX_AI_LOCATION=%REGION%,VERTEX_AI_MODEL=%GEMINI_MODEL%,PORT=8080" ^
    --port="8080"

if %errorlevel% neq 0 (
    echo ❌ Cloud Run deployment failed
    pause
    exit /b 1
)

REM Get service URL
for /f "tokens=*" %%i in ('gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"') do set SERVICE_URL=%%i

echo ✅ Deployment successful!
echo 📝 Service URL: %SERVICE_URL%
echo 🧪 Test endpoints:
echo   Health Check: %SERVICE_URL%/api/v1/health
echo   API Docs: %SERVICE_URL%/docs
echo   Receipt Upload: %SERVICE_URL%/api/v1/receipts/upload

echo 🎉 WalleteriumImperium is now live at: %SERVICE_URL%
pause 