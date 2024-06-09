from django.apps import AppConfig


class ChatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chats"
    verbose_name = "Чаты"

    def ready(self):
        # Загрузка моделей из подпапки models
        import os

        from django.apps import apps
        from django.utils.module_loading import module_has_submodule

        from chats import signals

        app_module = apps.get_app_config("chats").module
        models_module = getattr(app_module, "models", None)

        if models_module:
            for file_name in os.listdir(models_module.__path__[0]):
                if file_name.endswith(".py") and not file_name.startswith("__"):
                    module_name = f"{models_module.__name__}.{file_name[:-3]}"
                    if module_has_submodule(models_module, file_name[:-3]):
                        __import__(module_name)