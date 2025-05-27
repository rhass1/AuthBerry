# Production Dockerfile for Vue frontend with Node.js serving
FROM node:23 AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production stage
FROM node:23-alpine

WORKDIR /app

# Install serve globally for serving static files and wget for health checks
RUN apk add --no-cache wget && \
    npm install -g serve

# Copy built assets from build stage
COPY --from=build /app/dist ./dist

# Expose port
EXPOSE 3000

# Serve the built Vue.js app
CMD ["serve", "-s", "dist", "-l", "3000", "--no-clipboard"] 