INTENT_TO_ACTION = {}

class SemanticRouter:
    def __init__(self):
        pass
    async def warmup(self):
        pass
    async def classify(self, text, extra_intents=None):
        return "UNKNOWN", 0.0
