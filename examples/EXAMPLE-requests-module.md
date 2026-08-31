# Module Src Requests

# HTTP Client Core (`src/requests/`)

## Module Responsibility

The `src/requests/` module implements the core HTTP client functionality, handling:
- Request/response lifecycle (`src/requests/models.py:284-375`, `src/requests/models.py:378-729`, `src/requests/models.py:732-1184`)
- Session management (`src/requests/sessions.py:395-905`)
- Transport adapters (`src/requests/adapters.py:158-748`)
- Authentication (`src/requests/auth.py:85-113`)
- Cookie handling (`src/requests/cookies.py`)

## Key Files and Components

### Request/Response Cycle (`src/requests/models.py`)

Core objects:
- `src/requests/models.py:284-375`: User-facing request builder
- `src/requests/models.py:378-729`: Immutable, fully-formed request ready for transmission
- `src/requests/models.py:732-1184`: Server response container

Key mixins:
- `src/requests/models.py:254-281`: Event hook registration
- `src/requests/models.py:108-251`: URL/parameter encoding

### Session Management (`src/requests/sessions.py`)

- `src/requests/sessions.py:395-905`: Persistent connection pool and settings
  - Manages cookies, auth, proxies
  - Uses `src/requests/sessions.py:76-105` to combine request/session settings
  - Implements redirect handling via `src/requests/sessions.py:127-392`

### Transport Layer (`src/requests/adapters.py`)

- `src/requests/adapters.py:158-748`: Default HTTP/HTTPS transport
  - Manages connection pools via urllib3
  - Handles proxy configuration
  - Implements retry logic

### Utilities (`src/requests/utils.py`)

Key functions:
- `src/requests/utils.py:160-228`: Determines content length
- `src/requests/utils.py:231-280`: Extracts auth from .netrc
- `src/requests/utils.py:329-338`: Safe file writing

## Data Flow

1. User creates `src/requests/models.py:284-375`
2. `src/requests/sessions.py:395-905` prepares request via `src/requests/sessions.py:511-555`
3. `src/requests/adapters.py:158-748` sends `src/requests/models.py:378-729`
4. Server returns `src/requests/models.py:732-1184`

## Key Interactions

- Sessions maintain cookie state via `src/requests/cookies.py` utilities
- Auth handlers (`src/requests/auth.py:85-113`) modify requests before sending
- Adapters use `src/requests/utils.py:160-228` for content-length headers
- Redirects are handled by `src/requests/sessions.py:127-392`

## Cross-Module Dependencies

- Uses urllib3 for low-level HTTP operations
- Integrates with standard library's http.cookiejar
- Depends on cryptography for SSL verification

---
## See also
- [[architecture]]
- [[data-flow]]
- [[glossary]]
- [[module-docs]]
- [[module-docs-_themes]]
- [[module-tests]]
- [[module-tests-testserver]]
- [[onboarding]]
