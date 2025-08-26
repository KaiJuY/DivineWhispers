@echo off
REM Development Environment Setup Script using UV for Windows

echo 🚀 Setting up Divine Whispers Backend Development Environment with UV

REM Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo 📦 Installing uv package manager...
    powershell -Command "& {irm https://astral.sh/uv/install.ps1 | iex}"
    REM Refresh environment
    call refreshenv
) else (
    echo ✅ uv is already installed
)

REM Create virtual environment with uv
echo 🐍 Creating virtual environment...
uv venv --python 3.11

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo 📦 Installing dependencies with uv...
uv pip install -r requirements.txt

REM Install development dependencies  
echo 🛠️ Installing development dependencies...
uv pip install -e ".[dev]"

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env file with your configuration
)

echo ✅ Development environment setup complete!
echo.
echo Next steps:
echo 1. Activate virtual environment: .venv\Scripts\activate
echo 2. Edit .env file with your configuration
echo 3. Start the development server: uvicorn app.main:app --reload
echo 4. Or use Docker: docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

pause