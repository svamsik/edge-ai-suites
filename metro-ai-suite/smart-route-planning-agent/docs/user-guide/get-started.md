# Get Started

| **STATUS** |  Work in Progress |
|------------| ------------------|

## Prerequisites

Before you begin, ensure the following:

- **System requirements**: Verify that your system meets the [minimum requirements](./system-requirements.md).

- **Docker platform**: Install Docker platform. For installation instructions, see [Get Docker](https://docs.docker.com/get-docker/).

- You are familiar with Docker commands and using the terminal. If you are new to Docker platform, see [Docker Documentation](https://docs.docker.com/) for an introduction.

## Quick Start with Setup Script

| **STATUS** |  Work in Progress |
|------------| ------------------|

Intel recommends using the unified setup script `setup.sh` that configures, builds, deploys, and manages the Smart Route Planning Agent. 

1. Clone the repository:

```bash
git clone https://github.com/open-edge-platform/edge-ai-suites.git
cd edge-ai-suites/metro-ai-suite/smart-route-planning-agent
```

2. Run the complete setup:

The setup script provides several options. For a complete setup (recommended for first-time users):

```bash
source setup.sh --setup
```

3. Run alternative setup options

For a more granular control, run these commands:

```bash

# Start services only (after setup)
source setup.sh --run

# Stop services
source setup.sh --stop

# Restart services
source setup.sh --restart
```

## Manual Setup for Advanced Users

For advanced users who need more control over the configuration, you can set up the stack manually using Docker Compose tool.

### Manual Environment Configuration

<<<<<<< HEAD
If you prefer to configure environment variables manually instead of using the setup script, see the [Environment Variables Guide](./environment-variables.md) for details. 
=======
If you prefer to manually configure environment variables instead of using the setup script, see the [Environment Variables Guide](./environment-variables.md) for complete details.
>>>>>>> main

### Manual Docker Compose Tool Deployment

| **STATUS** |  Work in Progress |
|------------| ------------------|


## Configuration Files

The Smart Route Planning Agent stack uses several configuration files located in the `config/` directory:

### Smart Route Planning Agent Configuration

| **STATUS** |  Work in Progress |
|------------| ------------------|
