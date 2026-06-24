"""Compatibility wrapper for the project-level Ableton analyzer."""

from .abelton.project_analyzer import AbletonProjectAnalyzer, analyze_file, main, render_markdown

__all__ = ["AbletonProjectAnalyzer", "analyze_file", "main", "render_markdown"]


if __name__ == "__main__":
    raise SystemExit(main())
