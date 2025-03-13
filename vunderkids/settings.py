import os

from dotenv import load_dotenv

load_dotenv(override=True)

STAGE = os.getenv("STAGE")

if STAGE == "PROD":
    from vunderkids.settings_config.production import *
else:
    from vunderkids.settings_config.development import *
