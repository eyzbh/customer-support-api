
import sqlite3

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture
def client_with_approval_database(tmp_path, monkeypatch):
    database_name = str(tmp_path / "approval_api.db")

    with sqlite3.connect(database_name) as connection:
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE approval_requests (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL
                    CHECK (action IN ('close_ticket', 'reopen_ticket')),
                ticket_id INTEGER NOT NULL,
                requested_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                decided_at TEXT,
                decided_by TEXT,
                executed_at TEXT,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO tickets (
                customer_name, email, subject, description
            )
            VALUES (?, ?, ?, ?)
            """,
            ("API Test", "api@example.com", "Test ticket", "Test description"),
        )

    import persistent_approval_service
    import ticket_actions

    monkeypatch.setattr(
        main,
        "list_approval_requests",
        lambda status=None: (
            persistent_approval_service.list_approval_requests(
                status, database_name
            )
        ),
    )
    monkeypatch.setattr(
        main,
        "get_approval_request",
        lambda request_id: (
            persistent_approval_service.get_approval_request(
                request_id, database_name
            )
        ),
    )
    monkeypatch.setattr(
        main,
        "decide_approval",
        lambda request_id, decision, decided_by: (
            persistent_approval_service.decide_approval(
                request_id, decision, decided_by, database_name
            )
        ),
    )
    monkeypatch.setattr(
        main,
        "execute_approved_action",
        lambda request_id: ticket_actions.execute_approved_action(
            request_id, database_name
        ),
    )

    # Configure distinct test identities and roles.
    monkeypatch.delenv("SUPPORT_API_KEY", raising=False)
    monkeypatch.setenv(
        "SUPPORT_API_USERS",
        "reviewer-test-key:reviewer-1,agent-test-key:support-agent",
    )
    monkeypatch.setenv("SUPPORT_API_REVIEWERS", "reviewer-1")

    client = TestClient(main.app)
    client.headers.update(
        {"Authorization": "Bearer reviewer-test-key"}
    )

    return client, database_name


def create_pending_request(database_name):
    from persistent_approval_service import create_approval_request

    return create_approval_request(
        "close_ticket", 1, "test-agent", database_name
    )


def test_list_approvals(client_with_approval_database):
    client, database_name = client_with_approval_database
    create_pending_request(database_name)

    response = client.get("/approvals")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "pending"


def test_filter_pending_approvals(client_with_approval_database):
    client, database_name = client_with_approval_database
    create_pending_request(database_name)

    response = client.get("/approvals?status=pending")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_invalid_status_filter_is_rejected(client_with_approval_database):
    client, _ = client_with_approval_database

    response = client.get("/approvals?status=unknown")

    assert response.status_code == 422


def test_get_approval_by_id(client_with_approval_database):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.get(f"/approvals/{request['request_id']}")

    assert response.status_code == 200
    assert response.json()["request_id"] == request["request_id"]


def test_missing_approval_returns_404(client_with_approval_database):
    client, _ = client_with_approval_database

    response = client.get("/approvals/not-a-real-request")

    assert response.status_code == 404


def test_approve_request(client_with_approval_database):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["decided_by"] == "reviewer-1"
def test_extra_decided_by_field_is_rejected(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={
            "decision": "approved",
            "decided_by": "fake-reviewer",
        },
    )

    assert response.status_code == 422

    from persistent_approval_service import get_approval_request

    saved_request = get_approval_request(
        request["request_id"], database_name
    )
    assert saved_request["status"] == "pending"
    assert saved_request["decided_by"] is None

def test_reject_request(client_with_approval_database):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "rejected"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["decided_by"] == "reviewer-1"


def test_non_reviewer_cannot_decide_approval(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/decision",
        headers={"Authorization": "Bearer agent-test-key"},
        json={"decision": "approved"},
    )

    assert response.status_code == 403

    from persistent_approval_service import get_approval_request

    saved_request = get_approval_request(
        request["request_id"], database_name
    )
    assert saved_request["status"] == "pending"
    assert saved_request["decided_by"] is None


def test_invalid_decision_is_rejected(client_with_approval_database):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "maybe"},
    )

    assert response.status_code == 422


def test_deciding_request_twice_returns_conflict(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)
    url = f"/approvals/{request['request_id']}/decision"

    first_response = client.post(
        url,
        json={"decision": "approved"},
    )
    second_response = client.post(
        url,
        json={"decision": "rejected"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_execute_pending_approval_is_forbidden(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    response = client.post(
        f"/approvals/{request['request_id']}/execute"
    )

    assert response.status_code == 403

    from persistent_approval_service import get_approval_request

    saved_request = get_approval_request(
        request["request_id"], database_name
    )
    assert saved_request["executed_at"] is None


def test_execute_rejected_approval_is_forbidden(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    decision_response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "rejected"},
    )
    assert decision_response.status_code == 200

    response = client.post(
        f"/approvals/{request['request_id']}/execute"
    )

    assert response.status_code == 403

    from persistent_approval_service import get_approval_request

    saved_request = get_approval_request(
        request["request_id"], database_name
    )
    assert saved_request["executed_at"] is None


def test_execute_approved_request_closes_ticket(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    decision_response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "approved"},
    )
    assert decision_response.status_code == 200

    response = client.post(
        f"/approvals/{request['request_id']}/execute"
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["status"] == "closed"

    with sqlite3.connect(database_name) as connection:
        ticket = connection.execute(
            "SELECT status FROM tickets WHERE id = 1"
        ).fetchone()
        approval = connection.execute(
            """
            SELECT executed_at
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request["request_id"],),
        ).fetchone()

    assert ticket[0] == "closed"
    assert approval[0] is not None


def test_executing_approval_twice_returns_conflict(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    decision_response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "approved"},
    )
    assert decision_response.status_code == 200

    first_response = client.post(
        f"/approvals/{request['request_id']}/execute"
    )
    second_response = client.post(
        f"/approvals/{request['request_id']}/execute"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_execute_unknown_approval_returns_404(
    client_with_approval_database,
):
    client, _ = client_with_approval_database

    response = client.post(
        "/approvals/unknown-request/execute"
    )

    assert response.status_code == 404


def test_list_approvals_requires_authentication(
    client_with_approval_database,
):
    client, _ = client_with_approval_database

    response = client.get(
        "/approvals",
        headers={"Authorization": ""},
    )

    assert response.status_code == 401
def test_non_reviewer_cannot_execute_approved_request(
    client_with_approval_database,
):
    client, database_name = client_with_approval_database
    request = create_pending_request(database_name)

    # A reviewer approves the request.
    decision_response = client.post(
        f"/approvals/{request['request_id']}/decision",
        json={"decision": "approved"},
    )
    assert decision_response.status_code == 200

    # A regular support agent tries to execute it.
    response = client.post(
        f"/approvals/{request['request_id']}/execute",
        headers={"Authorization": "Bearer agent-test-key"},
    )

    assert response.status_code == 403

    from persistent_approval_service import get_approval_request

    saved_request = get_approval_request(
        request["request_id"], database_name
    )
    assert saved_request["status"] == "approved"
    assert saved_request["executed_at"] is None