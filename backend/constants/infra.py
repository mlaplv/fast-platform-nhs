import os

# R105: Background Task Retention Policy
# Elite V2.2: Standard 3-day limit to protect SSD space in 2GB RAM environments
INFRA_RETENTION_DAYS: int = int(os.getenv("INFRA_RETENTION_DAYS", "3"))

# R106: Neural Trigger Tokens
# Special message to trigger Helen follow-up logic
HELEN_FOLLOW_UP_TRIGGER: str = "[SYSTEM_FOLLOW_UP_TRIGGER]"

# Arq Worker Performance Constants
ARQ_CONN_TIMEOUT: int = 10
ARQ_MAX_JOBS_DEFAULT: int = 5
ARQ_MAX_JOBS_HIGH: int = 10
