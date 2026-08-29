"""Fixture app for tests."""
from app import util


def run(input_data: str) -> str:
    """Main entry point for the fixture pipeline."""
    return util.transform(input_data)
