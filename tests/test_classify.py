from datetime import datetime, timezone
from backend.graph.nodes import classify
from backend.schemas.models import GraphState, RawEmail, EmailCategory


class FakeLLM:
    def __init__(self):
        self.prompts = []

    def with_structured_output(self, schema, method=None):
        return self

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return classify.ClassifyResult(category=EmailCategory.INTERNSHIP)


def test_classify_prompt_includes_subject(monkeypatch):
    llm = FakeLLM()
    monkeypatch.setattr(classify, "llm", llm)
    email = RawEmail(gmail_message_id="m1", subject="Acme | SDE Intern | 6M", body="OA venue changed.",
                     received_at=datetime.now(timezone.utc))

    state = classify.classify_node(GraphState(raw_email=email))

    assert "Acme | SDE Intern | 6M" in llm.prompts[0]
    assert state.category == EmailCategory.INTERNSHIP
