#!/bin/bash

# Monu OS v1 Deployment Script
# This script builds and deploys the Docker container

set -e  # Exit on any error

# Configuration - Update these with your actual values
DOCKER_HUB_USERNAME="your_dockerhub_username"
IMAGE_NAME="monu_os_v1"
TAG="latest"
FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${TAG}"

# Railway configuration (placeholder - update with actual values)
RAILWAY_PROJECT_ID="your_railway_project_id"
RAILWAY_SERVICE_ID="your_railway_service_id"
RAILWAY_API_TOKEN="your_railway_api_token"

echo "🚀 Starting Monu OS v1 deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image: ${FULL_IMAGE_NAME}"
docker build -t "${FULL_IMAGE_NAME}" .

# Tag the image as latest
docker tag "${FULL_IMAGE_NAME}" "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"

# Push to Docker Hub
echo "📤 Pushing image to Docker Hub..."
docker push "${FULL_IMAGE_NAME}"

echo "✅ Docker image pushed successfully: ${FULL_IMAGE_NAME}"

# Deploy to Railway (placeholder commands - update with actual Railway CLI commands)
echo "🚂 Deploying to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway (you may need to do this manually or use API token)
if [ -n "$RAILWAY_API_TOKEN" ]; then
    railway login --token "$RAILWAY_API_TOKEN"
else
    echo "⚠️  RAILWAY_API_TOKEN not set. Please login manually:"
    echo "railway login"
    railway login
fi

# Link to project (if not already linked)
if [ -n "$RAILWAY_PROJECT_ID" ]; then
    railway link "$RAILWAY_PROJECT_ID"
fi

# Deploy the service
if [ -n "$RAILWAY_SERVICE_ID" ]; then
    railway up --service "$RAILWAY_SERVICE_ID"
else
    railway up
fi

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Your Monu OS v1 is now running on Railway!"
echo "📊 Check your Google Sheets and Telegram for market updates."
echo ""
echo "🔧 Next steps:"
echo "   1. Set up GitHub repository secrets for automated deployment"
echo "   2. Configure environment variables in Railway dashboard"
echo "   3. Test the daily pipeline manually if needed"

# Optional: Run a quick test
echo ""
read -p "🧪 Do you want to run a quick connection test? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Running connection test..."
    docker run --rm \
        -e TVDATA_USERNAME="$TVDATA_USERNAME" \
        -e TVDATA_PASSWORD="$TVDATA_PASSWORD" \
        -e GOOGLE_SA_JSON_PATH="/tmp/service_account.json" \
        -e SHEETS_ID="$SHEETS_ID" \
        -e TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
        -e TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
        -v "$(pwd)/service_account.json:/tmp/service_account.json:ro" \
        "${FULL_IMAGE_NAME}" \
        python src/cli.py test
fi
