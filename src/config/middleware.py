from django.utils import translation


class AdminLocaleMiddleware:
    """
    Форсирует использование русского языка (RU) для всех путей в админ-панели.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        previous_language = translation.get_language()
        if request.path.startswith('/admin/'):
            translation.activate('ru')
            request.LANGUAGE_CODE = 'ru'

        response = self.get_response(request)

        if request.path.startswith('/admin/'):
            if hasattr(response, "render") and callable(response.render) and not getattr(response, "is_rendered", True):
                response.render()
            if previous_language:
                translation.activate(previous_language)
            else:
                translation.deactivate()

        return response
