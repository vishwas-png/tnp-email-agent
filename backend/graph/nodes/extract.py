from langchain_groq import ChatGroq
from backend.schemas.models import ExtractedInfo,RawEmail
from backend.graph.nodes.prompts import TNP_EXTRACTION_PROMPT
from dotenv import load_dotenv
import os 

load_dotenv()

def extract_info(raw_email:RawEmail) -> ExtractedInfo:

    llm= ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0
    ).with_structured_output(ExtractedInfo)

    prompt=TNP_EXTRACTION_PROMPT.format(email_body=raw_email.body,received_at=raw_email.received_at)

    result=llm.invoke(prompt)

    result.received_at=raw_email.received_at

    return result
