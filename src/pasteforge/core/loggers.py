import logging
import logging.config

from celery.signals import setup_logging as celery_setup_logging

from src.pasteforge.core.config import configs


def build_logging_config(component: str) -> dict:
    if component not in {"api", "worker"}:
        raise ValueError(f"Unsupported component: {component}")

    configs.LOG_DIR.mkdir(parents=True, exist_ok=True)

    component_logger = "pasteforge" if component == "api" else "pasteforge.infrastructure.worker"

    return {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "console": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "file": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": configs.LOG_LEVEL,
                "formatter": "console",
            },
            "component_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "file",
                "filename": str(configs.LOG_DIR / f"{component}.log"),
                "maxBytes": configs.LOG_MAX_BYTES,
                "backupCount": configs.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
            "sqlalchemy_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": configs.SQLALCHEMY_LOG_LEVEL,
                "formatter": "file",
                "filename": str(configs.LOG_DIR / "sqlalchemy.log"),
                "maxBytes": configs.LOG_MAX_BYTES,
                "backupCount": configs.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },

        "loggers": {
            component_logger: {
                "level": configs.LOG_LEVEL,
                "handlers": ["console", "component_file"],
                "propagate": False,
            },
            'pasteforge.tasks': {
                "level": configs.LOG_LEVEL,
                "handlers": ["console", "component_file"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "component_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": configs.SQLALCHEMY_LOG_LEVEL,
                "handlers": ["sqlalchemy_file"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["sqlalchemy_file"],
                "propagate": False,
            },
        },

        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
    }


def setup_api_logging() -> None:
    config = build_logging_config("api")
    config["loggers"]["uvicorn"] = {
        "level": "INFO",
        "handlers": ["console", "component_file"],
        "propagate": False,
    }
    logging.config.dictConfig(config)


@celery_setup_logging.connect
def setup_celery_logging(**kwargs) -> None:
    config = build_logging_config("worker")
    logging.config.dictConfig(config)
