"""Lambda handler for FastAPI via Mangum adapter"""

from mangum import Mangum
from human_design.web.app import app

# Mangum adapter converts Lambda events to ASGI
handler = Mangum(app, lifespan="off")
