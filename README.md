# Callback Microservice

Сервис для обработки AMQP сообщений и отправки callback-запросов с HMAC подписью для партнерской интеграции.

## Возможности

- Прием сообщений из AMQP очереди
- Автоматическая подпись запросов через HMAC
- Повторные попытки при ошибках отправки
- Prometheus метрики с визуализацией в Grafana
- JSON логирование
- CLI интерфейс
- Контейнеризация с Docker и Docker Compose

## Установка

### С использованием Poetry

```bash
# Установка зависимостей
poetry install

# Проверка типов
poetry run pyright

# Запуск линтера
poetry run ruff check .
```

### С использованием Docker

```bash
# Сборка и запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f

# Остановка сервисов
docker compose down

# Остановка сервисов с удалением волюмов
docker compose down -v
```

После запуска будут доступны:
- RabbitMQ Management UI: http://localhost:15672 (guest/guest)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Метрики приложения: http://localhost:8000/metrics

## Использование

### Запуск сервиса

Сервис можно запустить в одном из двух режимов:

```bash
# Через Poetry:

# Запуск сервера метрик
poetry run python -m app.cli --metrics

# Запуск AMQP консьюмера
poetry run python -m app.cli --consumer

# Через Docker:
docker compose up metrics    # для метрик
docker compose up consumer  # для консьюмера
```

Опции `--metrics` и `--consumer` являются взаимоисключающими - необходимо выбрать один из режимов работы.

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

### Требования

- Python 3.9+
- Poetry

### Установка для разработки

```bash
# Установка Poetry (если еще не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей
poetry install

# Активация виртуального окружения
source $(poetry env info --path)/bin/activate
```

### Запуск сервиса

```bash
# Через Poetry
poetry run python -m app --consumer

# Или после активации окружения
python -m app --consumer
```

### Инструменты разработчика

- **Ruff**: Линтер и форматтер кода
  ```bash
  poetry run ruff check .    # проверка
  poetry run ruff format .   # форматирование
  ```

- **Pyright**: Статический анализатор типов
  ```bash
  poetry run pyright
  ```

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