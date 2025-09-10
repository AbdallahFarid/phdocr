# Coding Standards

## Core Standards
- **Languages & Runtimes:** Python 3.8+, PEP 8 compliance
- **Style & Linting:** black formatter, flake8 linter, mypy type checking
- **Test Organization:** pytest with test files matching `test_*.py` pattern

## Naming Conventions
| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `ChequeDataProcessor` |
| Functions | snake_case | `extract_payee_name()` |
| Variables | snake_case | `confidence_score` |
| Constants | UPPER_SNAKE_CASE | `MIN_CONFIDENCE_THRESHOLD` |
| Files | snake_case | `field_extractor.py` |

## Critical Rules
- **Logging Requirement:** Use structured logging, never print() statements in production code
- **Error Handling:** All external library calls must be wrapped in try-catch blocks
- **Type Hints:** All public methods must include type hints for parameters and return values
- **Configuration:** Never hardcode file paths or processing parameters - use configuration system
- **Resource Management:** Use context managers for file operations and external resources
