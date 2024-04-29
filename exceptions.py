class EnvVarException(Exception):
    """Исключение отсутствия переменных окружения."""

    pass


class MessageError(Exception):
    """Исключение при ошибке отправки сообщения."""

    pass


class TransactionError(Exception):
    """Исключение при неуспешной транзакции."""

    pass
