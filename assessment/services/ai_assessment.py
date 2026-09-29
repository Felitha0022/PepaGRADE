import json
import os
import logging

from dotenv import load_dotenv
from openai import OpenAI
from mistralai.client import Mistral

from .prompt_builder import build_assessment_prompt


load_dotenv()

logger = logging.getLogger(__name__)


class AIAssessmentError(Exception):
    """
    Custom error used when all AI assessment services fail.
    """
    pass


# ============================================================
# CLEAN AI RESPONSE
# ============================================================

def clean_json_response(response_text):
    """
    Clean and convert an AI response into a Python dictionary.
    """

    if response_text is None:
        raise ValueError(
            "The AI service returned an empty response."
        )

    # --------------------------------------------------------
    # Already a dictionary
    # --------------------------------------------------------

    if isinstance(response_text, dict):

        result = response_text

    # --------------------------------------------------------
    # String response
    # --------------------------------------------------------

    elif isinstance(response_text, str):

        result = response_text.strip()

        if not result:

            raise ValueError(
                "The AI service returned an empty response."
            )

        # Remove Markdown JSON code fences
        if result.startswith("```json"):

            result = result[7:]

        elif result.startswith("```"):

            result = result[3:]

        if result.endswith("```"):

            result = result[:-3]

        result = result.strip()

        try:

            result = json.loads(
                result
            )

        except json.JSONDecodeError as error:

            logger.error(
                "Invalid JSON returned by AI: %s",
                result[:1000]
            )

            raise ValueError(
                "The AI service returned an invalid JSON response."
            ) from error

    # --------------------------------------------------------
    # List response
    # --------------------------------------------------------

    elif isinstance(response_text, list):

        text_parts = []

        for item in response_text:

            if isinstance(item, str):

                text_parts.append(item)

            elif isinstance(item, dict):

                # Common structured response formats
                if "text" in item:

                    text_parts.append(
                        str(item["text"])
                    )

                elif "content" in item:

                    text_parts.append(
                        str(item["content"])
                    )

        combined_text = "".join(
            text_parts
        ).strip()

        if not combined_text:

            raise ValueError(
                "The AI service returned an empty structured response."
            )

        # Remove Markdown code fences
        if combined_text.startswith("```json"):

            combined_text = combined_text[7:]

        elif combined_text.startswith("```"):

            combined_text = combined_text[3:]

        if combined_text.endswith("```"):

            combined_text = combined_text[:-3]

        combined_text = combined_text.strip()

        try:

            result = json.loads(
                combined_text
            )

        except json.JSONDecodeError as error:

            logger.error(
                "Invalid JSON returned by AI: %s",
                combined_text[:1000]
            )

            raise ValueError(
                "The AI service returned an invalid JSON response."
            ) from error

    else:

        raise ValueError(
            "The AI service returned an unexpected response format."
        )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    if not isinstance(result, dict):

        raise ValueError(
            "The AI service returned an unexpected assessment format."
        )

    if "criterion_scores" not in result:

        raise ValueError(
            "The AI assessment is missing criterion scores."
        )

    return result


# ============================================================
# DEEPSEEK — PRIMARY AI SERVICE
# ============================================================

