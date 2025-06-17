# Callback Microservice

Сервис для обработки AMQP сообщений и отправки callback-запросов с HMAC подписью для партнерской интеграции.

## Возможности

- Прием сообщений из AMQP очереди
- Автоматическая подпись запросов через HMAC
- Повторные попытки при ошибках отправки
- Prometheus метрики
- JSON логирование
- CLI интерфейс

## Установка

```bash
pip install -r requirements.txt
```

## Использование

### Запуск сервиса

Сервис можно запустить в двух режимах:

```bash
# Запуск только метрик
python -m app --metrics

# Запуск только AMQP консьюмера
python -m app --consumer

# Запуск обоих компонентов
python -m app --metrics --consumer
```

### AMQP API

Для отправки callback-запроса, необходимо отправить сообщение в AMQP со следующими параметрами:

- content_type: application/json
- type: SendCallback

Формат сообщения:
```json
{
    "target_url": "https://example.com/webhook",
    "target_method": "POST",  // Опционально, по умолчанию POST
    "hmac_secret": "your-secret-key",
    "payload": {
        // Любые данные для отправки
    }
}
```

### Параметры AMQP

- Exchange: "" (стандартный exchange)
- Queue: "callbacks"
- Routing key: "callbacks"

### HMAC подпись

- Используется алгоритм SHA256
- Payload сериализуется в JSON с сортировкой ключей
- Подпись добавляется в заголовок X-Signature

### Метрики

Сервис предоставляет Prometheus метрики по адресу `/metrics`:

- `callback_total` - количество обработанных callback-запросов (с метками status=[success|error])
- `callback_duration_seconds` - время обработки запросов (с меткой target_url)
- `hmac_errors_total` - количество ошибок при создании HMAC подписей
- `amqp_reconnects_total` - количество попыток переподключения к AMQP

### Логирование

Логи записываются в JSON формате для удобной интеграции с Promtail и Loki. Каждая запись содержит:

- timestamp
- level
- message
- дополнительные контекстные данные

## Конфигурация

Все параметры можно настроить в файле `app/config.py`:

- AMQP подключение
- Параметры очередей
- HTTP таймауты и ретраи
- Настройки метрик
- Уровень логирования

## Разработка

### Структура проекта

```
app/
  __init__.py      # Инициализация пакета
  cli.py          # CLI интерфейс
  consumer.py     # AMQP консьюмер
  callback.py     # HTTP клиент для колбэков
  crypto.py       # HMAC подписи
  metrics.py      # Prometheus метрики
  config.py       # Конфигурация
  logger.py       # JSON логирование
```

### Зависимости

- pika - AMQP клиент
- requests - HTTP клиент
- prometheus-client - метрики
- python-json-logger - JSON логирование
- backoff - повторные попытки с экспоненциальной задержкой
- aiohttp - асинхронный HTTP клиент