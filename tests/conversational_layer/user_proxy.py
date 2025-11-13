"""User-proxy for multi-turn conversational tests.

Simulates user responses in conversations where the assistant needs clarification.
Validates that MCP calls were made before asking questions.
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .errors import handle_subprocess_error
from .fixtures import parse_payload, extract_text
from .logging_config import get_logger


CLAUDE_CMD = "claude"


@dataclass
class ConversationalConfig:
    """Configuration for a conversational test.

    Attributes:
        enabled: Whether this test uses conversational mode
        max_turns: Maximum conversation turns (default: 3)
        user_responses: List of scripted user responses (DEPRECATED - use LLM mode)
        validate_mcp_before_ask: Verify MCP was called before asking
        require_search_first: Require search/query before asking clarification

        # LLM User-Proxy Config (new)
        use_llm_user: Use LLM to generate natural user responses (default: True)
        user_proxy_model: Model for LLM user-proxy (default: Haiku 4.5)
        llm_user_temperature: Temperature for user-proxy LLM (default: 0.7)
        goal_summary: Brief description of user's goal
        success_criteria: List of success criteria for the test
    """
    enabled: bool = False
    max_turns: int = 3
    user_responses: List[str] = field(default_factory=list)  # DEPRECATED
    validate_mcp_before_ask: bool = True
    require_search_first: bool = True

    # LLM user-proxy config
    use_llm_user: bool = True
    user_proxy_model: str = "claude-sonnet-4-5-20250929"
    llm_user_temperature: float = 0.7
    goal_summary: str = ""
    success_criteria: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> 'ConversationalConfig':
        """Create from test case dictionary.

        Args:
            data: Dictionary from test case 'conversational' field

        Returns:
            ConversationalConfig instance
        """
        if not data:
            return cls(enabled=False)

        return cls(
            enabled=data.get("enabled", False),
            max_turns=data.get("max_turns", 3),
            user_responses=data.get("user_responses", []),  # DEPRECATED
            validate_mcp_before_ask=data.get("validate_mcp_before_ask", True),
            require_search_first=data.get("require_search_first", True),
            use_llm_user=data.get("use_llm_user", True),
            user_proxy_model=data.get("user_proxy_model", "claude-sonnet-4-5-20250929"),
            llm_user_temperature=data.get("llm_user_temperature", 0.7),
            goal_summary=data.get("goal_summary", ""),
            success_criteria=data.get("success_criteria", [])
        )


@dataclass
class ConversationTurn:
    """Single turn in a conversation.

    Attributes:
        turn_number: Which turn (1-based)
        user_message: User's message
        assistant_response: Assistant's response text
        full_output: Full JSON output with MCP calls
        session_id: Session ID for resumption
        mcp_calls_made: Whether assistant made MCP calls
        duration: Turn duration in seconds
    """
    turn_number: int
    user_message: str
    assistant_response: str = ""
    full_output: str = ""
    session_id: str = ""
    mcp_calls_made: bool = False
    duration: float = 0.0


@dataclass
class ConversationResult:
    """Result from a multi-turn conversation.

    Attributes:
        success: Whether conversation completed successfully
        turns: List of conversation turns
        final_response: Final assistant response
        full_transcript: Complete conversation transcript
        session_id: Final session ID
        total_duration: Total conversation duration
        reason: Error reason if failed
    """
    success: bool
    turns: List[ConversationTurn] = field(default_factory=list)
    final_response: str = ""
    full_transcript: str = ""
    session_id: str = ""
    total_duration: float = 0.0
    reason: str = ""


class UserProxy:
    """Simulates user responses in multi-turn conversations.

    Handles:
    - Running initial prompt
    - Resuming sessions with user responses
    - Validating MCP usage before asking questions
    - Building conversation transcripts
    """

    def __init__(self, config: Config):
        """Initialize user proxy.

        Args:
            config: Test configuration
        """
        self.config = config
        self.logger = get_logger()

    def _has_mcp_calls(self, payload: Dict[str, Any]) -> bool:
        """Check if response contains MCP tool calls.

        Args:
            payload: Parsed JSON payload from Claude CLI

        Returns:
            True if MCP calls were made
        """
        if not isinstance(payload, dict):
            return False

        # Check for tool uses in messages
        messages = payload.get("messages", [])
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            content = msg.get("content", [])
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue

                # Look for tool_use blocks
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    # MCP tools start with mcp__
                    if tool_name.startswith("mcp__"):
                        return True

        return False

    def _has_search_calls(self, payload: Dict[str, Any]) -> bool:
        """Check if response contains search/query MCP calls.

        Args:
            payload: Parsed JSON payload

        Returns:
            True if search/query calls were made
        """
        if not isinstance(payload, dict):
            return False

        search_tools = [
            "mcp__gtd-graph-memory__search_content",
            "mcp__gtd-graph-memory__query_nodes",
            "mcp__gtd-graph-memory__get_connected_nodes"
        ]

        messages = payload.get("messages", [])
        for msg in messages:
            if not isinstance(msg, dict):
                continue

            content = msg.get("content", [])
            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue

                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    if tool_name in search_tools:
                        return True

        return False

    def _run_claude_turn(
        self,
        user_message: str,
        session_id: Optional[str],
        append_prompts: List[str]
    ) -> subprocess.CompletedProcess[str]:
        """Execute Claude CLI for a single conversation turn.

        Args:
            user_message: User's message
            session_id: Optional session ID to resume
            append_prompts: System prompt additions

        Returns:
            CompletedProcess with stdout/stderr
        """
        args = [CLAUDE_CMD]
        if self.config.mcp_config_path:
            args += ["--mcp-config", str(self.config.mcp_config_path)]

        args += [
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json"
        ]

        # System prompt only on first turn
        if not session_id:
            if self.config.system_prompt_path and self.config.system_prompt_path.exists():
                args += ["--system-prompt", str(self.config.system_prompt_path)]

            for append_content in append_prompts:
                if append_content.strip():
                    args += ["--append-system-prompt", append_content]
        else:
            # Resume session
            args += ["--resume", session_id]

        args.append(user_message)

        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=self.config.assistant_timeout,
            check=False,
        )

    def _execute_turn(
        self,
        turn_number: int,
        user_message: str,
        session_id: Optional[str],
        append_prompts: List[str],
        conv_config: ConversationalConfig
    ) -> ConversationTurn:
        """Execute a single conversation turn.

        Args:
            turn_number: Turn number (1-based)
            user_message: User's message
            session_id: Optional session ID to resume
            append_prompts: System prompt additions
            conv_config: Conversational configuration

        Returns:
            ConversationTurn with results

        Raises:
            Exception: If turn fails
        """
        start_time = time.time()

        try:
            result = self._run_claude_turn(user_message, session_id, append_prompts)

            if result.returncode != 0:
                reason = result.stderr.strip() or "CLI error"
                raise Exception(f"Turn {turn_number} CLI error: {reason}")

            payload = parse_payload(result.stdout)
            if payload is None:
                raise Exception(f"Turn {turn_number} returned non-JSON output")

            new_session_id = payload.get("session_id", session_id or "")
            assistant_text = extract_text(payload).strip()
            mcp_calls_made = self._has_mcp_calls(payload)

            # Log MCP call status for all turns (for debugging)
            # Note: We no longer fail tests here - the judge evaluates effectiveness
            # with the full transcript (including MCP calls) and makes the determination
            if not mcp_calls_made:
                self.logger.debug(
                    f"Turn {turn_number}: No MCP calls detected in this turn"
                )
            else:
                self.logger.debug(
                    f"Turn {turn_number}: MCP calls detected"
                )

            duration = time.time() - start_time

            return ConversationTurn(
                turn_number=turn_number,
                user_message=user_message,
                assistant_response=assistant_text,
                full_output=result.stdout.strip(),
                session_id=new_session_id,
                mcp_calls_made=mcp_calls_made,
                duration=duration
            )

        except subprocess.TimeoutExpired:
            raise Exception(f"Turn {turn_number} timeout after {self.config.assistant_timeout}s")
        except Exception as e:
            if "CLI error" in str(e) or "non-JSON" in str(e) or "timeout" in str(e):
                raise
            error_dict = handle_subprocess_error(e, f"turn_{turn_number}")
            raise Exception(error_dict.get("reason", str(e)))

    def run_conversation(
        self,
        initial_prompt: str,
        conv_config: ConversationalConfig,
        append_prompts: List[str],
        case_name: str = ""
    ) -> ConversationResult:
        """Run multi-turn conversation with scripted user responses.

        Args:
            initial_prompt: Initial user prompt
            conv_config: Conversational configuration
            append_prompts: System prompt additions
            case_name: Test case name (for logging)

        Returns:
            ConversationResult with full transcript
        """
        self.logger.info(
            f"Starting conversation for {case_name} "
            f"(max {conv_config.max_turns} turns, "
            f"{len(conv_config.user_responses)} scripted responses)"
        )

        start_time = time.time()
        turns = []
        session_id = None

        try:
            # Turn 1: Initial prompt
            turn1 = self._execute_turn(
                turn_number=1,
                user_message=initial_prompt,
                session_id=None,
                append_prompts=append_prompts,
                conv_config=conv_config
            )
            turns.append(turn1)
            session_id = turn1.session_id

            self.logger.debug(
                f"Turn 1 complete: {len(turn1.assistant_response)} chars, "
                f"MCP calls: {turn1.mcp_calls_made}"
            )

            # Additional turns with user responses
            for i, user_response in enumerate(conv_config.user_responses, start=2):
                if i > conv_config.max_turns:
                    self.logger.warning(
                        f"Reached max turns ({conv_config.max_turns}), "
                        f"stopping with {len(conv_config.user_responses) - i + 2} responses unused"
                    )
                    break

                turn = self._execute_turn(
                    turn_number=i,
                    user_message=user_response,
                    session_id=session_id,
                    append_prompts=[],  # Only on first turn
                    conv_config=conv_config
                )
                turns.append(turn)
                session_id = turn.session_id

                self.logger.debug(
                    f"Turn {i} complete: {len(turn.assistant_response)} chars, "
                    f"MCP calls: {turn.mcp_calls_made}"
                )

            # Build full transcript
            transcript_parts = []
            for turn in turns:
                transcript_parts.append(f"[Turn {turn.turn_number} - User]")
                transcript_parts.append(turn.user_message)
                transcript_parts.append(f"\n[Turn {turn.turn_number} - Assistant]")
                # Use full_output to include MCP tool calls, not just extracted text
                transcript_parts.append(turn.full_output)
                transcript_parts.append("")

            full_transcript = "\n".join(transcript_parts)

            # Final response is last turn's assistant response
            final_response = turns[-1].assistant_response if turns else ""

            total_duration = time.time() - start_time

            self.logger.info(
                f"Conversation complete for {case_name}: "
                f"{len(turns)} turns, {total_duration:.1f}s"
            )

            return ConversationResult(
                success=True,
                turns=turns,
                final_response=final_response,
                full_transcript=full_transcript,
                session_id=session_id or "",
                total_duration=total_duration,
                reason=""
            )

        except Exception as e:
            total_duration = time.time() - start_time
            reason = str(e)

            self.logger.error(
                f"Conversation failed for {case_name}: {reason}",
                exc_info=True
            )

            return ConversationResult(
                success=False,
                turns=turns,
                final_response="",
                full_transcript="",
                session_id=session_id or "",
                total_duration=total_duration,
                reason=reason
            )


class LLMUserProxy(UserProxy):
    """LLM-powered user-proxy that responds naturally to assistant questions.

    Uses a separate Claude instance (typically Haiku) to role-play a user
    who understands the test scenario and responds naturally to whatever
    the assistant asks, rather than using scripted responses.
    """

    def _build_user_proxy_system_prompt(
        self,
        case: Dict[str, Any],
        conv_config: ConversationalConfig,
        conversation_history: List[ConversationTurn]
    ) -> str:
        """Build system prompt for user-proxy LLM.

        Args:
            case: Test case dictionary with scenario/goals
            conv_config: Conversational configuration
            conversation_history: Previous turns in conversation

        Returns:
            System prompt string for user-proxy LLM
        """
        # Extract test context
        category = case.get("category", "Unknown")
        expected_behavior = case.get("expected_behavior", "")
        judge_scenario = case.get("judge_scenario", "")
        original_prompt = case.get("prompt", "")

        # Format success criteria
        criteria_list = "\n".join(f"- {c}" for c in conv_config.success_criteria) if conv_config.success_criteria else "- Complete the requested task"

        # Build conversation history for context
        history_text = ""
        if conversation_history:
            history_parts = []
            for turn in conversation_history:
                history_parts.append(f"[Turn {turn.turn_number} - You said]")
                history_parts.append(turn.user_message)
                history_parts.append(f"\n[Turn {turn.turn_number} - Assistant responded]")
                history_parts.append(turn.assistant_response[:500] + ("..." if len(turn.assistant_response) > 500 else ""))
                history_parts.append("")
            history_text = "\n".join(history_parts)

        # Goal summary
        goal = conv_config.goal_summary if conv_config.goal_summary else expected_behavior

        prompt = f"""# You are Playing the Role of a User

