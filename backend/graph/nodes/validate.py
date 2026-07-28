from backend.schemas.models import GraphState, EmailCategory

MAX_RETRIES = 2


def validate_node(state: GraphState) -> GraphState:
    info = state.extracted_info

    if state.category in (EmailCategory.PLACEMENT,EmailCategory.INTERNSHIP): 
        is_valid = info.summary is not None and (info.deadline is not None or info.company_name is not None) 
    else:
        is_valid = info.summary is not None

    state.validation_passed = is_valid

    if is_valid:
        state.processing_status = "verified"
    else:
        state.retry_count += 1
        if state.retry_count >= MAX_RETRIES:
            state.processing_status ="failed_validation"
        else:
            state.processing_status ="retrying"

    return state