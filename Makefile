.PHONY: help install run docker-build docker-up docker-down docker-logs test clean

help:
	@echo "SPARK Coach - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install Python dependencies"
	@echo "  make setup-env     Copy .env.example to .env"
	@echo ""
	@echo "Development:"
	@echo "  make run           Run development server"
	@echo "  make test          Test API endpoints"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker images"
	@echo "  make docker-up     Start Docker services"
	@echo "  make docker-down   Stop Docker services"
	@echo "  make docker-logs   View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean         Clean cache and temp files"

install:
	@echo "Installing dependencies..."
	cd api && pip install -r requirements.txt

setup-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it with your API keys."; \
	else \
		echo ".env file already exists."; \
	fi

run:
	@echo "Starting SPARK Coach API..."
	cd api && python main.py

docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "API running at http://localhost:8080"
	@echo "Docs available at http://localhost:8080/docs"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down

docker-logs:
	docker-compose logs -f spark-coach-api

test:
	@echo "Testing SPARK Coach API..."
	@./test_api.sh

test-day2:
	@echo "Testing Day 2: Learning Schema & Briefing Agent..."
	@./test_day2.sh

clean:
	@echo "Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "Clean complete."
