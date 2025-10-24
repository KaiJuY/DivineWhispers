#!/usr/bin/env bash
# Build script for Render.com deployment (Frontend)

set -o errexit  # Exit on error
set -o pipefail # Exit on pipe failure
set -o nounset  # Exit on undefined variable

echo "🚀 Starting Divine Whispers Frontend build process..."

# Change to frontend directory if we're in project root
if [ -d "divine-whispers-frontend" ]; then
    echo "📂 Changing to divine-whispers-frontend directory..."
    cd divine-whispers-frontend
fi

# 1. Install Node dependencies
echo "📦 Installing Node.js dependencies..."
npm ci --legacy-peer-deps

# 2. Create .env.production with backend URL
echo "🔧 Creating .env.production..."

# If BACKEND_URL doesn't have https://, add it
if [ -n "${BACKEND_URL:-}" ]; then
    # Check if BACKEND_URL already starts with http
    if [[ "$BACKEND_URL" =~ ^https?:// ]]; then
        FULL_BACKEND_URL="$BACKEND_URL"
    else
        FULL_BACKEND_URL="https://$BACKEND_URL"
    fi
else
    FULL_BACKEND_URL="https://divine-whispers-backend.onrender.com"
fi

cat > .env.production <<EOF
REACT_APP_API_BASE_URL=$FULL_BACKEND_URL
REACT_APP_ENV=production
EOF

echo "✅ Environment file created:"
cat .env.production

# 3. Build React app
echo "🏗️  Building React application..."
npm run build

# 4. Verify build output
echo "🔍 Verifying build output..."
if [ -d "build" ]; then
    echo "✅ Build directory found"
    ls -lh build/ || true
else
    echo "❌ ERROR: Build directory not found!"
    exit 1
fi

echo "✅ Build completed successfully!"
echo "🌟 Divine Whispers Frontend is ready for deployment"
