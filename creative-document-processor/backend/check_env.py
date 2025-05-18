from dotenv import load_dotenv
import os

# First load from .env file
print("Loading environment variables from .env file...")
load_dotenv()

# Check if GOOGLE_API_KEY exists
api_key = os.getenv("GOOGLE_API_KEY", "")
if api_key:
    print(f"✅ GOOGLE_API_KEY found: {api_key[:4]}...{api_key[-4:]} (length: {len(api_key)})")
else:
    print("❌ GOOGLE_API_KEY not found in environment variables")

# Check if other important environment variables exist
other_vars = ["BACKEND_HOST", "BACKEND_PORT", "STORAGE_PATH"]
for var in other_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var} found: {value}")
    else:
        print(f"❌ {var} not found")

# Try to import the app settings directly
print("\nImporting settings from app.core.config...")
try:
    from app.core.config import settings
    print(f"GOOGLE_API_KEY in settings: {'Found' if settings.GOOGLE_API_KEY else 'Not found'}")
    if settings.GOOGLE_API_KEY:
        print(f"API Key in settings: {settings.GOOGLE_API_KEY[:4]}...{settings.GOOGLE_API_KEY[-4:]} (length: {len(settings.GOOGLE_API_KEY)})")
except Exception as e:
    print(f"Error importing settings: {str(e)}") 