You are roleplaying a **real user** who needs help from a GTD (Getting Things Done) productivity assistant.

**What is being tested**: The GTD assistant's ability to understand and complete your request.
**Your role**: Act as a natural, realistic user trying to get your task done.
**Your goal**: Work with the assistant to accomplish what you asked for, ideally within {conv_config.max_turns} conversational turns.

## Your Scenario

**Category**: {category}
**What you want to accomplish**: {goal}
**How this should resolve**: {expected_behavior}

## Your Original Request

You originally said to the assistant: "{original_prompt}"

The assistant is now responding or asking you questions. Your job is to answer naturally and help move toward completing your goal.

## What Success Looks Like for You

By the end of this conversation, you should have:
{criteria_list}

## How to Respond

1. **Be Natural and Realistic**
   - Respond like a real person would, not a script
   - Use conversational language
   - Be specific when you can, vague when that's realistic
   - Show natural human uncertainty or clarification needs

2. **Stay Focused on Your Goal**
   - Remember what you originally asked for
   - Help the assistant achieve: {goal}
   - If the assistant's questions are helping, answer them honestly
   - If the assistant seems confused, try to clarify

3. **Recognize When Done**
   - If the assistant has successfully completed your request, acknowledge it
   - Say something like "That looks good, thanks!" or "Perfect, that's what I needed"
   - Don't introduce new requirements once your goal is achieved

