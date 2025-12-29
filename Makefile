.PHONY: help validate quality test install format format-check deploy deploy-test deploy-prod

help:
	@echo "Power Benchmarking Suite - Development Commands"
	@echo ""
	@echo "  make install      - Install package in development mode"
	@echo "  make validate     - Run all code quality validations"
	@echo "  make quality      - Run code quality check (alias for validate)"
	@echo "  make test         - Run tests"
	@echo "  make format       - Auto-format code with Black"
	@echo "  make format-check - Check code formatting (no changes)"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  make deploy       - Deploy to GitHub (interactive)"
	@echo "  make deploy-test  - Deploy to GitHub + TestPyPI"
	@echo "  make deploy-prod  - Deploy to GitHub + PyPI (PRODUCTION)"

install:
	pip install -e .

validate:
	@echo "Running code quality validations..."
	@chmod +x scripts/validate-*.sh
	@./scripts/validate-all.sh

quality: validate

test:
	pytest tests/ -v

format:
	@echo "Auto-formatting code with Black..."
	black --line-length 100 power_benchmarking_suite/ scripts/ tests/
	@echo "✅ Code formatted"

format-check:
	@echo "Checking code formatting..."
	black --check --line-length 100 power_benchmarking_suite/ scripts/ tests/
	@echo "✅ Code is properly formatted"

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

deploy:
	@echo "🚀 Starting deployment..."
	@./scripts/deploy.sh

deploy-test:
	@echo "🧪 Deploying to GitHub + TestPyPI..."
	@DEPLOY_GITHUB=true DEPLOY_TESTPYPI=true ./scripts/deploy.sh

deploy-prod:
	@echo "⚠️  PRODUCTION DEPLOYMENT"
	@echo "This will deploy to PyPI (production)."
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@DEPLOY_GITHUB=true DEPLOY_PYPI=true ./scripts/deploy.sh
