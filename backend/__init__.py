# V61.0 Backend Package
import warnings
# R61: Suppress Pydantic V1/Alchemy legacy warnings on Python 3.14+ (triggered during initial import)
warnings.filterwarnings("ignore", message=".*Core Pydantic V1 functionality isn't compatible with Python 3.14.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*set_async_context.*")
