# UV Quick Reference

## Essential uv Commands

### Package Management

```bash
# Create virtual environment
uv venv

# Create venv with specific Python version
uv venv --python 3.11

# Install from requirements.txt
uv pip install -r requirements.txt

# Install in editable mode with extras
uv pip install -e ".[dev]"

# Add a new package
uv pip install package-name

# Add specific version
uv pip install package-name==1.2.3

# Install from git
uv pip install git+https://github.com/user/repo.git

# Upgrade package
uv pip install --upgrade package-name

# Uninstall package
uv pip uninstall package-name

# List installed packages
uv pip list

# Show package info
uv pip show package-name

# Freeze dependencies
uv pip freeze > requirements.txt
```

### Running Commands

```bash
# Run Python script
uv run python script.py

# Run module
uv run -m pytest

# Run with environment
uv run --env KEY=value python script.py
```

### Virtual Environment

```bash
# Activate (standard venv activation)
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

# Deactivate
deactivate
```

## Project-Specific Commands

### Setup

```bash
# Initial setup
uv venv
.venv\Scripts\activate  # Windows
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

### Development

```bash
# Format code
uv run ruff format src/

# Lint code
uv run ruff check src/

# Fix issues
uv run ruff check --fix src/

# Type check
uv run mypy src/
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test
uv run pytest tests/unit/test_auth.py

# Run with markers
uv run pytest -m unit
uv run pytest -m integration
```

### Running Application

```bash
# Main application
uv run python src/main.py

# Test scripts
uv run python scripts/test_config.py
uv run python scripts/test_auth.py
uv run python scripts/test_graph_api.py
uv run python scripts/test_openai.py
```

## Why uv?

### Speed Comparison
- **10-100x faster** than pip for package installation
- **Parallel downloads** and optimized caching
- **Faster dependency resolution**

### Benefits
- ✅ **Fast**: Blazing fast package installation
- ✅ **Reliable**: Better dependency resolution
- ✅ **Simple**: Drop-in replacement for pip
- ✅ **Compatible**: Works with existing requirements.txt
- ✅ **Modern**: Built in Rust for performance

### When to Use uv
- ✅ Installing packages: `uv pip install`
- ✅ Creating environments: `uv venv`
- ✅ Running scripts: `uv run`
- ✅ Building projects: `uv build` (coming soon)

## Ruff Quick Reference

### Formatting

```bash
# Format entire project
uv run ruff format .

# Format specific directory
uv run ruff format src/

# Check formatting without changes
uv run ruff format --check src/
```

### Linting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Show rule violations
uv run ruff check --show-files .

# Specific file
uv run ruff check src/main.py
```

### Configuration
All ruff settings are in `pyproject.toml`:
- Line length: 100
- Target Python: 3.11
- Rules enabled: E, W, F, I, N, UP, B, C4, SIM, PTH
- Auto-fix enabled for all rules

## Tips and Tricks

### Speed Up Installation
```bash
# Use cache aggressively (default)
uv pip install --cache-dir ~/.cache/uv package-name

# Skip cache for fresh install
uv pip install --no-cache package-name
```

### Development Workflow
```bash
# One-liner for setup
uv venv && .venv\Scripts\activate && uv pip install -e ".[dev]"

# Quick quality check
uv run ruff format src/ && uv run ruff check --fix src/ && uv run mypy src/

# Quick test
uv run pytest --lf  # Run last failed tests
```

### Working with Multiple Projects
```bash
# Create project-specific venv
uv venv .venv-project1
uv venv .venv-project2

# Activate specific venv
.venv-project1\Scripts\activate
```

## Common Issues

### Issue: uv not found
**Solution**: Restart terminal after installation or add to PATH manually

### Issue: Permission denied
**Solution**: Run as administrator (Windows) or use `sudo` (Linux/macOS)

### Issue: Package conflict
**Solution**: Use `uv pip install --force-reinstall` to reinstall conflicting packages

## Resources

- **uv GitHub**: https://github.com/astral-sh/uv
- **uv Documentation**: https://github.com/astral-sh/uv#readme
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **Python Packaging**: https://packaging.python.org/
