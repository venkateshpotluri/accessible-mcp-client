# CI/CD Pipeline Configuration

This repository includes a comprehensive CI/CD pipeline using GitHub Actions that automatically runs tests and code quality checks.

## Pipeline Features

- **Multi-Python Version Testing**: Tests are run on Python 3.8, 3.9, 3.10, 3.11, and 3.12
- **Code Quality Checks**: Automated linting with flake8, formatting checks with black, and import sorting with isort
- **Test Coverage**: Generates coverage reports and uploads to Codecov
- **Caching**: Optimized with pip dependency caching for faster builds

## GitHub Secrets Configuration

### Optional Secrets

- **CODECOV_TOKEN** - Token for uploading coverage reports to Codecov

## Setting Up Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the CODECOV_TOKEN secret if you want coverage reporting to Codecov

## Pipeline Triggers

The CI/CD pipeline runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

## Local Development Testing

Run the same checks locally before pushing:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check code formatting
black --check --diff .

# Check import sorting
isort --check-only --diff .

# Run tests with coverage
pytest -v --cov=. --cov-report=xml --cov-report=html
```


## Troubleshooting

### Common Issues

1. **Tests failing**
   - Check the GitHub Actions logs for detailed error messages
   - Ensure all dependencies are in requirements.txt
   - Run tests locally to debug issues

2. **Linting failures**
   - Run `black .` to auto-format code
   - Run `isort .` to fix import ordering
   - Fix any flake8 warnings manually

### Getting Help

- Check the GitHub Actions logs for detailed information
- Review the test output and coverage reports
- Ensure all secrets are properly configured