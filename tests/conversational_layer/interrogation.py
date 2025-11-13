"""Interrogation system for post-test questioning.

Provides functions to resume Claude sessions and ask follow-up questions
to understand test failures and successes.
"""

import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .errors import handle_subprocess_error
from .fixtures import parse_payload, extract_text
from .logging_config import get_logger


CLAUDE_CMD = "claude"


# Questions for failed tests
INTERROGATION_FAILURE_QUESTIONS = [
    "Why did you choose that approach to handle the user's request?",
    "The judge indicated your response had issues. Looking back, what were you trying to accomplish and why did you think that approach would work?",
    "Looking at the instructions you were given (system prompt, Claude Skill guidance, test context), was there anything unclear that made this task difficult? What could be written differently to make the right choice more obvious?",
]


# Questions for successful tests
INTERROGATION_SUCCESS_QUESTIONS = [
    textwrap.dedent("""
    Thank you! That was the desired behavior for this test.

    We're evaluating the quality of our instructions to ensure they make the right choices easy and clear. A few quick questions:

    1. Was it clear what you needed to do for this request?
    2. Were there any aspects where you felt uncertain about the right approach?
    3. Could any of the instructions (system prompt, Claude Skill guidance, test context) have been written more clearly or concisely?
    4. Was anything redundant or unnecessarily verbose in the instructions?

    Please be candid - we want to improve the instructions, not just confirm they work.
    """).strip(),
]


@dataclass
class QAPair:
    """Question-answer pair from interrogation.

    Attributes:
        question: Question asked
        answer: Assistant's response
        error: Optional error message if question failed
    """
    question: str
    answer: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "question": self.question,
            "answer": self.answer
        }
        if self.error:
            result["error"] = self.error
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QAPair':
        """Create from dictionary."""
        return cls(
            question=data["question"],
            answer=data["answer"],
            error=data.get("error")
        )


def get_interrogation_questions(passed: bool) -> List[str]:
    """Get appropriate interrogation questions based on test result.

    Args:
        passed: Whether test passed

    Returns:
        List of questions to ask
    """
    if passed:
        return INTERROGATION_SUCCESS_QUESTIONS
    else:
        return INTERROGATION_FAILURE_QUESTIONS


def resume_session_with_question(
    session_id: str,
    question: str,
    config: Config
) -> Dict[str, Any]:
    """Resume Claude session and ask a single question.

    Args:
        session_id: Session ID from original test run
        question: Question to ask
        config: Test configuration

    Returns:
        Dictionary with answer or error info
    """
    logger = get_logger()

    try:
        args = [CLAUDE_CMD]
        if config.mcp_config_path:
            args += ["--mcp-config", str(config.mcp_config_path)]
        args += [
            "--model", "sonnet",
            "--resume", session_id,
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json",
            question
        ]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=config.interrogation_timeout,
            check=False,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "CLI error"
            logger.warning(f"Interrogation CLI error: {error_msg}")
            return {
                "success": False,
                "answer": f"[ERROR: {error_msg}]",
                "error": error_msg
            }

        payload = parse_payload(result.stdout)
        if payload is None:
            logger.warning("Interrogation returned non-JSON output")
            return {
                "success": False,
                "answer": "[ERROR: Non-JSON output]",
                "error": "Non-JSON output"
            }

        answer = extract_text(payload).strip()
        return {
            "success": True,
            "answer": answer,
            "error": None
        }

    except subprocess.TimeoutExpired:
        logger.error(f"Interrogation timeout after {config.interrogation_timeout}s")
        return {
            "success": False,
            "answer": f"[ERROR: Timeout after {config.interrogation_timeout}s]",
            "error": "Timeout"
        }
    except Exception as e:
        error_dict = handle_subprocess_error(e, "resume_session_with_question")
        return {
            "success": False,
            "answer": f"[ERROR: {error_dict['reason'][:200]}]",
            "error": error_dict["reason"]
        }


