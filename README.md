# WMS Operations Portal

A web application built using FastAPI, SQLite, Jinja2 and Bootstrap for managing:

- WMS Instances
- Facilities
- Contacts
- Application URLs
- Rollouts & Extensions
- Version Management
- Deployment Tracking
- Documentation Library
- Training Requests
- Improvement Suggestions

## Technology

- Python
- FastAPI
- SQLite
- Jinja2
- Bootstrap 5

## Features

### Environment Management

Track production, test, development and archive environments.

### Extension Management

Manage rollout versions, supporting documentation and deployment history.

### Learning Hub

Browse training courses and submit training requests.

### Documentation Library

Store and download operational and technical documentation.

## Running Locally

```bash
pip install fastapi uvicorn
uvicorn app.main:app --reload
