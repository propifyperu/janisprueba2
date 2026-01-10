from django.apps import AppConfig


class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'properties'
    
    def ready(self):
        # Importar el módulo de matching al arrancar la app para asegurar
        # que sus utilidades/handlers estén disponibles en tiempo de ejecución.
        try:
            from . import matching  # noqa: F401
            # registrar señales relacionadas con Requirement
            from . import signals  # noqa: F401
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Error cargando properties.matching')
