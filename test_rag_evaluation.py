
from rag_evaluation import evaluation_questions
from rag_service import answer_question


def test_evaluation_covers_supported_and_unsupported_questions():
    assert len(evaluation_questions) == 4

    supported = [
        item for item in evaluation_questions
        if item["expected_source"] is not None
    ]
    unsupported = [
        item for item in evaluation_questions
        if item["expected_source"] is None
    ]

    assert len(supported) == 3
    assert len(unsupported) == 1


def test_supported_questions_have_expected_sources():
    for item in evaluation_questions:
        if item["expected_source"] is None:
            continue

        result = answer_question(item["question"])
        source_titles = [
            source["title"] for source in result["sources"]
        ]

        assert item["expected_source"] in source_titles


def test_unsupported_question_does_not_invent_policy():
    result = answer_question(
        "Does the company offer student discounts?"
    )

    answer = result["answer"].lower()

    assert any(
        phrase in answer
        for phrase in [
            "not have enough information",
            "don't have enough information",
            "do not have enough information",
            "insufficient information",
        ]
    )
