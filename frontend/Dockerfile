# syntax=docker/dockerfile:1.4
# Multi-stage build for optimized React application

# Base stage for dependencies
FROM oven/bun:1 AS dependencies

WORKDIR /app

# Copy package files for better layer caching
COPY package.json bun.lock ./

# Install dependencies with mount cache
RUN --mount=type=cache,target=/root/.bun \
    bun install --frozen-lockfile

# Development stage
FROM dependencies AS development

WORKDIR /app

# Copy source code
COPY . .

# Set development environment variables
ENV VITE_ENVIRONMENT=development
ENV VITE_LOG_LEVEL=debug

# Expose port for development
EXPOSE 5173

# Development command
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]

# Build stage
FROM dependencies AS builder

WORKDIR /app

# Copy source code
COPY . .

# Set build-time environment variables for Vite
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_BASE_URL=ws://localhost:8000
ARG VITE_ENVIRONMENT=production
ARG VITE_LOG_LEVEL=info
ARG VITE_AUTH_SECRET

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT
ENV VITE_LOG_LEVEL=$VITE_LOG_LEVEL
ENV VITE_AUTH_SECRET=$VITE_AUTH_SECRET

# Build the application with cache mount
RUN --mount=type=cache,target=/app/node_modules/.cache \
    bunx vite build

# Production stage
FROM nginx:alpine AS production

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Set proper permissions for static files
RUN chmod -R 755 /usr/share/nginx/html

# Create nginx user and group
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# Default to production stage 