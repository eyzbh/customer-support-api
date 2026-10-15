# Customer Support API

A REST API for managing customer support tickets and analyzing text sentiment, built with **Python, FastAPI, SQLite, and Hugging Face Transformers**.

## Features

- Create customer support tickets
- Retrieve all tickets or a ticket by ID
- Update ticket status
- Validate request data using Pydantic
- Store ticket records in SQLite
- Handle missing tickets with appropriate HTTP errors
- Analyze text as positive, neutral, or negative using a pretrained Transformer model
- Return sentiment predictions with a confidence-like score
- Handle sentiment inference failures with an HTTP 503 response
- Automated API tests using pytest

## Tech Stack

- **Language:** Python 3.12
- **API Framework:** FastAPI
- **Database:** SQLite
- **Validation:** Pydantic
- **AI/ML:** Hugging Face Transformers and PyTorch
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
python -m pip install "fastapi[standard]" email-validator pytest httpx transformers torch
```

The sentiment-analysis model is downloaded automatically from Hugging Face when the service first loads. An internet connection is required for the initial download.

### 4. Run the API

```powershell
python -m uvicorn main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

### 5. Explore the API

Open the interactive API documentation:

http://127.0.0.1:8000/docs

### 6. Run the tests

From the project directory, run:

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
| POST | `/sentiment` | Analyze text sentiment |

## Sentiment Analysis

The `/sentiment` endpoint classifies submitted text as positive, neutral, or negative.

**Example request:**

```json
{
  "text": "The support team solved my problem quickly."
}
```

**Example response:**

```json
{
  "text": "The support team solved my problem quickly.",
  "sentiment": "positive",
  "score": 0.7627
}
```

The score is the model's confidence-like output. It does not guarantee that the prediction is correct.

Possible responses include:

- `200 OK` — sentiment analysis completed
- `422 Unprocessable Entity` — request validation failed
- `503 Service Unavailable` — sentiment inference failed

## Ticket Fields

Each ticket contains a customer name, email, subject, description, priority, and status.

Supported priorities: `low`, `medium`, `high`

Supported statuses: `open`, `closed`

## Project Status

The project includes ticket management, SQLite persistence, request validation, pretrained-model sentiment analysis, inference error handling, and automated API tests.

## Author

**Eyzrael Bekele Haile**