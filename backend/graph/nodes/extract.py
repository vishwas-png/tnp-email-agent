from langchain_groq import ChatGroq
from backend.schemas.models import GraphState, ExtractedInfo

from backend.graph.nodes.prompts import TNP_EXTRACTION_PROMPT
from dotenv import load_dotenv
import os 

load_dotenv()

llm=ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
)



def extract_node(state:GraphState)->GraphState:
     prompt=TNP_EXTRACTION_PROMPT.format(email_body=state.raw_email.body,received_at=state.raw_email.received_at,subject=state.raw_email.subject)
     result=llm.with_structured_output(ExtractedInfo).invoke(prompt)

     result.category=state.category
     result.received_at=state.raw_email.received_at

     if result.deadline is not None and result.deadline.tzinfo is None:
          result.deadline=result.deadline.replace(tzinfo=state.raw_email.received_at.tzinfo)

     state.extracted_info=result

   

     return state
