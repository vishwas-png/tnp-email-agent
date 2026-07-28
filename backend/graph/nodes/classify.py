from langchain_groq import ChatGroq
from pydantic import BaseModel
from backend.schemas.models import GraphState, EmailCategory
from backend.graph.nodes.prompts import TNP_CLASSIFY_PROMPT


class ClassifyResult(BaseModel):
    category: EmailCategory

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
def classify_node(state: GraphState) -> GraphState:
    structured_llm=llm.with_structured_output(ClassifyResult, method="json_mode")
    prompt = TNP_CLASSIFY_PROMPT.format(email_body=state.raw_email.body)
    
    result = structured_llm.invoke(prompt)
    state.category = result.category
    return state