set windows-shell := ["sh", "-c"]
set dotenv-load := true

COMMON_JUST_URL := 'https://raw.githubusercontent.com/esclient/tools/refs/heads/main/python/common.just'
LOAD_ENVS_URL := 'https://raw.githubusercontent.com/esclient/tools/refs/heads/main/load_envs.sh'

PROTO_TAG := 'v0.1.2'
PROTO_NAME := 'mod.proto'
TMP_DIR := '.proto'
OUT_DIR := 'src/modservice/grpc'
SERVICE_NAME := 'mod'

MKDIR_TOOLS := 'mkdir -p tools'

FETCH_COMMON_JUST := 'curl -fsSL ' + COMMON_JUST_URL + ' -o tools/common.just'
FETCH_LOAD_ENVS := 'curl -fsSL ' + LOAD_ENVS_URL + ' -o tools/load_envs.sh'

import? 'tools/common.just'

default:
    @just --list

fetch-tools:
    {{ MKDIR_TOOLS }}
    {{ FETCH_COMMON_JUST }}
    {{ FETCH_LOAD_ENVS }}
