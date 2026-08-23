from langgraph.graph import StateGraph , START ,END
from backend.schemas.models import EmailCategory, GraphState,RawEmail
from backend.graph.nodes.classify import classify_node
from backend.graph.nodes.extract import extract_node
from backend.graph.nodes.summary import summary_node
from backend.graph.nodes.validate import validate_node
from datetime import datetime, timezone, timedelta




def route_after_classify(state: GraphState) -> str:
   if state.category == EmailCategory.GENERAL_NOTICE: 
      return "summary"
   else: 
      return "extract"

def route_after_validate(state:GraphState)->str:
   if state.validation_passed:
      return END
   else:
     if state.processing_status == "retrying":
       if state.category == EmailCategory.GENERAL_NOTICE:
         return "summary"
       else:
         return "extract"
     else:
      return END

graph=StateGraph(GraphState)

graph.add_node("classify",classify_node)
graph.add_node("extract",extract_node)
graph.add_node("summary",summary_node)
graph.add_node("validate",validate_node)

graph.add_edge(START,"classify")
graph.add_conditional_edges("classify",route_after_classify)
graph.add_edge("extract","validate")
graph.add_edge("summary","validate")
graph.add_conditional_edges("validate",route_after_validate)

workflow=graph.compile()



      