#!/usr/bin/env python3
"""
Local development setup script for Project Raseed
Automates the setup of local development environment

Usage: python scripts/setup_local.py [--skip-docker] [--skip-deps]
"""

import subprocess
import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message: str):
    """Print step message with formatting"""
    print(f"\n{Colors.OKBLUE}🔧 {message}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def run_command(cmd: List[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run command and handle output"""
    try:
        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        raise

def check_python_version():
    """Check Python version compatibility"""
    print_step("Checking Python version")
    
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")

def check_docker():
    """Check if Docker is available"""
    print_step("Checking Docker availability")
    
    try:
        result = run_command(["docker", "--version"], check=False)
        if result.returncode == 0:
            print_success(f"Docker found: {result.stdout.strip()}")
            return True
        else:
            print_warning("Docker not found or not running")
            return False
    except Exception:
        print_warning("Docker not available")
        return False

def setup_python_environment(project_root: Path):
    """Setup Python virtual environment and dependencies"""
    print_step("Setting up Python environment")
    
    # Check if virtual environment exists
    venv_path = project_root / ".venv"
    
    if not venv_path.exists():
        print("   Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", ".venv"], cwd=project_root)
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")
    
    # Determine pip executable
    if os.name == 'nt':  # Windows
        pip_exe = venv_path / "Scripts" / "pip.exe"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix-like
        pip_exe = venv_path / "bin" / "pip"
        python_exe = venv_path / "bin" / "python"
    
    # Upgrade pip
    print("   Upgrading pip...")
    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    requirements_files = ["requirements.txt", "requirements-dev.txt"]
    
    for req_file in requirements_files:
        req_path = project_root / req_file
        if req_path.exists():
            print(f"   Installing dependencies from {req_file}...")
            run_command([str(pip_exe), "install", "-r", str(req_path)])
            print_success(f"Dependencies from {req_file} installed")
        else:
            print_warning(f"{req_file} not found, skipping")

def create_env_file(project_root: Path):
    """Create .env file with development settings"""
    print_step("Creating environment configuration")
    
    env_path = project_root / ".env"
    
    if env_path.exists():
        print_success(".env file already exists")
        return
    
    env_content = """# Project Raseed - Development Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
PORT=8080

# Google Cloud Configuration (for production deployment)
# GOOGLE_CLOUD_PROJECT=your-project-id
# VERTEX_AI_LOCATION=asia-south1

# Development Emulator Settings
USE_EMULATORS=true
FIRESTORE_EMULATOR_HOST=localhost:8080
VERTEX_AI_MOCK_HOST=localhost:8090

# Processing Configuration
MAX_RETRIES=3
PROCESSING_TIMEOUT=300
TOKEN_EXPIRY_MINUTES=10
MAX_IMAGE_SIZE_MB=10

# Performance Settings
ENABLE_CACHE=true
CACHE_TTL=3600

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000,http://localhost:8080
"""
    
    env_path.write_text(env_content)
    print_success(".env file created with development settings")

def create_test_data_structure(project_root: Path):
    """Create test data directory structure"""
    print_step("Creating test data structure")
    
    test_dirs = [
        "test-data",
        "test-data/receipts",
        "test-data/images",
        "test-data/mock-responses"
    ]
    
    for dir_path in test_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    # Create sample test files
    sample_receipt = project_root / "test-data" / "receipts" / "sample_receipt.json"
    if not sample_receipt.exists():
        sample_data = {
            "store_name": "Test Supermarket",
            "total": 1234.50,
            "items": [
                {"name": "Test Item 1", "price": 500.00},
                {"name": "Test Item 2", "price": 734.50}
            ]
        }
        
        sample_receipt.write_text(json.dumps(sample_data, indent=2))
        print_success("Sample test data created")

def setup_docker_environment(project_root: Path):
    """Setup Docker development environment"""
    print_step("Setting up Docker environment")
    
    # Create docker-compose.yml if it doesn't exist
    compose_file = project_root / "docker-compose.yml"
    
    if compose_file.exists():
        print_success("docker-compose.yml already exists")
    else:
        compose_content = """version: '3.8'
services:
  # FastAPI Backend
  raseed-backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=development
      - FIRESTORE_EMULATOR_HOST=firestore-emulator:8080
      - VERTEX_AI_MOCK_HOST=vertex-ai-mock:8090
    volumes:
      - .:/app
      - /app/.venv  # Exclude virtual environment
    depends_on:
      - firestore-emulator
      - vertex-ai-mock
    command: python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

  # Firestore Emulator
  firestore-emulator:
    image: gcr.io/google.com/cloudsdktool/google-cloud-cli:latest
    ports:
      - "8080:8080"  # Firestore
      - "4000:4000"  # UI
    command: >
      sh -c "gcloud emulators firestore start 
             --host-port=0.0.0.0:8080 
             --rules=/dev/null"
    environment:
      - CLOUDSDK_CORE_PROJECT=raseed-dev

  # Mock Vertex AI Service
  vertex-ai-mock:
    build:
      context: ./dev-tools/vertex-ai-mock
      dockerfile: Dockerfile
    ports:
      - "8090:8090"
    environment:
      - MOCK_RESPONSE_DELAY=3000

  # Test Web Interface
  test-interface:
    build:
      context: ./dev-tools/test-interface
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - raseed-backend
"""
        
        compose_file.write_text(compose_content)
        print_success("docker-compose.yml created")
    
    # Create Dockerfile.dev
    dockerfile = project_root / "Dockerfile.dev"
    if not dockerfile.exists():
        dockerfile_content = """FROM python:3.11-slim as development

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \\
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash raseed
USER raseed

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/api/v1/health/live || exit 1

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
"""
        
        dockerfile.write_text(dockerfile_content)
        print_success("Dockerfile.dev created")

