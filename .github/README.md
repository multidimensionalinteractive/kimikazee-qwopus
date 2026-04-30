# GitHub Configuration

This directory contains configuration files for the Kimikazee Qwopus project.

## 📁 Structure

```
.github/
├── workflows/          # GitHub Actions CI/CD workflows
│   ├── ci.yml         # Main CI pipeline
│   ├── release.yml    # Release pipeline
│   ├── codeql.yml     # Security scanning
│   └── docker.yml     # Docker build & deploy
├── ISSUE_TEMPLATE/     # Issue templates
├── PULL_REQUEST_TEMPLATE.md  # PR template
├── RELEASE_TEMPLATE.md    # Release notes template
└── CHANGELOG_TEMPLATE.md  # Changelog template
```

## 🔧 Workflow Files

### CI Pipeline (`ci.yml`)
- Runs on every push and pull request
- Tests on Python 3.10, 3.11, 3.12
- Code style checks (flake8, black, isort)
- Coverage reporting and upload to Codecov
- Type checking with mypy
- Security scanning

### Release Pipeline (`release.yml`)
- Triggers on semantic version tags (v1.0.0)
- Creates GitHub release with changelog
- Builds and attaches artifacts
- Builds and pushes Docker images
- Tags all artifacts

### Security Analysis (`codeql.yml`)
- CodeQL analysis for code vulnerabilities
- Dependency vulnerability scanning
- Secret detection (GitLeaks)
- Weekly scheduled runs

### Docker Build (`docker.yml`)
- Builds Docker images on push
- Pushes to Docker Hub (main branch)
- Pushes to GHCR (releases)
- Multi-platform support (amd64, arm64)
- Image scanning with Trivy

## 🚀 Quick Start

### Running Locally

```bash
# Test workflows locally with act
act -j lint
act -j test
act -j docker-build-test
```

### Manual Workflow Run

1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"
4. Choose branch/tag

## 🔑 Required Secrets

Configure these in Repository Settings > Secrets and variables:

| Secret | Description |
|--------|-------------|
| `CODECOV_TOKEN` | Codecov upload token |
| `DOCKER_HUB_USERNAME` | Docker Hub username |
| `DOCKER_HUB_TOKEN` | Docker Hub access token |
| `GITHUB_TOKEN` | GitHub token (auto-generated) |

## 📊 Workflow Status

View workflow runs at: https://github.com/kimikazee/kimikazee-qwopus/actions

---

*Kimikazee Qwopus CI/CD Documentation*
