MKDIR := 'mkdir -p'
RM := 'rm -rf ' + TMP_DIR
RM_MODERATION := 'rm -rf ' + MODERATION_TMP_DIR
DOWN := 'curl -fsSL'
DOWN_OUT := '-o'
PY_FIX_IMPORTS := 'for f in ' + OUT_DIR + '/*_pb2_grpc.py; do [ -f "$f" ] && sed -i "s/^import \\(.*_pb2\\)/from . import \\1/" "$f"; done'

clean:
    {{RM}}
    {{RM_MODERATION}}

fetch-proto:
    {{MKDIR}} "{{TMP_DIR}}"
    {{DOWN}} "https://raw.githubusercontent.com/esclient/protos/{{PROTO_TAG}}/{{PROTO_NAME}}" {{DOWN_OUT}} "{{TMP_DIR}}/{{PROTO_NAME}}"
    {{MKDIR}} "{{MODERATION_TMP_DIR}}"
    {{DOWN}} "https://raw.githubusercontent.com/esclient/protos/{{MODERATION_PROTO_TAG}}/{{MODERATION_PROTO_NAME}}" {{DOWN_OUT}} "{{MODERATION_TMP_DIR}}/{{MODERATION_PROTO_NAME}}"

run:
    ENV=dev PYTHONPATH=src ./tools/load_envs.sh pdm run run-server

gen-stubs: fetch-proto
    {{MKDIR}} "{{OUT_DIR}}"
    pdm run python -m grpc_tools.protoc \
      --proto_path="{{TMP_DIR}}" \
      --python_out="{{OUT_DIR}}" \
      --grpc_python_out="{{OUT_DIR}}" \
      --pyi_out="{{OUT_DIR}}" \
      "{{TMP_DIR}}/{{PROTO_NAME}}"
    {{PY_FIX_IMPORTS}}

update: gen-stubs clean

gen-stubs-moderation: fetch-proto
    {{MKDIR}} "{{OUT_DIR}}"
    pdm run python -m grpc_tools.protoc \
      --proto_path="{{MODERATION_TMP_DIR}}" \
      --python_out="{{OUT_DIR}}" \
      --grpc_python_out="{{OUT_DIR}}" \
      --pyi_out="{{OUT_DIR}}" \
      "{{MODERATION_TMP_DIR}}/{{MODERATION_PROTO_NAME}}"
    {{PY_FIX_IMPORTS}}

update-moderation: gen-stubs-moderation clean

format:
    black .
    isort .
    ruff check . --fix

lint:
    black --check .
    isort . --check --diff
    flake8 .
    ruff check .
    mypy --strict src/

test:
    pytest \
      --cov=src/{{SOURCE}} \
      --cov-report=xml:coverage.xml

prepare: format lint test
