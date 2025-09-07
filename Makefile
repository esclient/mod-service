-include .env

PROTO_TAG ?= v0.1.0
PROTO_NAME := mod.proto

TMP_DIR := .proto
OUT_DIR := src/modservice/grpc

.PHONY: clean fetch-proto get-stubs update format lint test install check-deps docker-build run

ifeq ($(OS),Windows_NT)
MKDIR	 = powershell -Command "New-Item -ItemType Directory -Force -Path"
RM		 = powershell -NoProfile -Command "if (Test-Path '$(TMP_DIR)') { Remove-Item -Recurse -Force '$(TMP_DIR)' }"
DOWN	 = powershell -Command "Invoke-WebRequest -Uri"
DOWN_OUT = -OutFile
FIX_IMPORTS = powershell -Command "Get-ChildItem -Path '$(OUT_DIR)' -Filter '*_pb2_grpc.py' | ForEach-Object { (Get-Content $$_.FullName) -replace '^import (.*_pb2)', 'from . import $$1' | Set-Content -Path $$_.FullName -Encoding UTF8 }"
CHECK_PYTHON = powershell -Command "try { python --version | Out-Null } catch { Write-Host 'Python not found'; exit 1 }"
CHECK_PDM = powershell -Command "try { pdm --version | Out-Null } catch { Write-Host 'PDM not found. Install with: pip install pdm'; exit 1 }"
else
MKDIR	 = mkdir -p
RM		 = rm -rf $(TMP_DIR)
DOWN	 = wget
DOWN_OUT = -O
FIX_IMPORTS = \
	for f in $(OUT_DIR)/*_pb2_grpc.py; do \
		sed -i 's/^import \(.*_pb2\)/from . import \1/' $$f; \
	done
CHECK_PYTHON = command -v python3 >/dev/null 2>&1 || { echo "Error: Python not found"; exit 1; }
CHECK_PDM = command -v pdm >/dev/null 2>&1 || { echo "Error: PDM not found. Install with: pip install pdm"; exit 1; }
endif

check-system:
	@$(CHECK_PYTHON)
	@$(CHECK_PDM)


bootstrap:
	@pdm venv create --force || true

install: bootstrap check-system
	@pdm install

check-deps:
	@pdm list

clean:
	@$(RM)

clean-venv:
	@pdm venv remove -y .venv || true

fetch-proto:
	@$(MKDIR) "$(TMP_DIR)"
	@$(DOWN) "https://raw.githubusercontent.com/esclient/protos/$(PROTO_TAG)/$(PROTO_NAME)" $(DOWN_OUT) "$(TMP_DIR)/$(PROTO_NAME)"

get-stubs: fetch-proto
	@$(MKDIR) "$(OUT_DIR)"
	@pdm run python -m grpc_tools.protoc \
		--proto_path="$(TMP_DIR)" \
		--python_out="$(OUT_DIR)" \
		--grpc_python_out="$(OUT_DIR)" \
		--pyi_out="$(OUT_DIR)" \
		"$(TMP_DIR)/$(PROTO_NAME)"
	@$(FIX_IMPORTS)

update: get-stubs clean

format:
	@pdm run black .
	@pdm run isort .
	@pdm run ruff check . --fix

lint:
	@pdm run black --check .
	@pdm run isort . --check --diff
	@pdm run flake8 .
	@pdm run ruff check .
	@pdm run mypy --strict .

test:
	@pdm run pytest

dev-check: install format lint test

docker-build:
	@docker build --build-arg PORT=$(PORT) -t mod .

run: docker-build
	@docker run --rm -it \
		--env-file .env \
		-p $(PORT):$(PORT) \
		-v $(CURDIR):/app \
		-e WATCHFILES_FORCE_POLLING=true \
		mod