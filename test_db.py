from backend.utils.security import GeminiSecurity
from backend.core.config import settings

print("Key len:", len(settings.encryption_key) if settings.encryption_key else 0)
print("Is encryption key set?", bool(settings.encryption_key))
