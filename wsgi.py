from app.config import load_config, setup_logging
from app.monitor import MonitoringService
from app.web.app import create_app

logger = setup_logging()
config = load_config()
monitoring_service = MonitoringService(config)
app = create_app(config, monitoring_service)