import re

# Elite V2.2: Centralized Device Detection (Backend)
MOBILE_REGEX = re.compile(r"Mobi|Android|iPhone|iPod|BlackBerry|IEMobile|Opera Mini", re.I)

def is_mobile_device(user_agent: str) -> bool:
    if not user_agent:
        return False
        
    is_mobile_match = bool(MOBILE_REGEX.search(user_agent))
    is_ipad = bool(re.search(r"iPad", user_agent, re.I))
    is_android_tablet = bool(re.search(r"Android", user_agent, re.I)) and not bool(re.search(r"Mobi", user_agent, re.I))
    
    return is_mobile_match and not is_ipad and not is_android_tablet
