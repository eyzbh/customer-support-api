# Customer Support API

A REST API for managing customer support tickets, built with **FastAPI, Python, SQLite, and pytest**.

## Features

- Create customer support tickets
- Retrieve all tickets
- Retrieve a ticket by ID
- Update ticket status
- Validate request data using Pydantic
- Store ticket records in a SQLite database
- Handle missing tickets with appropriate HTTP errors
- Automated API tests using pytest

## Tech Stack

- **Language:** Python 3.12
- **API Framework:** FastAPI
- **Database:** SQLite
- **Validation:** Pydantic
- **Testing:** pytest and FastAPI TestClient
- **Version Control:** Git and GitHub

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/eyzbh/customer-support-api.git
cd customer-support-api
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install "fastapi[standard]" email-validator pytest httpx
```

### 4. Run the API

```powershell
python -m uvicorn main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

### 5. Explore the API

Open the interactive API documentation:

`http://127.0.0.1:8000/docs`

### 6. Run the tests

In a separate terminal, from the project directory, run:

```powershell
python -m pytest -v
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| POST | `/tickets` | Create a support ticket |
| GET | `/tickets` | Retrieve all tickets |
| GET | `/tickets/{ticket_id}` | Retrieve a ticket by ID |
| PATCH | `/tickets/{ticket_id}` | Update ticket status |

## Ticket Fields

Each ticket contains a customer name, email, subject, description, priority, and status.

Supported priorities: `low`, `medium`, `high`

Supported statuses: `open`, `closed`

## Project Status

The initial version implements ticket creation, retrieval, status updates, SQLite persistence, request validation, and automated tests.

## Author

**Eyzrael Bekele Haile**