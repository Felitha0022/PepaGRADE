import json
import os
import logging

from dotenv import load_dotenv
from google import genai
from mistralai.client import Mistral

from .prompt_builder import build_assessment_prompt


load_dotenv()

logger = logging.getLogger(__name__)


class AIAssessmentError(Exception):
    """Raised when AI assessment cannot be completed."""
    pass


def clean_json_response(result):
    """
    Clean and validate the AI response.

    The AI should return JSON, but this function also handles
    Markdown code fences in case the model adds them.
    """

    # Already a Python dictionary
    if isinstance(result, dict):
        data = result

    # Convert string response into a dictionary
    elif isinstance(result, str):
        text = result.strip()

        # Remove Markdown code fences
        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

            # Remove "json" if it appears immediately after the fence
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            data = json.loads(text)

        except json.JSONDecodeError as exc:
            logger.error("AI returned invalid JSON: %s", text[:2000])
            raise ValueError("AI returned invalid JSON.") from exc

    else:
        raise ValueError(
            f"Unsupported AI response type: {type(result).__name__}"
        )

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object.")

    if "criterion_scores" not in data:
        raise ValueError(
            "AI response does not contain 'criterion_scores'."
        )

    if not isinstance(data["criterion_scores"], dict):
        raise ValueError(
            "'criterion_scores' must be a JSON object."
        )

    return data


# ============================================================
# GEMINI - PRIMARY AI
# ============================================================

