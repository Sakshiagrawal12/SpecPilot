from typing import Any, Dict, List
from typing_extensions import TypedDict


class RequirementState(TypedDict, total=False):

    # =====================================================
    # SESSION / PROJECT
    # =====================================================

    project_id: int
    project_name: str
    thread_id: str

    # =====================================================
    # USER MESSAGE
    # =====================================================

    user_message: str

    # =====================================================
    # REQUIREMENTS
    # =====================================================

    requirements: Dict[str, Any]

    # =====================================================
    # CONVERSATION
    # =====================================================

    messages: List[Dict[str, str]]

    # =====================================================
    # INTENT / MESSAGE CLASSIFICATION
    # =====================================================

    # Examples:
    # answer
    # question
    # correction
    # skip
    # generate_for_me
    # off_track
    # no_op
    message_type: str

    # =====================================================
    # CURRENT FIELD
    # =====================================================

    current_field: str

    # =====================================================
    # CORRECTION
    # =====================================================

    # Field that the user wants to change
    correction_field: str

    # New value extracted from the correction
    correction_value: Any

    # =====================================================
    # CLARIFICATION
    # =====================================================

    # Number of times the user has asked for clarification
    # for each field.
    #
    # Example:
    # {
    #     "business_objective": 2,
    #     "target_users": 1
    # }
    clarification_attempts: Dict[str, int]

    # =====================================================
    # GENERATED VALUE
    # =====================================================

    # Used when the user says:
    # "write it for me"
    # "suggest one"
    # "according to you"
    # etc.
    #
    # The generated value is NOT immediately stored.
    # It first waits for user confirmation.

    pending_generated_field: str
    pending_generated_value: str

    # True while waiting for:
    # yes / no / accept / reject
    pending_confirmation: bool

    # =====================================================
    # EXTRACTION
    # =====================================================

    extracted_value: Any
    extracted_confidence: float
    extracted_reason: str

    extracted_off_track: bool
    extracted_off_track_reason: str

    # Result of extraction processing
    #
    # Examples:
    # no_op
    # accepted
    # low_confidence
    # blank
    # off_track
    extraction_outcome: str

    # Number of unsuccessful attempts for current field
    attempts_so_far: int

    # =====================================================
    # EVALUATION
    # =====================================================

    missing_fields: List[str]

    completeness_status: str
    completeness_score: float

    # =====================================================
    # AGENT RESPONSE
    # =====================================================

    agent_response: str

    # Examples:
    # wait_for_user
    # generate_prd
    # review_requirements
    next_action: str

    document_summary:str

    # ===================================================== # DOCUMENT # ===================================================== 
    uploaded_filename: str 
    uploaded_file_bytes: bytes 
    document_filled_fields: List[str] 
    document_processed:bool
    
    # ===================================================== # CONVERSATION # ===================================================== 
    conversation_history: List[Dict[str, Any]]