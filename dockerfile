# Use a lightweight and secure base Python image (Section 7 - Bonus)
FROM python:3.12-slim

# Set work directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src
COPY tests/ ./tests

# Default command: launch the interactive CC-IDE REPL in the terminal
CMD ["python", "-m", "cc_analyzer.presentation.repl"]