def assess_with_deepseek(prompt):

    api_key = os.getenv(
        "DEEPSEEK_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "DEEPSEEK_API_KEY was not found."
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

    response = client.chat.completions.create(

        model="deepseek-flash",

        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic writing assessment assistant. "
                    "Return ONLY valid JSON. "
                    "Do not use Markdown code fences."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        response_format={
            "type": "json_object"
        },

        max_tokens=8192,

        temperature=0.2
    )

    # --------------------------------------------------------
    # Get response content safely
    # --------------------------------------------------------

    message = response.choices[0].message

    result = message.content

    logger.info(
        "DeepSeek returned response type: %s",
        type(result).__name__
    )

    return clean_json_response(
        result
    )


# ============================================================
# MISTRAL — BACKUP AI SERVICE
# ============================================================

def assess_with_mistral(prompt):

    api_key = os.getenv(
        "MISTRAL_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "MISTRAL_API_KEY was not found."
        )

    client = Mistral(
        api_key=api_key
    )

    response = client.chat.complete(

        model="mistral-small-latest",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # --------------------------------------------------------
    # Get Mistral response
    # --------------------------------------------------------

    message = response.choices[0].message

    result = message.content

    logger.info(
        "Mistral returned response type: %s",
        type(result).__name__
    )

    return clean_json_response(
        result
    )


# ============================================================
# DEMO ASSESSMENT — PRESENTATION FALLBACK
# ============================================================

def get_demo_assessment():

    """
    Returns a pre-generated assessment result for
    demonstration purposes when live AI services
    are unavailable.

    This does NOT call an external AI API.
    """

    return {

        "criterion_scores": {

            "Content and Relevance": {
                "score": 18,
                "max_score": 25,
                "feedback": (
                    "The paper addresses the selected topic "
                    "and presents relevant ideas."
                )
            },

            "Organization and Structure": {
                "score": 16,
                "max_score": 20,
                "feedback": (
                    "The paper follows a generally logical "
                    "structure, although some sections could "
                    "be developed further."
                )
            },

            "Evidence and Analysis": {
                "score": 14,
                "max_score": 20,
                "feedback": (
                    "Relevant evidence is included, but "
                    "deeper analysis and stronger supporting "
                    "evidence would improve the discussion."
                )
            },

            "Academic Writing": {
                "score": 15,
                "max_score": 20,
                "feedback": (
                    "The writing is generally understandable "
                    "and appropriate for academic work, with "
                    "some areas requiring grammatical revision."
                )
            },

            "Referencing": {
                "score": 8,
                "max_score": 15,
                "feedback": (
                    "References are included, although "
                    "citation consistency and formatting "
                    "could be improved."
                )
            }
        },

        "total_score": 71,

        "ai_score": 71,

        "ai_grade": "B",

        "grade": "B",

        "citation_analysis": {
            "in_text_citations_found": 0,
            "matched_references": 0,
            "unmatched_citations": 0,
            "uncited_references": 0,
            "unsupported_claims": [],
            "citation_issues": [],
            "overall_observation": (
                "The paper contains citations, but citation "
                "consistency should be improved."
            )
        },

        "reference_analysis": {
            "references_found": 0,
            "missing_or_incomplete_references": [],
            "duplicate_references": [],
            "formatting_issues": [],
            "potentially_suspicious_references": [],
            "overall_observation": (
                "References are present and generally relevant. "
                "Some formatting improvements are recommended."
            )
        },

        "grammar_analysis": {
            "grammar_issues": [],
            "spelling_issues": [],
            "punctuation_issues": [],
            "sentence_clarity_issues": [],
            "examples_and_corrections": [],
            "overall_observation": (
                "The writing is generally clear. Several "
                "sentences could be revised for grammar, "
                "punctuation, and clarity."
            )
        },

        "academic_writing_analysis": {
            "academic_tone": (
                "The submission generally maintains an "
                "appropriate academic tone."
            ),
            "clarity": (
                "The main ideas are generally understandable."
            ),
            "coherence": (
                "The discussion demonstrates a generally "
                "logical flow."
            ),
            "sentence_structure": (
                "Some sentences could be revised for clarity "
                "and grammatical accuracy."
            ),
            "paragraph_structure": (
                "The paragraphs generally follow a recognizable "
                "academic structure."
            ),
            "academic_vocabulary": (
                "The submission uses generally appropriate "
                "academic vocabulary."
            ),
            "repetition": (
                "Some ideas may be expressed repeatedly."
            ),
            "unsupported_claims": [],
            "overall_writing_quality": (
                "The submission demonstrates a satisfactory "
                "level of academic writing."
            ),
            "improvement_suggestions": [
                "Strengthen transitions between ideas.",
                "Improve sentence-level clarity.",
                "Use more precise academic language."
            ]
        },

        "strengths": [
            "The topic is clearly identified.",
            "The discussion contains relevant ideas.",
            "The paper follows a recognizable academic structure.",
            "The paper demonstrates an understanding of the topic."
        ],

        "weaknesses": [
            "Some arguments require deeper analysis.",
            "Some sections need stronger supporting evidence.",
            "Citation formatting needs greater consistency.",
            "Some sentences require grammatical improvement."
        ],

        "feedback": (
            "The paper demonstrates a satisfactory understanding "
            "of the selected topic and meets several of the "
            "assessment criteria. The strongest areas are the "
            "relevance of the discussion and the overall structure. "
            "Further improvement is recommended in the areas of "
            "critical analysis, supporting evidence, citation "
            "consistency, and sentence-level clarity."
        ),

        "demo_mode": True,

        "assessment_source": "Demo Assessment"
    }


# ============================================================
# MAIN AI ASSESSMENT FUNCTION
# ============================================================

def assess_submission(
    submission_text,
    marking_guide_text,
    document_type
):

    # ========================================================
    # BUILD PROMPT
    # ========================================================

    try:

        prompt = build_assessment_prompt(

            assignment_text=submission_text,

            marking_guide_text=marking_guide_text,

            document_type=document_type
        )

    except Exception as error:

        logger.exception(
            "Failed to build AI assessment prompt."
        )

        raise AIAssessmentError(
            f"Unable to prepare the AI assessment: {error}"
        ) from error


    # ========================================================
    # 1. TRY DEEPSEEK FIRST
    # ========================================================

    try:

        logger.info(
            "Attempting AI assessment using DeepSeek."
        )

        result = assess_with_deepseek(
            prompt
        )

        logger.info(
            "DeepSeek assessment completed successfully."
        )

        return clean_json_response(
            result
        )

    except Exception as deepseek_error:

        logger.warning(
            "DeepSeek assessment failed: %s",
            deepseek_error
        )


    # ========================================================
    # 2. TRY MISTRAL
    # ========================================================

    try:

        logger.info(
            "DeepSeek failed. Attempting Mistral backup."
        )

        result = assess_with_mistral(
            prompt
        )

        logger.info(
            "Mistral backup assessment completed successfully."
        )

        return clean_json_response(
            result
        )

    except Exception as mistral_error:

        logger.error(
            "Mistral backup assessment failed: %s",
            mistral_error
        )


    # ========================================================
    # 3. USE DEMO ASSESSMENT
    # ========================================================

    logger.warning(
        "Live AI services unavailable. "
        "Using demonstration assessment."
    )

    return get_demo_assessment()