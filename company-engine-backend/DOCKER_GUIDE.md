# Docker Guide for Social Intelligence Engine Backend

## Files Created

1. **Dockerfile** - Defines the Docker image for the application
2. **docker-compose.yml** - Orchestrates the services (updated to remove obsolete version field)
3. **.dockerignore** - Excludes unnecessary files from Docker builds

## Usage

### Option 1: Run the Complete Pipeline + API Server

This will run the data collection pipeline and then start the API server:

```bash
docker-compose up app
```

With a custom domain:
```bash
DOMAIN=stripe.com docker-compose up app
```

The API will be available at: http://localhost:8000

### Option 2: Run API Server Only

If you already have data and just want to run the API server:

```bash
docker-compose --profile api-only up api
```

The API will be available at: http://localhost:8001

### Option 3: Run Both Services Separately

Run the pipeline:
```bash
docker-compose up app
```

In another terminal, run the API server:
```bash
docker-compose --profile api-only up api
```

## Building

To rebuild the Docker image after making changes:

```bash
docker-compose build
```

To rebuild and start:
```bash
docker-compose up --build
```

## Data Persistence

The `./data` directory is mounted as a volume, so your SQLite database and reports will persist between container restarts.

## Stopping Services

Stop running services:
```bash
docker-compose down
```

Stop and remove volumes:
```bash
docker-compose down -v
```

## Viewing Logs

View logs in real-time:
```bash
docker-compose logs -f
```

View logs for a specific service:
```bash
docker-compose logs -f app
```

## Environment Variables

You can set the following environment variables:

- `DOMAIN` - The company domain to analyze (default: openai.com)
- `DATABASE_PATH` - Path to SQLite database (default: /app/data/social_intel.db)

Example:
```bash
DOMAIN=anthropic.com docker-compose up app
```

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, you can change it in docker-compose.yml:

```yaml
ports:
  - '8080:8000'  # Maps host port 8080 to container port 8000
```

### Permission Issues with Data Directory

If you get permission errors, make sure the `./data` directory exists and is writable:

```bash
mkdir -p data
chmod 755 data
```

### Rebuilding After Code Changes

After modifying Python code, rebuild the image:

```bash
docker-compose build
docker-compose up
```

## Accessing the API

Once running, you can access:

- **API Root**: http://localhost:8000/
- **Companies**: http://localhost:8000/companies
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Using with the Frontend

Make sure the frontend's `.env` file points to the correct API URL:

```
VITE_API_URL=http://localhost:8000
```

Then start the frontend separately:

```bash
cd ../company-engine-frontend
npm run dev
```

The frontend will be available at http://localhost:5173 and will connect to the Dockerized backend.
