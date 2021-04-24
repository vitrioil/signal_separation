#!/bin/bash

export PYTHONPATH=$(pwd)
poetry run pytest api/ -s
poetry run black . --line-length 79
