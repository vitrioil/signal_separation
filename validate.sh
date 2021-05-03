#!/bin/bash

export PYTHONPATH=$(pwd)
poetry run black . --line-length 79
poetry run pytest . --cov=. --cov-branch
