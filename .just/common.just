MKDIR := if os() == 'windows' { 'powershell -Command "New-Item -ItemType Directory -Force -Path"' } else { 'mkdir -p' }
RM := if os() == 'windows' { 'powershell -NoProfile -Command "Remove-Item -Path ' + TMP_DIR + ' -Recurse -Force"' } else { 'rm -rf ' + TMP_DIR }
DOWN := if os() == 'windows' { 'powershell -Command "Invoke-WebRequest -Uri"' } else { 'wget' }
DOWN_OUT := if os() == 'windows' { '-OutFile' } else { '-O' }
PY_FIX_IMPORTS := if os() == 'windows' {
  "Get-ChildItem -Path '" + OUT_DIR + "' -Filter '*_pb2_grpc.py' | ForEach-Object { (Get-Content $_.FullName) -replace '^\\s*import (.*_pb2)', 'from . import $1' | Set-Content -Path $_.FullName -Encoding UTF8 }"
} else {
  'bash -lc "for f in ' + OUT_DIR + '/*_pb2_grpc.py; do [ -f \"$f\" ] && sed -i \"s/^import \\(.*_pb2\\)/from . import \\1/\" \"$f\"; done"'
}

clean:
    {{RM}}

fetch-proto:
    {{MKDIR}} "{{TMP_DIR}}"
    {{DOWN}} "https://raw.githubusercontent.com/esclient/protos/{{PROTO_TAG}}/{{PROTO_NAME}}" {{DOWN_OUT}} "{{TMP_DIR}}/{{PROTO_NAME}}"

docker-build:
    docker build --build-arg PORT={{ env_var('PORT') }} -t {{SERVICE_NAME}} .

run: docker-build
    docker run --rm -it \
      --env-file .env \
      -p {{ env_var('PORT') }}:{{ env_var('PORT') }} \
      -v {{invocation_directory()}}:/app \
      -e WATCHFILES_FORCE_POLLING=true \
      {{SERVICE_NAME}}

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
    pytest

prepare: format lint test
