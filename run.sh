#!/bin/bash
python -m uvicorn api.main:api --reload --host 0.0.0.0
