# TTS Light Novel - Docker Image Version Management

## Overview

This project uses a base Docker image (`kalekber/tts-base`) that contains shared dependencies for all workers. The base image is automatically built and pushed to Docker Hub when you create a new version tag.

## Versioning System

### Creating a New Base Image Version

1. **Make changes** to `libs/Dockerfile` or any shared dependencies in `libs/requirements.txt`

2. **Commit your changes**:
   ```bash
   git add libs/
   git commit -m "Update base image dependencies"
   ```

3. **Create and push a version tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. **GitHub Actions will automatically**:
   - Build the base image from `libs/Dockerfile`
   - Push it to Docker Hub as `kalekber/tts-base:v1.0.0`
   - Also tag it as `kalekber/tts-base:latest`

### Using a Specific Version Locally

You can control which base image version your workers use by setting the `TTS_BASE_VERSION` environment variable:

**Option 1: Using .env file** (recommended)
```bash
# Copy the example file if you haven't already
cp .env.example .env

# Edit .env and set the version
TTS_BASE_VERSION=v1.0.0
```

**Option 2: Inline environment variable**
```bash
TTS_BASE_VERSION=v1.0.0 docker compose up --build
```

**Option 3: Use latest (default)**
```bash
# This will use the latest tag
docker compose up --build
```

### Version Tag Format

Use semantic versioning for tags:
- `v1.0.0` - Major.Minor.Patch
- `v1.1.0` - Minor updates (new features)
- `v1.0.1` - Patch updates (bug fixes)

## GitHub Actions Setup

### Required Secrets

You need to add these secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password or access token

### Workflow File

The workflow is defined in `.github/workflows/build-base-image.yml` and will:
- Trigger on any tag push matching `v*.*.*`
- Build for both `linux/amd64` and `linux/arm64` platforms
- Push to Docker Hub with both the version tag and `latest` tag
- Use build cache for faster builds

## Architecture Details

### Worker Dockerfiles

All worker Dockerfiles now use a build argument for dynamic versioning:

```dockerfile
ARG VERSION=latest
FROM kalekber/tts-base:${VERSION}
```

This allows each worker to pull the correct base image version during build.

### Docker Compose Integration

The `docker-compose.yml` file passes the version to all workers:

```yaml
services:
  book-worker:
    build:
      context: workers/book
      dockerfile: Dockerfile
      args:
        VERSION: ${TTS_BASE_VERSION:-latest}
```

The `${TTS_BASE_VERSION:-latest}` syntax means:
- Use the `TTS_BASE_VERSION` environment variable if set
- Otherwise, default to `latest`

## Examples

### Example 1: Deploy with a specific version
```bash
# Set the version in .env
echo "TTS_BASE_VERSION=v1.2.3" > .env

# Build and start all services
docker compose up --build
```

### Example 2: Test a new version locally before tagging
```bash
# Build the base image locally with a test tag
docker build -t kalekber/tts-base:test ./libs

# Use the test version
TTS_BASE_VERSION=test docker compose up --build
```

### Example 3: Release a new version
```bash
# After testing, create and push the release tag
git tag v1.2.3
git push origin v1.2.3

# Wait for GitHub Actions to complete (~5 minutes)

# Pull the new version
docker pull kalekber/tts-base:v1.2.3

# Update your .env file
echo "TTS_BASE_VERSION=v1.2.3" > .env

# Rebuild workers with new base image
docker compose up --build
```

## Troubleshooting

### Build failing to find base image

If workers fail to build with "image not found" error:
```bash
# Pull the base image manually
docker pull kalekber/tts-base:latest

# Or build it locally
docker build -t kalekber/tts-base:latest ./libs
```

### Using development version

For development, you can build the base image locally without pushing:
```bash
# Build locally
docker build -t kalekber/tts-base:dev ./libs

# Use in docker-compose
TTS_BASE_VERSION=dev docker compose up --build
```

## Maintenance

### When to create a new version:

- ✅ Updating Python dependencies in `libs/requirements.txt`
- ✅ Adding new system packages to `libs/Dockerfile`
- ✅ Changing shared code in `libs/*.py`
- ✅ Security updates or patches
- ❌ Worker-specific changes (these go in `workers/*/`)
- ❌ Configuration changes in `docker-compose.yml`
