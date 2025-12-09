# Contributing to Medical MCPs

Thank you for your interest in contributing to Medical MCPs! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/pascalwhoop/medical-mcps.git
   cd medical-mcps
   ```

2. **Install dependencies**
   ```bash
   make install
   # or: uv sync
   ```

3. **Install pre-commit hooks** (optional but recommended)
   ```bash
   uv run pre-commit install
   ```

4. **Start the development server**
   ```bash
   make server
   ```
   The server will be available at `http://localhost:8000` with auto-reload on code changes.

## Code Style & Quality

We use **Ruff** for both linting and formatting. All pull requests must pass these checks.

### Formatting Code
```bash
make format
```

This will:
- Format code with `ruff format`
- Apply automatic fixes with `ruff check --fix`

### Linting Code
```bash
make lint
```

This checks for:
- PEP 8 style violations (E, W)
- Logical errors (F)
- Import sorting issues (I)
- Naming conventions (N)
- Python version compatibility (UP)
- Async/await issues (ASYNC)
- Ruff-specific rules (RUF)

### Configuration
Ruff configuration is in `pyproject.toml` under `[tool.ruff]`. Key settings:
- **Line length**: 100 characters
- **Target Python**: 3.12+
- **Auto-fix**: Enabled for safe fixes

## Testing

We use **pytest** for testing. All contributions should include tests.

### Running Tests

```bash
# Run fast tests (excludes slow Pathway Commons tests)
make test

# Run slow tests
make test-slow

# Run all tests
make test-all

# Run tests with coverage report
make test-cov

# Run tests on file changes (auto-watch)
make test-watch
```

### Writing Tests

Tests are located in `tests/` directory:
- **Unit/Integration tests**: Standard pytest files (e.g., `test_*.py`)
- **API contract tests**: Tavern YAML files (e.g., `*.tavern.yaml`)

Test markers:
- `@pytest.mark.slow` - For slow tests (Pathway Commons)
- `@pytest.mark.tavern` - For Tavern YAML tests

### Coverage
We track code coverage with pytest-cov. Generate a coverage report:
```bash
make test-cov
```

This generates:
- Terminal report with missing lines
- HTML coverage report in `htmlcov/`

Coverage is currently informational—no hard failures, but improvements are welcome!

## Adding a New API Integration

To add a new biological/medical API:

### 1. Create API Client
File: `medical_mcps/api_clients/{api_name}_client.py`

```python
from .base_client import BaseClient

class MyAPIClient(BaseClient):
    def __init__(self, enable_cache: bool = True):
        super().__init__(cache_file=f"{api_name}.db", enable_cache=enable_cache)
        self.base_url = "https://api.example.com"

    async def get_resource(self, resource_id: str) -> dict:
        """Get a resource by ID."""
        url = f"{self.base_url}/resource/{resource_id}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()
```

### 2. Create API Server
File: `medical_mcps/servers/{api_name}_server.py`

```python
from mcp.server.fastmcp import FastMCP
from ..med_mcp_server import unified_mcp, tool as medmcps_tool
from ..api_clients.myapi_client import MyAPIClient

myapi_mcp = FastMCP("myapi", stateless_http=True, json_response=True)

@medmcps_tool(name="myapi_get_resource", servers=[myapi_mcp, unified_mcp])
async def myapi_get_resource(resource_id: str) -> dict:
    """Get a resource by ID.

    Args:
        resource_id: Resource identifier
    """
    client = MyAPIClient()
    return await client.get_resource(resource_id)
```

### 3. Register Server
File: `medical_mcps/http_server.py`

Add import and register:
```python
from .servers import myapi_server

# In lifespan function:
await stack.enter_async_context(myapi_mcp.session_manager.run())

# In router mounts:
Mount("/tools/myapi/mcp", myapi_mcp.aio_transport.asgi_app)
```

### 4. Naming Conventions
- **Tools**: `{api_name}_{function_name}` (e.g., `myapi_get_resource`)
- **Files**: `{api_name}_client.py`, `{api_name}_server.py`
- **Server variable**: `{api_name}_mcp` (e.g., `myapi_mcp`)

### 5. Add Tests
Create test file: `tests/test_myapi_tools.py` or `.tavern.yaml`

## Pull Request Process

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**
   - Code changes
   - Tests for new features/fixes
   - Documentation updates if needed

3. **Check code quality**
   ```bash
   make format  # Auto-format code
   make lint    # Check for issues
   make test    # Run tests
   ```

4. **Push and create a PR**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin feature/my-feature
   ```

5. **PR Description**
   Include:
   - What type of change (feature, bug fix, docs, refactoring)
   - APIs affected (if applicable)
   - Testing performed
   - Breaking changes (if any)

## Commit Message Guidelines

We follow conventional commits for clarity:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Maintenance, dependencies

**Examples:**
- `feat(reactome): add pathway graph traversal`
- `fix(chembl): handle empty search results`
- `docs: update API documentation`
- `chore: update dependencies`

## API Key Handling

For APIs requiring authentication:

1. Add `api_key: str` as a parameter to all tools
2. Don't store keys in environment variables or config files
3. Return clear error if missing: `"Error: API key is required. Get from <url>"`
4. Pass key to client during instantiation: `client = APIClient(api_key=api_key)`

Example:
```python
@medmcps_tool(name="omim_get_entry", servers=[omim_mcp, unified_mcp])
async def omim_get_entry(mim_number: str, api_key: str) -> dict:
    """Get OMIM entry.

    Args:
        mim_number: MIM number
        api_key: OMIM API key (REQUIRED - get from https://omim.org/api)
    """
    if not api_key:
        return {"error": "API key is required. Get from https://omim.org/api"}
    client = OMIMClient(api_key=api_key)
    return await client.get_entry(mim_number)
```

## Documentation

- **README.md**: User-facing documentation, setup, configuration
- **docs/**: Detailed documentation (architecture, deployment, etc.)
- **Docstrings**: Python docstrings for all public functions/classes
- **.claude/CLAUDE.md**: Internal development notes

When adding a new API, update:
1. README.md - Add to "APIs Integrated" section and tool listings
2. Docstrings - Clear descriptions of parameters and returns

## Questions?

- Check existing [issues](https://github.com/pascalwhoop/medical-mcps/issues)
- Review [README.md](../README.md) and `.claude/CLAUDE.md` for architecture details
- Open a discussion or issue for larger changes

## Code of Conduct

This project is committed to providing a welcoming and inclusive environment for all participants. Please be respectful and constructive in all interactions.

---

Thank you for contributing to Medical MCPs! 🙌
