# White Buffalo MoMo Image Compressor - Frontend Dockerfile
# Multi-stage build for optimal image size and Apple Silicon (ARM64) support

# Stage 1: Build Vue 3 App with Vite
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve with lightweight Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
