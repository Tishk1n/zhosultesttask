FROM python:3.11-slim

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtualenv
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --without dev --no-interaction

# Copy application code
COPY app/ ./app/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the application
ENTRYPOINT ["poetry", "run", "python", "-m", "app.cli"]
