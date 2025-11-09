"""Conversational layer test framework.

This package provides a modular LLM-as-judge test framework for evaluating
GTD (Getting Things Done) conversational assistant behavior.

Components:
- runner: Test orchestration and execution
- judge: LLM-as-judge evaluation system
- interrogation: Post-test questioning
- fixtures: Graph setup and cleanup
- user_proxy: Multi-turn conversation simulation
- results_db: SQLite persistence for test results
- retry: Exponential backoff retry logic
- errors: Error handling utilities
- logging_config: Structured logging setup
- cli: Command-line interface
- config: Configuration management
"""

__version__ = "2.0.0"
