# Customer Support API

A REST API for managing customer support tickets, analyzing customer messages, and answering questions from a knowledge base. Built with **Python, FastAPI, SQLite, Hugging Face Transformers, and Ollama**.

## Features

- Create, retrieve, and update customer support tickets
- Validate requests using Pydantic
- Persist ticket data in SQLite
- Analyze sentiment using a pretrained Transformer model
- Analyze support messages using a local LLM
- Classify support issues, estimate priority, and suggest customer replies
- Answer knowledge-base questions using retrieval-augmented generation (RAG)
- Authenticate protected endpoints using API keys
- Enforce reviewer-only approval and execution permissions
- Support approval workflows for ticket actions
- Limit knowledge endpoint requests to 10 per minute
- Return controlled error responses when AI services fail
- Automated tests for API behavior, authentication, authorization, and reliability

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| API framework | FastAPI |
| Database | SQLite |
| Validation | Pydantic |
| Sentiment analysis | Hugging Face Transformers and PyTorch |
| Local LLM | Ollama with Qwen3 4B Instruct |
| Testing | pytest and FastAPI TestClient |
| Rate limiting | SlowAPI |
| Version control | Git and GitHub |

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/eyzbh/customer-support-api.git
cd customer-support-api
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the project's dependencies:

```powershell
python -m pip install -r requirements.txt
```


### 4. Set up Ollama

Install Ollama from https://ollama.com/download.

Download the model:

```powershell
ollama pull qwen3:4b-instruct
```

Ensure Ollama is running before using endpoints that depend on the local LLM. The model runs locally, so these features do not require a paid hosted LLM API key. An internet connection is needed to download the model initially.

The Hugging Face sentiment model may also need an internet connection to download its model files on first use.

### 5. Configure API authentication

Ticket endpoints require a valid API key. Configure users with the `SUPPORT_API_USERS` environment variable.

Example for the current PowerShell session:

```powershell
$env:SUPPORT_API_USERS = "agent-key:support-agent,reviewer-key:reviewer-1"
$env:SUPPORT_API_REVIEWERS = "reviewer-1"
```

The format of `SUPPORT_API_USERS` is a comma-separated list of `api-key:username` entries. `SUPPORT_API_REVIEWERS` is a comma-separated list of usernames permitted to perform reviewer-only operations.

Use your own strong, unique API keys in real deployments. Do not commit real credentials to GitHub or place them directly in source code.

Requests to protected ticket endpoints must include a bearer token:

```http
Authorization: Bearer agent-key
```

An authenticated support agent can access protected ticket endpoints, but only configured reviewers can make approval decisions or execute approved actions.

If authentication is not configured, protected endpoints return `503 Service Unavailable`. Missing or invalid credentials return `401 Unauthorized`, and users without reviewer permission receive `403 Forbidden`.

### 6. Start the API

```powershell
python -m uvicorn main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### 7. Run the tests

Run the complete test suite:

```powershell
python -m pytest -q
```

The latest verified result during development was **117 passing tests**. Run the suite again after making changes to confirm the current result.

## API Endpoints

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/` | Welcome message | Public |
| GET | `/health` | Health check | Public |
| POST | `/tickets` | Create a ticket | API key |
| GET | `/tickets` | List tickets | API key |
| GET | `/tickets/{ticket_id}` | Retrieve a ticket | API key |
| PATCH | `/tickets/{ticket_id}` | Update ticket status | API key |
| POST | `/sentiment` | Analyze sentiment | No API key dependency configured |
| POST | `/analyze-ticket` | Analyze a support message | No API key dependency configured |
| POST | `/ask-knowledge` | Ask a knowledge-base question | Rate-limited |
| GET | `/approvals` | List approval requests | API key |
| GET | `/approvals/{request_id}` | Retrieve an approval request | API key |
| POST | `/approvals/{request_id}/decision` | Approve or reject a request | Reviewer |
| POST | `/approvals/{request_id}/execute` | Execute an approved action | Reviewer |

The access descriptions above reflect the current application routes. Consider whether the AI endpoints should also require authentication before deploying the API publicly.

## Rate Limiting

The `/ask-knowledge` endpoint is configured with a limit of **10 requests per minute per client IP address**.

Requests exceeding the configured limit receive HTTP `429 Too Many Requests`. This limit is based on the client address, so deployments behind a reverse proxy should configure and validate proxy handling carefully.

## Sentiment Analysis

The `/sentiment` endpoint classifies text as positive, neutral, or negative using a pretrained Transformer model.

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

The score is a model confidence-like output and does not guarantee that the prediction is correct.

Possible responses:

- `200 OK` — analysis completed
- `422 Unprocessable Entity` — request validation failed
- `503 Service Unavailable` — sentiment inference failed

## AI Support Ticket Analysis

The `/analyze-ticket` endpoint uses the local Qwen3 4B Instruct model through Ollama.

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

The response contains an estimated issue category, priority, and suggested reply. The exact output depends on the customer's message and the model's analysis. Support staff should review suggested replies before sending them to customers.

Possible responses:

- `200 OK` — analysis completed
- `422 Unprocessable Entity` — request validation failed
- `503 Service Unavailable` — ticket analysis failed

## Knowledge-Base Questions

The `/ask-knowledge` endpoint answers questions using the project's RAG service.

### Example request

```json
{
  "question": "I forgot my password. How can I get back into my account?"
}
```

The response includes the submitted question, an answer, and source information returned by the retrieval service. The exact answer and sources depend on the documents indexed by the project.

Possible responses:

- `200 OK` — question answered
- `422 Unprocessable Entity` — request validation failed
- `429 Too Many Requests` — rate limit exceeded
- `503 Service Unavailable` — knowledge service failed

## Ticket Fields

Ticket records include:

- Customer name
- Email
- Subject
- Description
- Priority
- Status

Supported priorities: `low`, `medium`, `high`

Supported statuses: `open`, `closed`

## Approval Workflows

The approval workflow supports review of proposed ticket actions before execution.

- Approval requests can be listed and retrieved.
- Configured reviewers can approve or reject pending requests.
- Only reviewers can execute approved actions.
- Actions are checked to prevent execution before approval or repeated execution.
- Unsupported actions and missing tickets are rejected.

Approval decisions accept `approved` or `rejected`. Extra fields in the decision request are rejected by request validation.

## Error Handling

The API uses appropriate HTTP responses for common failures, including:

- `401 Unauthorized` — missing or invalid API key
- `403 Forbidden` — insufficient reviewer permission
- `404 Not Found` — ticket or approval request does not exist
- `409 Conflict` — approval workflow conflict or invalid execution state
- `422 Unprocessable Entity` — invalid request data
- `429 Too Many Requests` — rate limit exceeded
- `503 Service Unavailable` — configured service or model failure

Unexpected AI-service errors are logged on the server, while the knowledge endpoint returns a generic error message to clients rather than exposing internal exception details.

## Project Status

The project demonstrates REST API development, database persistence, input validation, local AI inference, RAG, authentication, role-based authorization, approval workflows, rate limiting, controlled error handling, and automated testing.

## Author

**Eyzrael Bekele Haile**
