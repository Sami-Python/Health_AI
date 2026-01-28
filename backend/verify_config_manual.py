import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.config import get_settings, DevelopmentSettings, ProductionSettings
except ImportError:
    try:
        from config import get_settings, DevelopmentSettings, ProductionSettings
    except ImportError as e:
        print(f"Import Error: {e}")
        sys.exit(1)

def run_checks():
    print("Testing Development Config...")
    os.environ["APP_ENV"] = "development"
    get_settings.cache_clear()
    settings = get_settings()
    if not isinstance(settings, DevelopmentSettings):
        print("FAIL: Expected DevelopmentSettings")
        return False
    if settings.DEBUG is not True:
        print("FAIL: DEBUG should be True")
        return False
    print("PASS: Development Config OK")

    print("\nTesting Production Config...")
    os.environ["APP_ENV"] = "production"
    os.environ["FRONTEND_URL"] = "https://healthai.app"
    get_settings.cache_clear()
    settings = get_settings()
    if not isinstance(settings, ProductionSettings):
        print(f"FAIL: Expected ProductionSettings, got {type(settings)}")
        return False
    if settings.DEBUG is not False:
        print("FAIL: DEBUG should be False")
        return False
    if "https://healthai.app" not in settings.CORS_ORIGINS:
        print(f"FAIL: CORS_ORIGINS should contain frontend url. Got: {settings.CORS_ORIGINS}")
        return False
    print("PASS: Production Config OK")
    return True

if __name__ == "__main__":
    success = run_checks()
    if success:
        print("\nAll checks passed!")
        sys.exit(0)
    else:
        print("\nSome checks failed.")
        sys.exit(1)
