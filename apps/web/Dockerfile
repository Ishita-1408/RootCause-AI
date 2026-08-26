# syntax=docker/dockerfile:1
# -----------------------------------------------------------------------------
# RootCause AI — Frontend Production Dockerfile
# Multi-stage build: Node 20 builder -> Nginx unprivileged minimal runner.
# -----------------------------------------------------------------------------

# Stage 1: Build static assets
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package manifests
COPY package.json package-lock.json ./

# Install dependencies deterministically
RUN npm ci

# Copy configuration and source files
COPY tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src

# Build production bundle with TypeScript check
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Production Nginx Server
# -----------------------------------------------------------------------------
FROM nginx:alpine AS runner

WORKDIR /usr/share/nginx/html

# Remove default static files
RUN rm -rf ./*

# Copy built frontend assets from builder
COPY --from=builder /app/dist .

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose standard HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/healthz || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
