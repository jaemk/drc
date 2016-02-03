#!/bin/bash
gunicorn drc.wsgi:application --bind localhost:8001 --workers 4 --max-requests 500
