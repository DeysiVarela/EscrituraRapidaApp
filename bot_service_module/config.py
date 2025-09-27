import os

class DefaultConfig:
    """
    Configuracion general del bot
    """

    APP_ID = os.environ.get("MICROSFT_APP_ID", "")
    APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
    APP_TYPE = os.environ.get("APP_TYPE", "")
    APP_TENANTID = os.environ.get("APP_TENANTID", "")