4. **Avoid Common Pitfalls**
   - Don't introduce unrelated requirements
   - Don't contradict what you said before
   - Don't be overly pedantic or difficult
   - Stay in character as a busy professional, not a tester

5. **Provide Context When Asked**
   - If asked about priority, deadlines, or dependencies, give realistic details
   - If you don't know something, it's okay to say "I'm not sure" or "whatever makes sense"
   - Be helpful, not obstructive

## Context from Previous Turns

{history_text if history_text else "This is the first turn after your initial request."}

## Example Responses

**Good responses:**
- "Yes, I need those three sub-tasks done in order - metrics first, then the narrative, then slides."
- "Oh, I didn't realize I already had a similar task. Let's update that one instead."
- "That works! Thanks for setting that up."
- "The finalize task is different from the review task - they're for different contracts."

**Avoid responses like:**
- "Actually, now I also want X, Y, and Z..." (introducing new requirements)
- "No, that's wrong, I said..." (unless assistant truly misunderstood)
- "Can you also..." (piling on unrelated tasks)

## Important Guidelines

- Respond ONLY as the user, never break character
- Keep responses concise (1-3 sentences usually is plenty)
- Be honest about what you know and don't know
- If the assistant has met your goal, say so and end positively
- Your responses should feel natural, not robotic or test-like

