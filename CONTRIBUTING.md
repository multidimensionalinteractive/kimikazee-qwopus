# Contributing to Kimikazee Qwopus 🐙

Thank you for your interest in contributing to Kimikazee Qwopus! This document provides guidelines and information to help you get started.

## 🎯 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. All contributors are expected to:

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards other community members

Please report unacceptable behavior to [team@kimikazee.com](mailto:team@kimikazee.com).

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip or poetry
- Docker (optional, for containerized development)
- git

### Development Setup

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/kimikazee-qwopus.git
   cd kimikazee-qwopus
   ```

3. **Install dependencies**
   ```bash
   # Install main dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

---

## Development Workflow

### Branch Strategy

We use a variation of Git Flow:

```
main              Production-ready code
develop          Development integration
feature/*       New features
bugfix/*        Bug fixes
release/*       Release preparation
hotfix/*        Emergency production fixes
```

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(server): add streaming response support
fix(config): handle missing environment variables
docs(readme): update installation instructions
```

---

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 120)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [flake8](https://flake8.pycqa.org/) for linting (max-complexity: 18)
- Add type hints using [mypy](https://mypy.readthedocs.io/)

### Pre-commit Checks

All code must pass:
```bash
pre-commit run --all-files
```

Or run individually:
```bash
black . --check
isort . --check-only
flake8 .
pytest tests/
```

### Code Quality Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| Black | Code formatting | `line-length = 120` |
| isort | Import sorting | `profile = "black"` |
| flake8 | Linting | `max-line-length = 120` |
| mypy | Type checking | `strict = true` |
| bandit | Security scanning | `--severity-level high` |

---

## Pull Request Process

### Before Submitting

1. ✅ Ensure all tests pass
2. ✅ Run pre-commit hooks
3. ✅ Update documentation
4. ✅ Add tests for new features
5. ✅ Update CHANGELOG.md

### PR Template

Use the provided PR template:
- Summary of changes
- Related issues
- Testing performed
- Breaking changes (if any)
- Screenshots (if UI changes)

### Review Process

1. **Automated Checks**: CI must pass
2. **Code Review**: At least 1 maintainer approval required
3. **Tests**: All tests must pass
4. **Documentation**: Updates must be complete

### Merging

- Squash merge for feature branches
- Rebase merge for bug fixes
- Merge commit for documentation

---

## Testing Guidelines

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=server --cov-report=html

# Run specific test file
pytest tests/test_config.py -v

# Run with specific marker
pytest tests/ -m "integration"
```

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── __init__.py
├── test_config.py       # Configuration tests
├── test_server.py       # Server/API tests
├── test_models.py       # Model tests
└── utils/               # Test utilities
    ├── __init__.py
    └── helpers.py
```

### Test Types

- **Unit Tests**: Fast, isolated tests (mark with `@pytest.mark.unit`)
- **Integration Tests**: Test component interactions (mark with `@pytest.mark.integration`)
- **End-to-End Tests**: Full system tests (mark with `@pytest.mark.e2e`)

### Writing Good Tests

```python
import pytest
from server import load_config

def test_load_config_success(tmp_path):
    """Test successful config loading."""
    config_path = tmp_path / "test.yaml"
    config_path.write_text("model: test.gguf")
    
    config = load_config(str(config_path))
    
    assert config["model"] == "test.gguf"
```

### Test Coverage Target

- Overall: 80%+
- Core modules: 90%+
- All new code: 100%

---

## Documentation

### What to Document

- New features
- Configuration options
- API endpoints
- Code functions/classes
- Deployment procedures

### Documentation Format

- Use Google-style docstrings
- Keep README.md up to date
- Add examples for new features
- Update CHANGELOG.md

### Docstring Example

```python
def process_request(data: Dict) -> Response:
    """Process a request and return response.
    
    Args:
        data: Request data dictionary
        
    Returns:
        Response object with processed data
        
    Raises:
        ValueError: If data is invalid
        TimeoutError: If processing takes too long
        
    Example:
        >>> result = process_request({"key": "value"})
        >>> isinstance(result, Response)
        True
    """
```

---

## Security

### Reporting Vulnerabilities

If you discover a security vulnerability:

1. **DO NOT** create a public issue
2. Email security@kimikazee.com
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Security Best Practices

- Never commit secrets or API keys
- Use environment variables for sensitive data
- Keep dependencies updated
- Run security scans regularly
- Follow principle of least privilege

### Security Tools

```bash
# Check for vulnerabilities
pip-audit
safety check

# Scan for secrets
git ls-files | xargs gitleaks detect
```

---

## Getting Help

### Channels

- **Discussions**: GitHub Discussions
- **Issues**: GitHub Issues (bugs, features)
- **Chat**: [Discord Server](link)
- **Email**: team@kimikazee.com

### First-Time Contributors

Look for issues marked with:
- `good first issue`
- `help wanted`
- `beginner-friendly`

---

## Release Process

### Version Numbers

We use [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     └─ Bug fixes
  |     └─────── Backward-compatible features
  └───────────── Incompatible changes
```

### Releasing

1. Update CHANGELOG.md
2. Update version in code
3. Create release branch: `git checkout -b release/v1.2.3`
4. Run release workflow
5. Tag and publish

---

## FAQ

**Q: How do I get my PR reviewed quickly?**

A: Make it small, well-documented, and follow the template.

**Q: Can I work on multiple issues?**

A: Yes, but communicate with maintainers first.

**Q: How often is this project released?**

A: Monthly minor releases, quarterly major releases.

**Q: I'm new to open source, where should I start?**

A: Look for `good first issue` labels and reach out!

---

## Resources

- [Python Style Guide](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [FastAPI Style Guide](https://github.com/tiangolo/fastapi/blob/main/docs/en/source/docs/tutorial.rst)

---

## Thank You! 🙏

Your contributions make Kimikazee Qwopus better for everyone. We appreciate your time and effort!

---

*Last updated: 2026-04-30*
