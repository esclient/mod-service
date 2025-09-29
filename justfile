set windows-shell := ["powershell", "-NoProfile", "-Command"]
set dotenv-load := true

COMMON_URL := 'https://raw.githubusercontent.com/esclient/tools/refs/heads/main/python/common.just'

PROTO_TAG := 'v0.1.2'
PROTO_NAME := 'mod.proto'
TMP_DIR := '.proto'
OUT_DIR := 'src/modservice/grpc'
SERVICE_NAME := 'mod'

MKDIR_DOTJUST := if os() == 'windows' {
  'New-Item -ItemType Directory -Force -Path ".just" | Out-Null'
} else {
  'mkdir -p .just'
}

FETCH_CMD := if os() == 'windows' {
  'Invoke-WebRequest -Uri ' + COMMON_URL + ' -OutFile .just/common.just'
} else {
  'curl -fsSL ' + COMMON_URL + ' -o .just/common.just'
}

import? '.just/common.just'

default:
    @just --list

fetch-common:
    {{ MKDIR_DOTJUST }}
    {{ FETCH_CMD }}
