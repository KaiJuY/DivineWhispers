# Divine Whispers Backend - UV Setup Guide

This project uses [UV](https://github.com/astral-sh/uv), a fast Python package manager, instead of pip for significantly faster dependency installation.

## 🚀 Quick Start with UV

### **Option 1: Local Development**

#### **Install UV**
```bash
# On Unix/Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# Alternative: Install via pip
pip install uv
```

#### **Setup Development Environment**
```bash
# Clone the repository
git clone <your-repo>
cd Backend

# Run setup script
chmod +x scripts/dev-setup.sh
./scripts/dev-setup.sh  # Linux/macOS
# OR
scripts\dev-setup.bat    # Windows
```

#### **Manual Setup**
```bash
# Create virtual environment
uv venv --python 3.11

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Install dependencies (much faster than pip!)
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -e ".[dev]"

# Start development server
uvicorn app.main:app --reload
```

### **Option 2: Docker Development (Recommended)**

```bash
# Copy environment file
cp .env.example .env

# Start with UV-optimized Docker build
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Run migrations
docker-compose exec app python -m alembic upgrade head
```

## ⚡ **UV Performance Benefits**

### **Installation Speed Comparison**
```bash
# Traditional pip (slow)
pip install -r requirements.txt
# ⏱️ ~2-5 minutes

# With UV (fast!)
uv pip install -r requirements.txt
# ⚡ ~10-30 seconds
```

### **Why UV is Faster**
- **Parallel Downloads**: Downloads packages concurrently
- **Smart Caching**: Advanced dependency resolution and caching
- **Written in Rust**: Native performance vs Python-based pip
- **Zero Configuration**: Works out-of-the-box with existing requirements.txt

## 🛠️ **Development Commands**

We've created a Makefile with UV-optimized commands:

```bash
# Show all available commands
make help

# Install dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Start development server
make dev-server

# Docker development
make docker-up

# Database migrations
make migrate
```

## 📦 **Dependency Management**

### **Adding New Dependencies**
```bash
# Add to pyproject.toml, then:
uv pip install <package-name>

# Or add directly to requirements.txt, then:
uv pip install -r requirements.txt
```

### **Updating Dependencies**
```bash
# Update all dependencies
make update

# Or manually:
uv pip compile pyproject.toml -o requirements.txt
uv pip install -r requirements.txt
```

### **Lock Dependencies**
```bash
# Generate lock file for reproducible builds
make uv-lock
# Creates requirements-lock.txt with exact versions
```

## 🔧 **UV Configuration**

### **Project Structure**
```
Backend/
├── pyproject.toml          # Project metadata & dependencies
├── requirements.txt        # UV-compatible requirements
├── requirements-lock.txt   # Locked versions (generated)
├── Dockerfile             # UV-optimized Docker build
├── Makefile               # UV development commands
└── scripts/
    ├── dev-setup.sh       # Linux/macOS setup
    └── dev-setup.bat      # Windows setup
```

### **Environment Variables**
UV respects these environment variables:

```bash
# Use custom index URL
export UV_INDEX_URL=https://pypi.org/simple/

# Use custom cache directory
export UV_CACHE_DIR=~/.cache/uv

# Disable network access (offline mode)
export UV_OFFLINE=1
```

## 🐳 **Docker Integration**

The Dockerfile has been optimized for UV:

```dockerfile
# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install dependencies with uv (much faster!)
RUN uv pip install --system --no-cache -r requirements.txt
```

### **Build Performance**
```bash
# Traditional pip Docker build
docker build .
# ⏱️ ~3-8 minutes

# UV-optimized Docker build  
docker build .
# ⚡ ~30 seconds - 2 minutes
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **"uv command not found"**
```bash
# Ensure uv is in PATH
source ~/.cargo/env  # Linux/macOS
# Or restart terminal/IDE
```

#### **Permission Errors**
```bash
# Use --user flag for system installs
uv pip install --user -r requirements.txt
```

#### **Version Conflicts**
```bash
# Check installed versions
uv pip list

# Force reinstall
uv pip install --force-reinstall -r requirements.txt
```

### **Debugging UV**
```bash
# Verbose output
uv pip install -v -r requirements.txt

# Check dependency resolution
uv pip compile --dry-run pyproject.toml
```

## 📈 **Migration from Pip**

If you're migrating an existing project:

1. **Backup current environment**:
   ```bash
   pip freeze > backup-requirements.txt
   ```

2. **Install UV and create new environment**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv venv --python 3.11
   source .venv/bin/activate
   ```

3. **Install with UV**:
   ```bash
   uv pip install -r requirements.txt
   ```

4. **Verify everything works**:
   ```bash
   python -m pytest
   ```

## 🚀 **Production Deployment**

UV works seamlessly in production:

```bash
# Production Docker build uses UV
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or manual production setup
uv pip install --system --no-dev -r requirements.txt
```

## 📚 **Additional Resources**

- [UV Documentation](https://github.com/astral-sh/uv)
- [UV Performance Benchmarks](https://github.com/astral-sh/uv#benchmarks)
- [Python Project Structure Best Practices](https://docs.python.org/3/tutorial/modules.html)

---

**🎉 Enjoy the speed! UV makes dependency management fast and reliable.**