def create_helper_scripts(project_root: Path):
    """Create helper scripts for development"""
    print_step("Creating helper scripts")
    
    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # Create start_local.sh/bat
    if os.name == 'nt':  # Windows
        start_script = scripts_dir / "start_local.bat"
        start_content = """@echo off
echo Starting Project Raseed Local Development Environment
echo.

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

REM Start the application
echo Starting FastAPI server...
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

pause
"""
    else:  # Unix-like
        start_script = scripts_dir / "start_local.sh"
        start_content = """#!/bin/bash
echo "Starting Project Raseed Local Development Environment"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Start the application
echo "Starting FastAPI server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
"""
        # Make script executable
        os.chmod(start_script, 0o755)
    
    start_script.write_text(start_content)
    print_success(f"Start script created: {start_script.name}")

def verify_setup(project_root: Path):
    """Verify the setup is working"""
    print_step("Verifying setup")
    
    # Check if we can import the main modules
    try:
        # Add project root to Python path
        sys.path.insert(0, str(project_root))
        
        # Try importing main modules
        from app.core.config import get_settings
        from app.models import ProcessingStatus
        
        settings = get_settings()
        print_success(f"Configuration loaded: {settings.ENVIRONMENT} environment")
        print_success("Core modules importable ✓")
        
    except Exception as e:
        print_error(f"Setup verification failed: {e}")
        return False
    
    return True

def print_next_steps():
    """Print next steps for the user"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🎉 SETUP COMPLETE!{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.OKGREEN}Next steps:{Colors.ENDC}")
    
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
        start_cmd = "scripts\\start_local.bat"
    else:  # Unix-like
        activate_cmd = "source .venv/bin/activate"
        start_cmd = "./scripts/start_local.sh"
    
    steps = [
        f"1. Activate virtual environment: {Colors.OKCYAN}{activate_cmd}{Colors.ENDC}",
        f"2. Start the server: {Colors.OKCYAN}{start_cmd}{Colors.ENDC}",
        f"3. Test the API: {Colors.OKCYAN}python scripts/test_receipt.py{Colors.ENDC}",
        f"4. View API docs: {Colors.OKCYAN}http://localhost:8080/docs{Colors.ENDC}",
        f"5. Check health: {Colors.OKCYAN}http://localhost:8080/api/v1/health{Colors.ENDC}"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    print(f"\n{Colors.OKBLUE}For Docker development:{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}docker-compose up -d{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}docker-compose logs -f raseed-backend{Colors.ENDC}")
    
    print(f"\n{Colors.OKBLUE}Useful files created:{Colors.ENDC}")
    print(f"   📁 .env - Environment configuration")
    print(f"   📁 test-data/ - Sample test data")
    print(f"   🐳 docker-compose.yml - Docker environment")
    print(f"   🚀 scripts/ - Helper scripts")

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup Project Raseed local development environment")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker setup")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("🚀 Project Raseed - Local Development Setup")
    print("=" * 50)
    print(f"{Colors.ENDC}")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    print(f"Project root: {Colors.OKCYAN}{project_root}{Colors.ENDC}")
    
    try:
        # Step 1: Check requirements
        check_python_version()
        
        if not args.skip_docker:
            docker_available = check_docker()
        else:
            docker_available = False
        
        # Step 2: Setup Python environment
        if not args.skip_deps:
            setup_python_environment(project_root)
        
        # Step 3: Create configuration files
        create_env_file(project_root)
        
        # Step 4: Create test data structure
        create_test_data_structure(project_root)
        
        # Step 5: Setup Docker environment
        if not args.skip_docker and docker_available:
            setup_docker_environment(project_root)
        
        # Step 6: Create helper scripts
        create_helper_scripts(project_root)
        
        # Step 7: Verify setup
        if verify_setup(project_root):
            print_next_steps()
        else:
            print_error("Setup verification failed!")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print_warning("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()