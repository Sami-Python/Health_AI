# Backend Integration Tests

## Overview

This directory contains both **unit tests** and **integration tests** for the Health AI backend.

### Test Types

**Unit Tests** (Existing)
- `test_endpoints.py` - Endpoint tests with mocked database
- `test_admin.py` - Admin endpoint tests with mocks
- `test_config.py` - Configuration tests
- Use `unittest.mock` for isolation
- Fast execution (~1-2 seconds)

**Integration Tests** (New)
- `test_integration.py` - Real Firebase Auth and Firestore tests
- Use Firebase Emulator for isolated testing
- Test actual flows with real tokens
- Slower execution (~30-60 seconds)

---

## Prerequisites

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `pytest>=7.4.0`
- `pytest-asyncio>=0.21.0`
- All other backend dependencies

### 2. Install Firebase CLI (for emulator)

```bash
npm install -g firebase-tools
```

### 3. Initialize Firebase Emulator (One-time setup)

```bash
cd ..  # Go to project root
firebase init emulators
```

Select:
- ✅ Authentication Emulator
- ✅ Firestore Emulator

Use default ports:
- Auth: 9099
- Firestore: 8080

---

## Running Tests

### Option 1: Unit Tests Only (Fast)

```bash
cd backend
pytest tests/test_endpoints.py tests/test_admin.py tests/test_config.py -v
```

**Expected output:** All tests pass in ~1-2 seconds

### Option 2: Integration Tests (Requires Emulator)

**Terminal 1: Start Firebase Emulator**
```bash
firebase emulators:start --only auth,firestore
```

Wait for:
```
✔  All emulators ready!
│ ✔  Auth Emulator running on http://localhost:9099
│ ✔  Firestore Emulator running on http://localhost:8080
```

**Terminal 2: Run Integration Tests**
```bash
cd backend
pytest tests/test_integration.py -v
```

**Expected output:** 20+ tests pass in ~30-60 seconds

### Option 3: All Tests

```bash
# Terminal 1: Start emulator
firebase emulators:start --only auth,firestore

# Terminal 2: Run all tests
cd backend
pytest tests/ -v
```

---

## Test Structure

### Integration Test Categories

**1. Authentication & Authorization (5 tests)**
- Valid token access
- Invalid token rejection
- User data isolation
- Admin-only endpoint protection

**2. GDPR Compliance (4 tests)**
- Data export completeness
- Firestore data deletion
- Firebase Auth user deletion
- Comprehensive deletion flow

**3. Garmin Integration (5 tests)**
- Credentials encryption
- Credentials decryption
- Status checking
- Credentials deletion
- User isolation

**4. Core Endpoints (6 tests)**
- Goals CRUD operations
- Profile updates
- Manual workout logging
- Feedback submission

**5. Error Handling (3 tests)**
- Invalid payloads
- Invalid dates
- Non-existent resources

---

## Test Fixtures

Defined in `conftest.py`:

- `test_user` - Creates test user with Firebase token
- `test_admin` - Creates admin user
- `second_test_user` - For isolation testing
- `authenticated_client` - Test client with auth headers
- `admin_client` - Test client with admin auth
- `wait_for_firestore` - Helper for eventual consistency

---

## Environment Variables

Tests use `.env.test`:

```bash
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
APP_ENV=test
ADMIN_EMAILS=admin@test.com,test_admin@example.com
ENCRYPTION_KEY=test_encryption_key_32bytes!!
```

---

## Troubleshooting

### "Connection refused" errors

**Problem:** Firebase Emulator not running

**Solution:**
```bash
firebase emulators:start --only auth,firestore
```

### "Module not found" errors

**Problem:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Tests hang or timeout

**Problem:** Firestore eventual consistency

**Solution:** Tests include `wait_for_firestore_write()` calls. If tests still hang, increase wait time in `test_helpers.py`.

### "User already exists" errors

**Problem:** Emulator data persisted

**Solution:** Restart emulator (it clears data on restart)

### Import errors

**Problem:** Python path issues

**Solution:** Run tests from `backend/` directory:
```bash
cd backend
pytest tests/test_integration.py -v
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Install Firebase CLI
        run: npm install -g firebase-tools
      
      - name: Start Firebase Emulator
        run: |
          firebase emulators:start --only auth,firestore &
          sleep 10  # Wait for emulator to start
      
      - name: Run Unit Tests
        run: |
          cd backend
          pytest tests/test_endpoints.py tests/test_admin.py -v
      
      - name: Run Integration Tests
        run: |
          cd backend
          pytest tests/test_integration.py -v
```

---

## Test Coverage

To generate coverage report:

```bash
cd backend
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

View HTML report:
```bash
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

**Target Coverage:** >70% for `main.py`

---

## Writing New Tests

### Unit Test Example

```python
# tests/test_endpoints.py
def test_new_endpoint(mock_db):
    mock_db.some_method.return_value = {"data": "test"}
    
    response = client.get("/new-endpoint")
    
    assert response.status_code == 200
    assert response.json() == {"data": "test"}
```

### Integration Test Example

```python
# tests/test_integration.py
@pytest.mark.integration
class TestNewFeature:
    def test_new_flow(self, authenticated_client, test_user):
        # Test real flow with real Firebase
        response = authenticated_client.post("/new-endpoint", json={...})
        
        assert response.status_code == 200
        
        wait_for_firestore_write()
        
        # Verify in Firestore
        db = firestore_manager.db
        doc = db.document(f"collection/{test_user['uid']}").get()
        assert doc.exists
```

---

## Best Practices

1. **Use appropriate test type:**
   - Unit tests for logic testing
   - Integration tests for flow testing

2. **Clean up test data:**
   - Fixtures handle cleanup automatically
   - Use `wait_for_firestore_write()` after mutations

3. **Isolate tests:**
   - Each test should be independent
   - Don't rely on test execution order

4. **Use descriptive names:**
   - `test_user_can_create_goal_successfully`
   - Not: `test_goal_1`

5. **Test edge cases:**
   - Invalid inputs
   - Missing data
   - Concurrent operations

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test output for specific errors
3. Check Firebase Emulator logs
4. Verify environment variables in `.env.test`
