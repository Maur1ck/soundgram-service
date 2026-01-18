from fastapi import HTTPException


class SoundgramException(Exception):
    detail = "Неожиданная ошибка"


class SoundgramHTTPException(HTTPException):
    status_code = 500
    detail = None

    def __init__(self, detail: str = None):
        if detail:
            self.detail = detail
        super().__init__(status_code=self.status_code, detail=self.detail)


class InvalidURLFormatException(SoundgramHTTPException):
    status_code = 400
    detail = "Неверный формат ссылки"


class CaptchaRequiredException(SoundgramHTTPException):
    status_code = 403
    detail = "Яндекс требует капчу (попробуйте сменить IP)"


class PlaylistNotFoundException(SoundgramHTTPException):
    status_code = 404
    detail = "Плейлист не найден или доступ к нему закрыт"


class ServiceUnavailableException(SoundgramHTTPException):
    status_code = 503
    detail = "Ошибка соединения с источником"


class ExternalServiceException(SoundgramHTTPException):
    def __init__(self, status_code: int, detail: str = "Ошибка при запросе к источнику"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail=self.detail)
