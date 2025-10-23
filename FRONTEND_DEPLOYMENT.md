# Frontend Deployment Guide for Render.com

## Overview

Your Divine Whispers frontend is now configured for deployment on Render.com using Docker and nginx.

## Files Created

### 1. `divine-whispers-frontend/Dockerfile`
Multi-stage Docker build:
- **Stage 1**: Builds the React app using Node.js
- **Stage 2**: Serves the built files using nginx

### 2. `divine-whispers-frontend/nginx.conf`
Nginx configuration with:
- React Router support (SPA routing)
- Gzip compression
- Security headers
- Static file caching
- Health check endpoint at `/health`

### 3. `divine-whispers-frontend/build.sh`
Build script that:
- Installs npm dependencies
- Creates `.env.production` with backend URL
- Builds the React app
- Verifies build output

### 4. `divine-whispers-frontend/.dockerignore`
Excludes unnecessary files from Docker build

### 5. `render.yaml` (Updated)
Added frontend service configuration with automatic backend URL injection

## Deployment Steps

### Option 1: Using render.yaml Blueprint (Recommended)

Since you already have the backend deployed and `render.yaml` is configured:

1. **Commit and push all changes:**
   ```bash
   git add .
   git commit -m "Add frontend deployment configuration for Render"
   git push origin main
   ```

2. **Render will automatically detect the updated render.yaml:**
   - The frontend service will be created automatically
   - Environment variables will be auto-configured
   - Backend and frontend will be linked automatically

3. **Wait for deployment to complete:**
   - Render will build both services
   - Frontend will be available at: `https://divine-whispers-frontend.onrender.com`
   - Backend will be available at: `https://divine-whispers-backend.onrender.com`

### Option 2: Manual Deployment via Render Dashboard

If you prefer to deploy manually or if auto-deploy doesn't work:

1. **Go to Render Dashboard:** https://dashboard.render.com

2. **Click "New +" → "Web Service"**

3. **Connect your repository** (if not already connected)

4. **Configure the service:**
   - **Name**: `divine-whispers-frontend`
   - **Region**: Oregon (same as backend)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: Docker
   - **Dockerfile Path**: `./divine-whispers-frontend/Dockerfile`
   - **Docker Context**: `.` (project root)
   - **Docker Build Context**: `.`

5. **Add environment variable:**
   - **Key**: `BACKEND_URL`
   - **Value**: `https://divine-whispers-backend.onrender.com`
   - (Or use "Link to service" to automatically get the backend URL)

6. **Set plan:**
   - Choose "Free"

7. **Advanced settings:**
   - **Build Command**: `bash divine-whispers-frontend/build.sh`
   - **Health Check Path**: `/health`

8. **Click "Create Web Service"**

## Environment Variables

The frontend uses these environment variables (automatically set during build):

- `BACKEND_URL`: URL of the backend API (injected from render.yaml)
- `REACT_APP_API_URL`: Created in `.env.production` during build
- `REACT_APP_ENV`: Set to "production"

## Updating Backend CORS Settings

After frontend deployment, you may need to update the backend's ALLOWED_HOSTS:

1. Go to **Backend Service** in Render Dashboard
2. Go to **Environment** tab
3. Update `ALLOWED_HOSTS` to include:
   ```
   https://divine-whispers-frontend.onrender.com,http://localhost:3000
   ```

## Verification

After deployment, verify:

1. **Frontend is running:**
   - Visit: `https://divine-whispers-frontend.onrender.com`
   - Should see the Divine Whispers UI

2. **Health check works:**
   - Visit: `https://divine-whispers-frontend.onrender.com/health`
   - Should return "healthy"

3. **Backend connection works:**
   - Try using features that call the API
   - Check browser console for any CORS errors

## Troubleshooting

### Build fails
- Check build logs in Render dashboard
- Verify `package.json` has all dependencies
- Check if `npm ci --legacy-peer-deps` works locally

### Frontend shows blank page
- Check browser console for errors
- Verify `REACT_APP_API_URL` is set correctly in build logs
- Check nginx is serving files from `/usr/share/nginx/html`

### API calls fail (CORS errors)
- Update backend `ALLOWED_HOSTS` to include frontend URL
- Make sure both services are using `https://` URLs

### Images or static assets don't load
- Check if files are in the `build` directory
- Verify nginx configuration serves static files correctly
- Check browser network tab for 404 errors

## Free Tier Limitations

On Render's free tier:
- Services spin down after 15 minutes of inactivity
- First request may take 30-50 seconds (cold start)
- 750 hours of runtime per month (shared across services)
- No custom domains without paid plan

## Next Steps

1. ✅ Deploy frontend using one of the methods above
2. ✅ Update backend ALLOWED_HOSTS to include frontend URL
3. ✅ Test the full application end-to-end
4. Consider setting up custom domain (requires paid plan)
5. Monitor logs and performance in Render dashboard

## Notes

- The frontend is built as a **static React app** served by nginx
- All API calls go to the backend service
- React Router handles client-side routing
- Build artifacts are created during Docker build (not at runtime)
