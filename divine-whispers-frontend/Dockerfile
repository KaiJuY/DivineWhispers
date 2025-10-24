# Multi-stage build for React frontend
# Stage 1: Build the React app
FROM node:18-alpine AS builder

# Accept build argument
ARG BACKEND_URL=https://divine-whispers-backend.onrender.com

WORKDIR /app

# Copy package files from frontend directory
COPY divine-whispers-frontend/package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code from frontend directory
COPY divine-whispers-frontend/ ./

# Set environment variable for React build
ENV REACT_APP_API_BASE_URL=${BACKEND_URL}
ENV REACT_APP_ENV=production

# Build the React app for production
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx config from frontend directory
COPY divine-whispers-frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
