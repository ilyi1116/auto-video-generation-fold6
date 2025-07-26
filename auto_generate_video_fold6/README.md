# Voice Cloning System

A production-grade voice cloning system built with microservices architecture, emphasizing modularity, security, and maintainability.

## Architecture Overview

The system is built using a microservices architecture with the following core components:

- **API Gateway**: Single entry point for all client requests with routing and rate limiting
- **Authentication Service**: User management and JWT token handling
- **Data Ingestion Service**: Voice data processing and preprocessing
- **Training Worker**: Asynchronous model training using Celery
- **Inference Service**: Real-time voice synthesis
- **Frontend**: SvelteKit-based user interface

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend APIs | FastAPI (Python) | High-performance async APIs |
| Frontend | SvelteKit (Node.js) | Optimized user interface |
| Task Queue | Celery + Redis | Asynchronous ML training |
| Database | PostgreSQL | Structured data storage |
| Object Storage | S3-compatible | Audio files and models |
| Caching | Redis | Session data and rate limiting |
| Containerization | Docker | Service isolation and deployment |
| CI/CD | GitHub Actions | Automated testing and deployment |

## Project Structure

```
/
├── .github/
│   └── workflows/          # CI/CD workflows
├── services/
│   ├── api-gateway/        # API Gateway service
│   ├── auth-service/       # Authentication service
│   ├── data-ingestion/     # Data processing service
│   ├── training-worker/    # ML training worker
│   └── inference-service/  # Real-time inference
├── frontend/               # SvelteKit frontend
├── packages/
│   └── protos/             # Shared gRPC definitions
├── tests/                  # Integration tests
├── docs/                   # Documentation
├── docker-compose.yml      # Local development setup
└── pyproject.toml          # Python project configuration
```

## Quick Start

1. **Prerequisites**
   - Docker and Docker Compose
   - Python 3.11+
   - Node.js 20+

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Development Environment**
   ```bash
   docker-compose up -d
   ```

4. **Access Services**
   - Frontend: http://localhost:5173
   - API Gateway: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend && npm test
```

### Code Quality
```bash
# Python formatting
black services/

# Linting
flake8 services/
```

## Security

This project implements a multi-layered security approach:

- Container image scanning with Trivy
- Dependency vulnerability scanning with Snyk
- Non-root container execution
- Secure secret management
- Automated security gates in CI/CD

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and security checks
5. Submit a pull request

## License

[Add your license here]