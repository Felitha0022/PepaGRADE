import json

from assessment.services.ai_assessment import assess_submission


assignment_text = """
Artificial intelligence is becoming increasingly important
in higher education. Universities are using AI to support
teaching, learning, research and administration.

AI systems can provide personalized learning experiences
by adapting educational content to individual student needs.
They can also help lecturers analyze student performance
and identify areas where students require additional support.

However, universities must also consider ethical issues
such as academic integrity, privacy and responsible use
of artificial intelligence.
"""


marking_guide_text = """
Introduction and relevance to topic - 10 marks

Understanding of the topic - 20 marks

Analysis and discussion - 30 marks

Use of evidence and references - 20 marks

Conclusion - 10 marks

Academic writing and presentation - 10 marks

Total - 100 marks
"""


result = assess_submission(
    submission_text=assignment_text,
    marking_guide_text=marking_guide_text,
    document_type="Essay"
)


print("\n===== AI ASSESSMENT RESULT =====\n")

print(
    json.dumps(
        result,
        indent=4
    )
)