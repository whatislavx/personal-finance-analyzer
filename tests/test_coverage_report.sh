#!/bin/bash

coverage run -m pytest --disable-warnings --cov=app.api.auth --cov=app.api.users --cov=app.api.jobs --cov=app.api.job_events --cov=app.api.job_results --cov=app.api.financial_data --cov=app.core.auth --cov=app.core.security
coverage report