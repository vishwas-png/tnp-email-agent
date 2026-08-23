from datetime import datetime, timezone, timedelta
from backend.schemas.models import GraphState, RawEmail, EmailCategory
from backend.graph.nodes.classify import classify_node
from backend.graph.nodes.summary import summary_node
from backend.graph.nodes.extract import extract_node

test_email =  RawEmail(gmail_message_id='19fa4493321fae1f', subject='Re: Fundwave | Full Stack | 6M+PPO', body="Dear students,\r\n\r\nThe OA venue has been changed to Computer Centre.\r\nThe reporting timing remains the same.\r\n\r\nRegards,\r\nPlaceComm'27\r\n\r\n\r\n", received_at=datetime(2026, 7, 27, 21, 24, 8, tzinfo=timezone(timedelta(seconds=19800))))

state = GraphState(raw_email=test_email)
state = classify_node(state)
print("Category:", state.category)

if state.category == EmailCategory.GENERAL_NOTICE:
    state = summary_node(state)
else:
    state = extract_node(state)

print(state)