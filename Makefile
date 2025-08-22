-include .env

PROTO_TAG ?= v0.0.16
PROTO_NAME := mod.proto

TMP_DIR := .proto
OUT_DIR := src/modservice/grpc

.PHONY: clean fetch-proto get-stubs update format lint test

ifeq ($(OS),Windows_NT)
MKDIR	 = powershell -Command "New-Item -ItemType Directory -Force -Path"
RM		 = powershell -NoProfile -Command "Remove-Item -Path '$(TMP_DIR)' -Recurse -Force"
DOWN	 = powershell -Command "Invoke-WebRequest -Uri"source .venv/Scripts/activate
DOWN_OUT = -OutFile
FIX_IMPORTS = powershell -Command "& { \
  Get-ChildItem -Path '$(OUT_DIR)' -Filter '*_pb2_grpc.py' | \
  ForEach-Object { \
    (Get-Content \$$_.FullName) -replace '^import (.*_pb2)', 'from . import \$$1' | \
    Set-Content -Path \$$_.FullName -Encoding UTF8 \
  } \
}"
else
MKDIR	 = mkdir -p
RM		 = rm -rf $(TMP_DIR)
DOWN	 = wget
DOWN_OUT = -O
FIX_IMPORTS = \
	for f in $(OUT_DIR)/*_pb2_grpc.py; do \
		sed -i 's/^import \(.*_pb2\)/from . import \1/' $$f; \
		done 
endif

docker-build:
	docker build --build-arg PORT=$(PORT) -t mod .

run: docker-build
	docker run --rm -it \
		--env-file .env \
		-p $(PORT):$(PORT) \
		-v $(CURDIR):/app \
		-e WATCHFILES_FORCE_POLLING=true \
		mod

clean:
	$(RM)

fetch-proto:
	$(MKDIR) "$(TMP_DIR)"
	$(DOWN) "https://raw.githubusercontent.com/esclient/protos/$(PROTO_TAG)/$(PROTO_NAME)" $(DOWN_OUT) "$(TMP_DIR)/$(PROTO_NAME)"

get-stubs: fetch-proto
	$(MKDIR) "$(OUT_DIR)"
	pdm run python -m grpc_tools.protoc \
		--proto_path="$(TMP_DIR)" \
		--python_out="$(OUT_DIR)" \
		--grpc_python_out="$(OUT_DIR)" \
		--pyi_out="$(OUT_DIR)" \
		"$(TMP_DIR)/$(PROTO_NAME)"
	$(FIX_IMPORTS)

update: get-stubs clean

format:
	black .
	isort .
	ruff check . --fix

lint:
	black --check .
	isort . --check --diff
	flake8 .
	ruff check .
	mypy --strict .

test:
	pytest
