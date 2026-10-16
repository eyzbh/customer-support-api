# Customer Support API

A REST API for managing customer support tickets and analyzing customer messages, built with **Python, FastAPI, SQLite, Hugging Face Transformers, and Ollama**.

## Features

- Create customer support tickets
- Retrieve all tickets or a ticket by ID
- Update ticket status
- Validate request data using Pydantic
- Store ticket records in SQLite
- Handle missing tickets with appropriate HTTP errors
- Analyze text sentiment using a pretrained Transformer model
- Analyze support messages using a local LLM
- Classify support issues and assign a priority
- Generate suggested customer replies using structured output
- Handle AI inference failures with appropriate HTTP errors
- Automated API tests using pytest

## Tech Stack

- **Language:** Python 3.12
- **API Framework:** FastAPI
- **Database:** SQLite
- **Validation:** Pydantic
- **Sentiment Analysis:** Hugging Face Transformers and PyTorch
- **Local LLM:** Ollama with Qwen3 4B Instruct
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

### 3. Install Python dependencies

```powershell
python -m pip install "fastapi[standard]" email-validator pytest httpx transformers torch ollama
```

### 4. Set up the local LLM

Install Ollama from [https://ollama.com/download](https://ollama.com/download).

Then download the model:

```powershell
ollama pull qwen3:4b-instruct
```

Make sure Ollama is running before using the ticket analyzer. The model runs locally, so the analyzer does not require a paid LLM API key. An internet connection is needed to download the model initially.

### 5. Run the API

From the project directory, run:

```powershell
python -m uvicorn main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

### 6. Explore the API

Open the interactive API documentation:

http://127.0.0.1:8000/docs

### 7. Run the tests

```powershell
python -m pytest -v
```

The ticket analyzer tests mock the AI function, so those tests do not need to run the model for every test.

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
| POST | `/analyze-ticket` | Analyze a support message using a local LLM |

## Sentiment Analysis

The `/sentiment` endpoint classifies submitted text as positive, neutral, or negative using a pretrained Transformer model.

### Example request

```json
{
  "text": "The support team solved my problem quickly."
}
```

### Example response

```json
{
  "text": "The support team solved my problem quickly.",
  "sentiment": "positive",
  "score": 0.7627
}
```

The score is a confidence-like model output and does not guarantee that the prediction is correct.

Possible responses:

- `200 OK` — sentiment analysis completed
- `422 Unprocessable Entity` — request validation failed
- `503 Service Unavailable` — sentiment inference failed

The sentiment model may download its files from Hugging Face when it first loads. An internet connection is required for the initial download.

## AI Support Ticket Analysis

The `/analyze-ticket` endpoint uses the local Qwen3 4B Instruct model through Ollama to analyze a customer message.

### Example request

```json
{
  "message": "I was charged twice for my subscription."
}
```

### Example response

```json
{
  "category": "billing",
  "priority": "high",
  "suggested_reply": "We will review the duplicate charge."
}
```

The response fields are:

- **category:** The type of support issue, such as billing, technical support, or account access.
- **priority:** The estimated urgency of the issue.
- **suggested_reply:** A proposed response for the support team to review.

The exact output depends on the customer's message and the model's analysis. Suggested replies should be reviewed before being sent to customers.

Possible responses:

- `200 OK` — ticket analysis completed
- `422 Unprocessable Entity` — request validation failed
- `503 Service Unavailable` — ticket analysis failed

## Ticket Fields

Each ticket contains:

- Customer name
- Email
- Subject
- Description
- Priority
- Status

Supported priorities: `low`, `medium`, `high`

Supported statuses: `open`, `closed`

## Project Status

The project includes REST API development, SQLite persistence, request validation, pretrained-model sentiment analysis, local LLM integration, structured ticket analysis, error handling, and automated testing.

## Author

**Eyzrael Bekele Haile**
