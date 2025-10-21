MKDIR := 'mkdir -p'
RM := 'rm -rf ' + TMP_DIR
DOWN := 'curl -fsSL'
DOWN_OUT := '-o'
PY_FIX_IMPORTS := 'for f in ' + OUT_DIR + '/*_pb2_grpc.py; do [ -f "$f" ] && sed -i "s/^import \\(.*_pb2\\)/from . import \\1/" "$f"; done'

clean:
    {{RM}}

fetch-proto:
    {{MKDIR}} "{{TMP_DIR}}"
    {{DOWN}} "https://raw.githubusercontent.com/esclient/protos/{{PROTO_TAG}}/{{PROTO_NAME}}" {{DOWN_OUT}} "{{TMP_DIR}}/{{PROTO_NAME}}"

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
    pytest \
      --cov=src/{{SOURCE}} \
      --cov-report=xml:coverage.xml

prepare: format lint test