def interrogate_session(
    session_id: str,
    passed: bool,
    config: Config,
    case_name: str = "",
    verdict: Optional[Dict[str, Any]] = None
) -> List[QAPair]:
    """Resume test session and ask follow-up questions.

    Args:
        session_id: Session ID from the initial test run
        passed: Whether test passed
        config: Test configuration
        case_name: Name of test case (for logging)
        verdict: Optional judge verdict dictionary to include in Q2

    Returns:
        List of Q&A pairs
    """
    logger = get_logger()

    questions = get_interrogation_questions(passed)

    # For Q2 on failed tests, inject judge feedback
    if not passed and verdict and len(questions) >= 2:
        judge_feedback = f"""
The judge indicated your response had issues. Here's what the judge said:

**Judge Verdict:**
- Effective: {'✅' if verdict.get('effective') else '❌'}
- Safe: {'✅' if verdict.get('safe') else '❌'}
- Clear: {'✅' if verdict.get('clear') else '❌'}
- Reasoning: {verdict.get('reasoning', 'No reasoning provided')}

Looking back, what were you trying to accomplish and why did you think that approach would work?
"""
        questions[1] = judge_feedback.strip()

    logger.info(
        f"Interrogating session for {case_name} ({len(questions)} questions)",
        extra={"test_name": case_name}
    )

    qa_pairs = []

    for i, question in enumerate(questions, start=1):
        logger.debug(f"Interrogation question {i}/{len(questions)}")

        result = resume_session_with_question(session_id, question, config)

        qa_pair = QAPair(
            question=question,
            answer=result["answer"],
            error=result.get("error")
        )
        qa_pairs.append(qa_pair)

        # Log if there was an error
        if not result["success"]:
            logger.warning(
                f"Interrogation question {i} failed: {result['error']}",
                extra={"test_name": case_name}
            )

    logger.info(
        f"Interrogation complete: {len(qa_pairs)} Q&A pairs",
        extra={"test_name": case_name}
    )

    return qa_pairs


def format_interrogation_for_display(qa_pairs: List[QAPair], max_length: int = 500) -> str:
    """Format interrogation Q&A pairs for console display.

    Args:
        qa_pairs: List of Q&A pairs
        max_length: Maximum length per answer (truncate if longer)

    Returns:
        Formatted string for display
    """
    lines = []
    for i, qa in enumerate(qa_pairs, 1):
        lines.append(f"\nQ{i}: {qa.question[:200]}")

        answer = qa.answer
        if len(answer) > max_length:
            answer = answer[:max_length] + "..."

        lines.append(f"A{i}: {answer}")

        if qa.error:
            lines.append(f"    [Error: {qa.error}]")

    return "\n".join(lines)


def format_interrogation_for_json(qa_pairs: List[QAPair]) -> List[Dict[str, Any]]:
    """Format interrogation Q&A pairs for JSON serialization.

    Args:
        qa_pairs: List of Q&A pairs

    Returns:
        List of dictionaries
    """
    return [qa.to_dict() for qa in qa_pairs]


def should_interrogate_test(
    passed: bool,
    config: Config
) -> bool:
    """Determine if test should be interrogated based on result and config.

    Args:
        passed: Whether test passed
        config: Test configuration

    Returns:
        True if should interrogate
    """
    return config.should_interrogate(passed)


def extract_uncertainty_mentions(qa_pairs: List[QAPair]) -> List[str]:
    """Extract mentions of uncertainty or confusion from interrogation answers.

    Args:
        qa_pairs: List of Q&A pairs

    Returns:
        List of uncertainty indicators found

    Useful for analyzing instruction quality and identifying areas
    where the system prompt could be clearer.
    """
    uncertainty_keywords = [
        "unclear",
        "uncertain",
        "confus",
        "not sure",
        "didn't know",
        "ambiguous",
        "vague",
        "could be clearer",
        "redundant",
        "verbose",
        "inconsistent",
    ]

    mentions = []

    for qa in qa_pairs:
        answer_lower = qa.answer.lower()
        for keyword in uncertainty_keywords:
            if keyword in answer_lower:
                # Extract sentence containing the keyword
                sentences = qa.answer.split(".")
                for sentence in sentences:
                    if keyword in sentence.lower():
                        mentions.append(sentence.strip())
                        break

    return mentions
