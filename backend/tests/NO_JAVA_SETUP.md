# Running Tests Without Firebase Emulator

If you don't want to install Java for the Firebase Emulator, you can run tests using a real Firebase test project instead.

## Option 1: Install Java (Recommended)

**Windows:**
```bash
# Using Chocolatey
choco install openjdk11

# Or download from:
# https://www.java.com/download/
```

After installation, restart terminal and verify:
```bash
java -version
```

Then run emulator:
```bash
firebase emulators:start --only auth,firestore
```

---

## Option 2: Use Real Firebase Test Project (No Java Required)

### Setup

1. **Create a separate Firebase test project:**
   - Go to https://console.firebase.google.com
   - Create new project: "health-ai-test"
   - Enable Authentication and Firestore

2. **Download service account key:**
   - Project Settings → Service Accounts
   - Generate new private key
   - Save as `test-service-account.json`

3. **Set environment variable:**
```bash
# Windows PowerShell
$env:FIREBASE_TEST_CREDENTIALS="C:\path\to\test-service-account.json"

# Windows CMD
set FIREBASE_TEST_CREDENTIALS=C:\path\to\test-service-account.json

# Bash
export FIREBASE_TEST_CREDENTIALS=/path/to/test-service-account.json
```

4. **Use alternative conftest:**
```bash
cd backend/tests
cp conftest_no_emulator.py conftest.py
```

### Running Tests

```bash
cd backend
pytest tests/test_integration.py -v
```

**Note:** This uses a REAL Firebase project, so:
- Tests will be slower (~60-90 seconds)
- May incur minimal Firebase costs
- Test data is automatically cleaned up after each test

---

## Option 3: Skip Integration Tests (Run Unit Tests Only)

If you just want to verify the code works:

```bash
cd backend
pytest tests/test_endpoints.py tests/test_admin.py tests/test_config.py -v
```

These tests use mocks and don't require Firebase at all.

---

## Comparison

| Method | Pros | Cons |
|--------|------|------|
| **Emulator** | Fast, free, isolated | Requires Java |
| **Real Project** | No Java needed | Slower, minimal cost |
| **Unit Tests Only** | Fastest, no setup | Doesn't test real flows |

**Recommendation:** Install Java and use Emulator for best experience.
