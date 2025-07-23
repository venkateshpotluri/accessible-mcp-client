# CI/CD Pipeline Configuration

This repository includes a comprehensive CI/CD pipeline using GitHub Actions that automatically runs tests, linting, and sends email notifications on success or failure.

## Pipeline Features

- **Multi-Python Version Testing**: Tests are run on Python 3.8, 3.9, 3.10, 3.11, and 3.12
- **Code Quality Checks**: Automated linting with flake8, formatting checks with black, and import sorting with isort
- **Test Coverage**: Generates coverage reports and uploads to Codecov
- **Email Notifications**: Sends success/failure emails after each CI/CD run
- **Caching**: Optimized with pip dependency caching for faster builds

## GitHub Secrets Configuration

To enable email notifications, configure the following secrets in your GitHub repository settings:

### Required Secrets

1. **SMTP_SERVER** - SMTP server address (e.g., `smtp.gmail.com`)
2. **SMTP_PORT** - SMTP server port (e.g., `587` for TLS, `465` for SSL)
3. **SMTP_USERNAME** - Email address for authentication
4. **SMTP_PASSWORD** - Email password or app-specific password
5. **NOTIFICATION_EMAIL** - Email address to receive notifications

### Optional Secrets

- **CODECOV_TOKEN** - Token for uploading coverage reports to Codecov

### Example SMTP Configuration

For Gmail:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAIL=notifications@yourcompany.com
```

For Outlook/Hotmail:
```
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
NOTIFICATION_EMAIL=notifications@yourcompany.com
```

## Setting Up Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with its corresponding value

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

## Email Notification Format

### Success Email
- Subject: "✅ CI/CD Pipeline Successful - [repository-name]"
- Contains: Repository info, branch, commit, triggered by, workflow run link

### Failure Email
- Subject: "❌ CI/CD Pipeline Failed - [repository-name]"
- Contains: Repository info, branch, commit, triggered by, failure details link

## Troubleshooting

### Common Issues

1. **Email notifications not working**
   - Check SMTP secrets are correctly set
   - Verify SMTP server settings
   - For Gmail, ensure you're using an App Password, not your regular password

2. **Tests failing**
   - Check the GitHub Actions logs for detailed error messages
   - Ensure all dependencies are in requirements.txt
   - Run tests locally to debug issues

3. **Linting failures**
   - Run `black .` to auto-format code
   - Run `isort .` to fix import ordering
   - Fix any flake8 warnings manually

### Getting Help

- Check the GitHub Actions logs for detailed information
- Review the test output and coverage reports
- Ensure all secrets are properly configured