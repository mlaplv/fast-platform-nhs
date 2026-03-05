from litestar import Controller, get

class HealthController(Controller):
    path = "/health"

    @get("/")
    async def health_check(self) -> dict:
        return {"system": "Fast-Platform Gateway", "status": "online"}
