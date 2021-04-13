import os
from starlette.datastructures import CommaSeparatedStrings, Secret


# API_V1_STR = "/api"

# JWT_TOKEN_PREFIX = "Token"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # one week

# load_dotenv(".env")

MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 10))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 10))
# SECRET_KEY = Secret(os.getenv("SECRET_KEY", "secret key for project"))

# PROJECT_NAME = os.getenv("PROJECT_NAME", "FastAPI example application")
# ALLOWED_HOSTS = CommaSeparatedStrings(os.getenv("ALLOWED_HOSTS", ""))

MONGODB_URL = os.getenv("MONGODB_URL", "")  # deploying without docker-compose
if not MONGODB_URL:
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
    MONGO_USER = os.getenv("MONGO_USER", "signal_sep")
    MONGO_PASS = os.getenv("MONGO_PASSWORD", "signal_sep")
    MONGO_DB = os.getenv("MONGO_DB", "signal")
    MONGODB_URL = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"

    MONGO_USER_TEST = os.getenv("MONGO_USER", "signal_sep_test")
    MONGO_PASS_TEST = os.getenv("MONGO_PASSWORD", "signal_sep_test")
    MONGO_DB_TEST = os.getenv("MONGO_DB", "signal_sep_test")
    MONGODB_TEST_URL = f"mongodb://{MONGO_USER_TEST}:{MONGO_PASS_TEST}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_TEST}"
else:
    MONGODB_URL = MONGODB_URL

database_name = MONGO_DB

signal_collection_name = "signal"
stem_collection_name = "stem"

augment_collection_name = "augment"