def assess_with_gemini(prompt):
    """
    Assess the student's paper using Google Gemini.

    Gemini is the primary AI provider for PepaGRADE.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )

    result = response.text

    logger.info(
        "Gemini assessment response received."
    )

    return clean_json_response(result)


# ============================================================
# MISTRAL - BACKUP AI
# ============================================================

def assess_with_mistral(prompt):
    """
    Assess the student's paper using Mistral.

    Mistral is used only if Gemini fails.
    """

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError(
            "MISTRAL_API_KEY was not found."
        )

    client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an academic writing assessment assistant. "
                    "Return ONLY valid JSON. "
                    "Do not use Markdown code fences."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    message = response.choices[0].message
    result = message.content

    logger.info(
        "Mistral backup assessment response received."
    )

    return clean_json_response(result)


# ============================================================
# DEMO FALLBACK
# ============================================================

def get_demo_assessment():
    """
    Emergency fallback assessment.

    This is only used when both Gemini and Mistral are unavailable.

    It allows the application to continue functioning during
    development/demo situations.
    """

    return {
        "criterion_scores": {
            "Content and Relevance": {
                "score": 18,
                "max_score": 25,
                "performance_level": "Good",
                "rubric_requirement": (
                    "The submission should address the requirements "
                    "of the marking guide."
                ),
                "evidence": (
                    "The submission addresses the main topic "
                    "but some areas require further development."
                ),
                "feedback": (
                    "Develop the content further and provide stronger "
                    "supporting evidence."
                ),
                "weak_area": True,
                "lecturer_review": (
                    "Review whether the discussion sufficiently "
                    "addresses the requirements of this criterion."
                ),
            },
            "Evidence and Analysis": {
                "score": 14,
                "max_score": 20,
                "performance_level": "Good",
                "rubric_requirement": (
                    "The submission should provide relevant evidence "
                    "and demonstrate analysis."
                ),
                "evidence": (
                    "Some evidence and analysis are present, "
                    "but deeper analysis is needed."
                ),
                "feedback": (
                    "Strengthen the analysis and connect evidence "
                    "more clearly to the discussion."
                ),
                "weak_area": True,
                "lecturer_review": (
                    "Review the quality and relevance of supporting evidence."
                ),
            },
            "Organization and Structure": {
                "score": 16,
                "max_score": 20,
                "performance_level": "Very Good",
                "rubric_requirement": (
                    "The submission should be logically organized "
                    "and clearly structured."
                ),
                "evidence": (
                    "The paper follows a generally logical structure "
                    "with some areas that could be improved."
                ),
                "feedback": (
                    "Improve transitions between sections "
                    "and maintain consistent organization."
                ),
                "weak_area": False,
                "lecturer_review": (
                    "Review whether all sections follow the required structure."
                ),
            },
            "Academic Writing": {
                "score": 15,
                "max_score": 20,
                "performance_level": "Very Good",
                "rubric_requirement": (
                    "The submission should use clear, appropriate "
                    "academic language."
                ),
                "evidence": (
                    "Academic language is generally appropriate "
                    "with some grammatical and clarity issues."
                ),
                "feedback": (
                    "Proofread the paper and improve sentence clarity."
                ),
                "weak_area": False,
                "lecturer_review": (
                    "Review grammar, sentence structure, and academic tone."
                ),
            },
            "Referencing": {
                "score": 8,
                "max_score": 15,
                "performance_level": "Satisfactory",
                "rubric_requirement": (
                    "Sources should be appropriately cited and referenced."
                ),
                "evidence": (
                    "Some sources are referenced, but consistency "
                    "and completeness need improvement."
                ),
                "feedback": (
                    "Improve citation consistency and ensure all "
                    "sources are properly referenced."
                ),
                "weak_area": True,
                "lecturer_review": (
                    "Review citations and references against the "
                    "required referencing style."
                ),
            },
        },

        "citation_analysis": {
            "citation_count": 0,
            "matched_references": 0,
            "unmatched_citations": 0,
            "uncited_references": 0,
            "observations": (
                "Citation analysis could not be completed because "
                "the primary AI service was unavailable."
            ),
        },

        "reference_analysis": {
            "reference_count": 0,
            "quality": "Not assessed",
            "observations": (
                "Reference analysis could not be completed because "
                "the primary AI service was unavailable."
            ),
        },

        "grammar_analysis": {
            "errors_found": 0,
            "severity": "Not assessed",
            "observations": (
                "Grammar analysis could not be completed because "
                "the primary AI service was unavailable."
            ),
        },

        "academic_writing_analysis": {
            "clarity": "Not assessed",
            "coherence": "Not assessed",
            "academic_tone": "Not assessed",
            "observations": (
                "Academic writing analysis could not be completed "
                "because the AI service was unavailable."
            ),
        },

        "strengths": [
            "The submission addresses the main topic.",
            "The overall structure is understandable.",
            "The paper demonstrates an attempt to use academic writing."
        ],

        "weaknesses": [
            "Some areas require deeper analysis.",
            "Referencing needs improvement.",
            "Some sections require stronger supporting evidence."
        ],

        "overall_feedback": (
            "The submission demonstrates an understanding of the topic, "
            "but several areas require further development. The lecturer "
            "should review the identified weak areas and confirm the "
            "final assessment."
        ),

        "grade": "B",

        "demo_mode": True,

        "assessment_source": "Demo Assessment",
    }


# ============================================================
# MAIN ASSESSMENT FUNCTION
# ============================================================

def assess_submission(
    submission_text,
    marking_guide_text,
    document_type=None,
):
    """
    Assess a student's academic submission.

    AI priority:

        1. Gemini 3.8 Flash
        2. Mistral Small
        3. Demo fallback

    The marking guide is dynamically supplied by the lecturer.
    PepaGRADE does not use a fixed marking rubric.
    """

    if not submission_text:
        raise AIAssessmentError(
            "The student submission is empty."
        )

    if not marking_guide_text:
        raise AIAssessmentError(
            "The marking guide is empty."
        )

    # --------------------------------------------------------
    # BUILD DYNAMIC ASSESSMENT PROMPT
    # --------------------------------------------------------

    prompt = build_assessment_prompt(
        submission_text=submission_text,
        marking_guide_text=marking_guide_text,
        document_type=document_type,
    )

    # --------------------------------------------------------
    # 1. TRY GEMINI FIRST
    # --------------------------------------------------------

    try:
        logger.info(
            "Starting AI assessment using Gemini 3.8 Flash."
        )

        result = assess_with_gemini(prompt)

        result["demo_mode"] = False
        result["assessment_source"] = "Gemini 3.8 Flash"

        logger.info(
            "Gemini assessment completed successfully."
        )

        return result

    except Exception as exc:
        logger.exception(
            "Gemini assessment failed: %s",
            exc,
        )

    # --------------------------------------------------------
    # 2. TRY MISTRAL BACKUP
    # --------------------------------------------------------

    try:
        logger.info(
            "Starting backup AI assessment using Mistral."
        )

        result = assess_with_mistral(prompt)

        result["demo_mode"] = False
        result["assessment_source"] = "Mistral"

        logger.info(
            "Mistral backup assessment completed successfully."
        )

        return result

    except Exception as exc:
        logger.exception(
            "Mistral backup assessment failed: %s",
            exc,
        )

    # --------------------------------------------------------
    # 3. FINAL DEMO FALLBACK
    # --------------------------------------------------------

    logger.warning(
        "Gemini and Mistral were unavailable. "
        "Using demo assessment fallback."
    )

    return get_demo_assessment()