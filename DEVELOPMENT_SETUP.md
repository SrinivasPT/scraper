# Development Setup Guide

This document outlines the comprehensive development setup for the RegScraper project with optimal VS Code and Python tooling configuration.

## ✨ What's Been Configured

### 🔧 VS Code Settings
- **Ruff Integration**: Complete linting and formatting with Ruff
- **Python Analysis**: Strict type checking with Pylance
- **Auto-formatting**: Format on save and paste
- **Code Actions**: Auto-organize imports and fix issues
- **Testing**: Integrated pytest runner with coverage
- **Debugging**: Ready-to-use debug configurations

### 🐍 Python & Ruff Configuration
- **Line Length**: 140 characters (optimal for modern screens)
- **Target Python**: 3.11+
- **Comprehensive Rules**: 70+ rule categories for code quality
- **Import Sorting**: Automatic import organization
- **Type Safety**: Enhanced type annotations and checking
- **Security**: Bandit security checks integrated

## 🚀 Quick Start

### 1. Install Development Dependencies
```powershell
# Using the development script
.\dev-commands.ps1 setup

# Or manually
py -m pip install -e ".[dev]"
```

### 2. VS Code Extensions
The workspace automatically recommends these extensions:
- Python
- Pylance
- Ruff
- Code Spell Checker
- Even Better TOML

### 3. Development Workflow
```powershell
# Fix all code issues
.\dev-commands.ps1 fix

# Run tests
.\dev-commands.ps1 test

# Check code quality
.\dev-commands.ps1 check

# Clean cache
.\dev-commands.ps1 clean
```

## 📋 Available Commands

### PowerShell Script (`dev-commands.ps1`)
```powershell
.\dev-commands.ps1 <command>
```

| Command | Description |
|---------|-------------|
| `setup` | Complete development environment setup |
| `install-dev` | Install development dependencies |
| `lint` | Run linter checks |
| `fix` | Automatically fix lint issues |
| `format` | Format code with Ruff |
| `check` | Run lint and format together |
| `test` | Run test suite |
| `test-cov` | Run tests with coverage report |
| `clean` | Clean cache directories |
| `help` | Show available commands |

### VS Code Tasks (Ctrl+Shift+P → "Tasks: Run Task")
- **Python: Install Dev Dependencies**
- **Ruff: Lint Code**
- **Ruff: Fix Issues**
- **Ruff: Format Code**
- **Ruff: Check All** (Default Build)
- **Python: Run Tests** (Default Test)
- **Python: Run Tests with Coverage**
- **Clean: Cache Directories**

### VS Code Keyboard Shortcuts
- **Ctrl+Shift+B**: Run default build task (Ruff check all)
- **Ctrl+Shift+P**: Command palette
- **F5**: Start debugging
- **Ctrl+Shift+`**: Open terminal

## 🛠️ Configuration Files

### Core Configuration
- **`.vscode/settings.json`**: VS Code workspace settings
- **`.vscode/extensions.json`**: Recommended extensions
- **`.vscode/launch.json`**: Debug configurations
- **`.vscode/tasks.json`**: Build and test tasks
- **`pyproject.toml`**: Python project configuration with Ruff rules
- **`ruff.toml`**: Alternative Ruff configuration (takes precedence)

### Development Scripts
- **`dev-commands.ps1`**: PowerShell development script
- **`Makefile.bat`**: Batch file alternative for Windows

## 🔍 Code Quality Standards

### Enabled Rule Categories (70+)
- **Style**: pycodestyle (E/W), pep8-naming (N)
- **Logic**: Pyflakes (F), flake8-bugbear (B)
- **Imports**: isort (I), flake8-tidy-imports (TID)
- **Types**: flake8-annotations (ANN), pyupgrade (UP)
- **Security**: flake8-bandit (S)
- **Performance**: Perflint (PERF)
- **Complexity**: Pylint (PL), McCabe complexity
- **Modern Python**: pyupgrade (UP), flake8-future-annotations (FA)

### Type Checking
- **Strict Mode**: Enabled in Pylance
- **Return Types**: Required for all functions
- **Inlay Hints**: Function returns and variable types shown
- **Auto-imports**: Automatic import suggestions

### Testing
- **Framework**: pytest with async support
- **Coverage**: HTML and terminal reports
- **Auto-discovery**: Tests found automatically
- **VS Code Integration**: Run/debug tests from editor

## 📊 Metrics & Reports

### Coverage Reports
```powershell
.\dev-commands.ps1 test-cov
```
- **HTML Report**: `htmlcov/index.html`
- **Terminal**: Immediate coverage summary

### Code Quality Metrics
- **Complexity**: Max 12 (McCabe)
- **Function Args**: Max 8 parameters
- **Line Length**: 140 characters
- **Import Organization**: Automatic sorting

## 🐛 Debugging

### Available Configurations
1. **Python: Current File** - Debug the currently open file
2. **Python: Module** - Debug the regscraper module
3. **Python: Pytest** - Debug all tests
4. **Python: Pytest Current File** - Debug current test file

### Debug Features
- **Breakpoints**: Click in gutter or F9
- **Step Through**: F10 (step over), F11 (step into)
- **Variable Inspection**: Hover over variables
- **Call Stack**: See execution path
- **Exception Handling**: Break on exceptions

## 🔧 Customization

### Adding More Rules
Edit `ruff.toml` or `pyproject.toml`:
```toml
[tool.ruff.lint]
select = [..., "NEW_RULE"]
```

### VS Code Settings
Modify `.vscode/settings.json` for workspace-specific preferences:
```json
{
    "python.analysis.typeCheckingMode": "strict",
    "editor.rulers": [140]
}
```

### Git Integration
Consider adding `.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
.mypy_cache/
```

## 📚 Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pylance Settings](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- [pytest Documentation](https://docs.pytest.org/)
- [VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial)

## 🎯 Benefits

✅ **Consistent Code Style** - Automatic formatting and linting
✅ **High Code Quality** - 70+ rules catching bugs and issues
✅ **Type Safety** - Strict type checking prevents runtime errors
✅ **Fast Feedback** - Real-time error detection in editor
✅ **Easy Testing** - One-click test running and debugging
✅ **Professional Setup** - Industry-standard tools and practices
✅ **Developer Experience** - Optimized for productivity and maintainability

This setup provides a professional, efficient development environment that supports the RegScraper project's production-ready architecture with comprehensive testing, ethical scraping practices, and extensible design patterns!
