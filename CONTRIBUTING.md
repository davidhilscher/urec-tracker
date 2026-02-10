# Contributing to JMU UREC Capacity Tracker

Thank you for your interest in contributing to the UREC Capacity Tracker! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/jmu-urec-capacity.git
   cd jmu-urec-capacity
   ```
3. **Set up the development environment** following [SETUP.md](docs/SETUP.md)
4. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Making Changes

1. Make your changes in your feature branch
2. Follow the coding standards (see below)
3. Write or update tests as needed
4. Test your changes locally
5. Commit with clear, descriptive messages

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(frontend): add real-time WebSocket updates
fix(backend): prevent negative capacity counts
docs(api): update endpoint documentation
```

### Pull Requests

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request on GitHub
3. Provide a clear description of the changes
4. Link any related issues
5. Ensure all CI checks pass

## Coding Standards

### Python (Backend)

- **Style**: Follow PEP 8
- **Formatting**: Use `black` for code formatting
- **Linting**: Code should pass `flake8` checks
- **Type Hints**: Use type hints where appropriate
- **Docstrings**: Use Google-style docstrings

Example:
```python
def update_capacity(area_id: str, action: str) -> Optional[AreaCapacity]:
    """
    Update capacity count for an area.
    
    Args:
        area_id: Area identifier
        action: Either 'enter' or 'exit'
    
    Returns:
        Updated area capacity data, or None if not found
    """
    # Implementation here
```

### JavaScript (Frontend)

- **Style**: Follow Airbnb JavaScript Style Guide
- **ES6+**: Use modern JavaScript features
- **Comments**: Add JSDoc comments for functions
- **Naming**: Use camelCase for variables and functions

Example:
```javascript
/**
 * Fetch capacity data from the API
 * @returns {Promise<Array>} Array of area capacity objects
 */
async function fetchCapacityData() {
    // Implementation here
}
```

### HTML/CSS (Frontend)

- **HTML**: Use semantic HTML5 elements
- **CSS**: Follow BEM naming convention
- **Accessibility**: Ensure WCAG 2.1 AA compliance
- **Responsive**: Mobile-first design

## Testing

### Backend Tests

Run tests with pytest:
```bash
cd tests
pytest test_api.py -v
```

Write tests for new features:
```python
def test_new_feature():
    """Test description"""
    # Test implementation
```

### Frontend Tests

Manual testing checklist:
- [ ] Works in Chrome, Firefox, Safari
- [ ] Responsive on mobile devices
- [ ] Accessible with keyboard navigation
- [ ] No console errors

### Integration Tests

Test the full stack:
1. Start backend server
2. Open frontend in browser
3. Verify data loads correctly
4. Test all user interactions

## Documentation

Update documentation when making changes:

- **Code**: Add inline comments and docstrings
- **API**: Update `docs/API.md` for API changes
- **Architecture**: Update `docs/ARCHITECTURE.md` for structural changes
- **Setup**: Update `docs/SETUP.md` for setup changes
- **README**: Update main `README.md` as needed

## Issue Reporting

When reporting issues:

1. **Search existing issues** first
2. **Use issue templates** when available
3. **Provide details**:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, browser, etc.)
   - Screenshots if applicable

## Feature Requests

When suggesting features:

1. **Check existing feature requests**
2. **Explain the use case**
3. **Describe the proposed solution**
4. **Consider alternatives**
5. **Note any breaking changes**

## Code Review Process

All contributions go through code review:

1. Reviewer checks:
   - Code quality and style
   - Test coverage
   - Documentation
   - Performance implications
   - Security considerations

2. Address reviewer feedback
3. Re-request review after changes
4. Maintainer merges when approved

## Development Tips

### Local Development

```bash
# Backend
cd backend
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
python -m http.server 8080
```

### Environment Variables

Use `.env` files (never commit these):
```bash
# backend/.env
AWS_REGION=us-east-1
DYNAMODB_TABLE=urec-capacity-dev
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Database Testing

Use a separate DynamoDB table for development:
```bash
export DYNAMODB_TABLE=urec-capacity-dev
python scripts/init_database.py
```

### Debugging

- Backend: Add `import pdb; pdb.set_trace()` for breakpoints
- Frontend: Use browser DevTools
- Lambda: Check CloudWatch Logs

## Project Structure

```
jmu-urec-capacity/
├── frontend/          # Static website
├── backend/           # FastAPI application
├── lambda/            # AWS Lambda function
├── infrastructure/    # AWS configuration
├── docs/             # Documentation
├── tests/            # Test files
└── scripts/          # Utility scripts
```

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join our Discord/Slack (if available)
- **Email**: contact@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes
- README.md (for significant contributions)

Thank you for contributing! 🎉
