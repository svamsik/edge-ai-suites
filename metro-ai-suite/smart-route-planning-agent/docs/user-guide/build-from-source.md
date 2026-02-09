# Build from Source

This section shows how to build the Smart Route Planning Agent from source to customize, debug, or extend its functionality, for developers who want to work directly with the source code.

You will do the following:
- Set up your development environment.
- Compile the source code and resolve dependencies.
- Generate a runnable build for local testing or deployment.

## Prerequisites

- **System Requirements**: Verify that your system meets the [minimum requirements](./system-requirements.md).

- Basic familiarity with Git commands, Python virtual environments, and using the terminal. If you are new to these concepts, see:
  - [Git Documentation](https://git-scm.com/doc)
  - [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

## Build Smart Route Planning Agent

**(Optional)** Docker Compose tool builds the Smart Route Planning Agent with a default image and tag name. If you want to use a different image and tag, export these variables:

```bash
export REGISTRY_URL="your-container-registry_url"
export PROJECT_NAME="your-project-name"
export TAG="your_tag"
```

> **Note:** `PROJECT_NAME` will be suffixed to `REGISTRY_URL` to create a namespaced URL. The final image name will be created by suffixing the application name and tag with the namespaced URL. 

> **Example:** If variables are set using above command, the final image name for Smart Route Planning Agent will be `<your-container-registry-url>/<your-project-name>/scene-intelligence:<your-tag>`. 

If variables are not set, the `TAG` will have the default value, which is `latest`. Hence, the final image name will be `scene-intelligence:latest`.

1. Clone the repository:

```bash
git clone https://github.com/open-edge-platform/edge-ai-libraries.git edge-ai-libraries
cd edge-ai-libraries/microservices/scene-intelligence
```

2. Set up environment values:

Follow the instructions in the [Get Started](./get-started.md#set-environment-values) section to set up the environment variables.

3. Build the Docker image:

```bash
cd docker
docker compose -f docker/compose.yaml build scene-intelligence
```

4. Run the Docker image:

```bash
docker compose -f docker/compose.yaml up scene-intelligence
```

## Development Setup

For local development without Docker platform:

1. Set up Python Environment:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows OS: venv\Scripts\activate

# Or, Intel recommends setting up using the Poetry tool
poetry install
poetry shell
```

2. Install dependencies:

```bash
# Using pip
pip install -r requirements.txt

# Or, Intel recommends setting up using the Poetry tool
poetry install
```

3. Set up configuration files:

```bash
mkdir -p config
cp config/scene_intelligence_config.json.example config/scene_intelligence_config.json
cp config/vlm_config.json.example config/vlm_config.json
```

Edit the configuration files according to your environment.

4. Set environment variables:

```bash
export SCENE_INTELLIGENCE_CONFIG_PATH="./config/scene_intelligence_config.json"
export VLM_CONFIG_PATH="./config/vlm_config.json"
export MQTT_BROKER_HOST="localhost"
export MQTT_BROKER_PORT=1883
```

5. Run the service:

```bash
# Using the Poetry tool
poetry run python -m src.scene_intelligence.main

# Using pip
python -m src.scene_intelligence.main
```

## Test the build

1. Run unit tests:

```bash
# Using Poetry
poetry run pytest tests/

# Using pip
python -m pytest tests/
```

2. Run integration tests:

```bash
# Start required services (MQTT broker, VLM service)
docker compose -f docker/compose.yaml up mqtt-broker vlm-service -d

# Run integration tests
poetry run pytest tests/integration/

# Stop services
docker compose -f docker/compose.yaml down
```

3. Verify API endpoints:

```bash
# Health check
curl http://localhost:8001/health

# Configuration
curl http://localhost:8001/config

# Get available intersections
curl http://localhost:8001/api/v1/intersections

# Traffic summary
curl "http://localhost:8001/api/v1/traffic/directional/summary"

# Intersection traffic (use actual intersection ID from /intersections endpoint)
curl "http://localhost:8001/api/v1/traffic/directional/intersection/3d7b9e1f-c4a6-4f8e-b2d5-6a8c0e2f4b7d"
```

## Development Workflow

1. Run the following to ensure code quality:

```bash
# Format code
poetry run black src/
poetry run isort src/

# Lint code
poetry run flake8 src/
poetry run pylint src/

# Type checking
poetry run mypy src/
```

2. Run pre-commit hooks:

```bash
# Install pre-commit
poetry add --dev pre-commit

# Install hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

3. Generate API documentation:

```bash
# Generate API documentation
poetry run sphinx-build -b html docs/ docs/_build/html

# Serve documentation locally
cd docs/_build/html && python -m http.server 8080
```

## Deployment

1. Build for production:

```bash
# Build optimized Docker image
docker build -t scene-intelligence:production -f docker/Dockerfile.prod .

# Or using Docker Compose tool with production overrides
docker compose -f docker/compose.yaml -f docker compose -f docker/compose.yaml.yml -f docker compose -f docker/compose.yaml.prod.yml build
```

2. Build for multiple architectures:

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t scene-intelligence:latest .
```

3. Deploy on a Kubernetes Cluster

```bash
# Generate Kubernetes manifests
helm template scene-intelligence helm/scene-intelligence > k8s-manifests.yaml

# Deploy on a Kubernetes cluster
kubectl apply -f k8s-manifests.yaml
```

## Troubleshooting

### Common Issues

**Dependencies are not installed**:
- Ensure Python programming version 3.10+ is installed
- Update pip: `pip install --upgrade pip`
- Clear the Poetry cache: `poetry cache clear pypi --all`

**Import errors**:
- Verify PYTHONPATH includes the src directory
- Check that virtual environment is activated
- Ensure all dependencies are installed

**Configuration errors**:
- Validate JSON configuration files
- Check file paths in environment variables
- Verify that all required configuration sections are present

**Service does not start**:
- Check port availability
- Verify Message Queuing Telemetry Transport (MQTT) broker connectivity
- Review service logs for detailed error messages

### Debug Mode

Run the service in debug mode for detailed logging:

```bash
export LOG_LEVEL=DEBUG
poetry run python -m src.scene_intelligence.main
```

## Learn More

* [Get Started Guide](get-started.md)
* [Environment Variables](environment-variables.md)
* [System Requirements](system-requirements.md)
