"""Margin intelligence module for SPAN analysis and delta narratives."""

from .span_parser import SPANParser, MarginComponents
from .delta_explainer import DeltaExplainer, MarginDelta, ChangeType

__all__ = ["SPANParser", "MarginComponents", "DeltaExplainer", "MarginDelta", "ChangeType"]