Now respond naturally to whatever the assistant just said or asked."""

        return prompt

    def _call_user_proxy_llm(
        self,
        assistant_message: str,
        case: Dict[str, Any],
        conv_config: ConversationalConfig,
        conversation_history: List[ConversationTurn]
    ) -> str:
        """Call LLM user-proxy to generate natural response.

        Args:
            assistant_message: What the assistant just said/asked
            case: Test case dictionary
            conv_config: Conversational configuration
            conversation_history: Previous conversation turns

        Returns:
            Natural user response from LLM
        """
        # Build system prompt
        system_prompt = self._build_user_proxy_system_prompt(
            case, conv_config, conversation_history
        )

        # Call Claude with user-proxy system prompt
        args = [
            CLAUDE_CMD,
            "--model", conv_config.user_proxy_model,
            "--dangerously-skip-permissions",
            "--print",
            "--output-format", "json",
            "--append-system-prompt", system_prompt
        ]
        # Note: --temperature flag not supported by Claude CLI

        # User message is the assistant's question/statement
        user_message = f"The assistant just said:\n\n{assistant_message}\n\nHow do you respond?"

        args.append(user_message)

        # Build subprocess call with system prompt
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120.0,  # Increased timeout for LLM user proxy responses
            check=False
        )

        if result.returncode != 0:
            self.logger.error(f"User-proxy LLM failed: {result.stderr}")
            # Fallback: simple confirmation
            return "Yes, that sounds good."

        # Parse response
        try:
            payload = parse_payload(result.stdout)
            if payload:
                response_text = extract_text(payload).strip()
                if response_text:
                    return response_text
        except Exception as e:
            self.logger.error(f"Failed to parse user-proxy response: {e}")

        # Fallback
        return "Yes, please proceed with that."

    def run_conversation(
        self,
        initial_prompt: str,
        conv_config: ConversationalConfig,
        append_prompts: List[str],
        case_name: str = "",
        case: Optional[Dict[str, Any]] = None
    ) -> ConversationResult:
        """Run multi-turn conversation with LLM-powered user responses.

        Args:
            initial_prompt: Initial user prompt
            conv_config: Conversational configuration
            append_prompts: System prompt additions
            case_name: Test case name (for logging)
            case: Full test case dictionary (needed for context)

        Returns:
            ConversationResult with full transcript
        """
        if case is None:
            self.logger.error("LLMUserProxy requires case dictionary for context")
            return ConversationResult(
                success=False,
                reason="No case dictionary provided to LLMUserProxy"
            )

        # Fall back to scripted mode if disabled
        if not conv_config.use_llm_user and conv_config.user_responses:
            self.logger.info(f"Using scripted responses for {case_name} (LLM mode disabled)")
            return super().run_conversation(initial_prompt, conv_config, append_prompts, case_name)

        self.logger.info(
            f"Starting LLM-powered conversation for {case_name} "
            f"(max {conv_config.max_turns} turns, model: {conv_config.user_proxy_model})"
        )

        start_time = time.time()
        turns = []
        session_id = None

        try:
            # Turn 1: Initial prompt
            turn1 = self._execute_turn(
                turn_number=1,
                user_message=initial_prompt,
                session_id=None,
                append_prompts=append_prompts,
                conv_config=conv_config
            )
            turns.append(turn1)
            session_id = turn1.session_id

            self.logger.debug(
                f"Turn 1 complete: {len(turn1.assistant_response)} chars, "
                f"MCP calls: {turn1.mcp_calls_made}"
            )

            # Additional turns with LLM-generated responses
            for turn_num in range(2, conv_config.max_turns + 1):
                # Generate natural user response
                user_response = self._call_user_proxy_llm(
                    assistant_message=turns[-1].assistant_response,
                    case=case,
                    conv_config=conv_config,
                    conversation_history=turns
                )

                self.logger.debug(f"User-proxy LLM generated response: {user_response[:100]}...")

                # Execute turn with LLM response
                turn = self._execute_turn(
                    turn_number=turn_num,
                    user_message=user_response,
                    session_id=session_id,
                    append_prompts=[],  # Only on first turn
                    conv_config=conv_config
                )
                turns.append(turn)
                session_id = turn.session_id

                self.logger.debug(
                    f"Turn {turn_num} complete: {len(turn.assistant_response)} chars, "
                    f"MCP calls: {turn.mcp_calls_made}"
                )

                # Check if conversation is complete (user satisfied)
                if any(phrase in user_response.lower() for phrase in [
                    "thanks", "perfect", "looks good", "that works",
                    "appreciate it", "all set", "that's it"
                ]):
                    self.logger.info(f"User appears satisfied, ending conversation at turn {turn_num}")
                    break

            # Build full transcript
            transcript_parts = []
            for turn in turns:
                transcript_parts.append(f"[Turn {turn.turn_number} - User]")
                transcript_parts.append(turn.user_message)
                transcript_parts.append(f"\n[Turn {turn.turn_number} - Assistant]")
                # Use full_output to include MCP tool calls, not just extracted text
                transcript_parts.append(turn.full_output)
                transcript_parts.append("")

            full_transcript = "\n".join(transcript_parts)

            # Final response is last turn's assistant response
            final_response = turns[-1].assistant_response if turns else ""

            total_duration = time.time() - start_time

            self.logger.info(
                f"LLM conversation complete for {case_name}: "
                f"{len(turns)} turns, {total_duration:.1f}s"
            )

            return ConversationResult(
                success=True,
                turns=turns,
                final_response=final_response,
                full_transcript=full_transcript,
                session_id=session_id or "",
                total_duration=total_duration,
                reason=""
            )

        except Exception as e:
            total_duration = time.time() - start_time
            reason = str(e)

            self.logger.error(
                f"LLM conversation failed for {case_name}: {reason}",
                exc_info=True
            )

            return ConversationResult(
                success=False,
                turns=turns,
                final_response="",
                full_transcript="",
                session_id=session_id or "",
                total_duration=total_duration,
                reason=reason
            )


def is_conversational_test(case: Dict[str, Any]) -> bool:
    """Check if test case is conversational.

    Args:
        case: Test case dictionary

    Returns:
        True if conversational test
    """
    conv_data = case.get("conversational")
    if not conv_data:
        return False

    return conv_data.get("enabled", False)


def extract_conversational_config(case: Dict[str, Any]) -> ConversationalConfig:
    """Extract conversational config from test case.

    Args:
        case: Test case dictionary

    Returns:
        ConversationalConfig instance
    """
    return ConversationalConfig.from_dict(case.get("conversational"))


def build_conversation_summary(result: ConversationResult) -> str:
    """Build human-readable conversation summary.

    Args:
        result: Conversation result

    Returns:
        Formatted summary string
    """
    if not result.success:
        return f"Conversation failed: {result.reason}"

    lines = [
        f"Conversation: {len(result.turns)} turns, {result.total_duration:.1f}s",
        ""
    ]

    for turn in result.turns:
        lines.append(f"Turn {turn.turn_number}:")
        lines.append(f"  User: {turn.user_message[:100]}...")
        lines.append(f"  Assistant: {turn.assistant_response[:100]}...")
        lines.append(f"  MCP calls: {turn.mcp_calls_made}")
        lines.append("")

    return "\n".join(lines)
