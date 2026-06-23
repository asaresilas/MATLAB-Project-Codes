import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    logger.info("TensorFlow Imported")
except ImportError as e:
    logger.error(f"TensorFlow Import Failed: {e}")

try:
    import argparse
    logger.info("Argparse Imported")
except ImportError as e:
    logger.error(f"Argparse Import Failed: {e}")

try:
    from src.interface import ModelManager
    logger.info("Loader Imported")
except ImportError as e:
    logger.error(f"Loader Import Failed: {e}")

try:
    from app.services.model_registry import registry
    logger.info("Registry Imported")
except ImportError as e:
    logger.error(f"Registry Import Failed: {e}")

try:
    from src.interface import predict_multi_modal
    logger.info("Prediction Engine Imported")
except ImportError as e:
    logger.error(f"Prediction Engine Import Failed: {e}")