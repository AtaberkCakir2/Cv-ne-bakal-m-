"""CV analizinin AI zinciri (T-057): PDF → maskeleme → çıkarım → eşleştirme → öneri.

from pipeline import AnalysisError, analyze_cv
out = analyze_cv(pdf_bytes, role_id=3, conn=psycopg_conn)
out.result  # contracts/analysis_result.schema.json alanları
"""

from pipeline.analyze import (
    BUDGET_SECONDS,
    MIN_LLM_SECONDS,
    AnalysisError,
    AnalysisOutput,
    analyze_cv,
    guess_lang,
    prompt_version,
)

__all__ = [
    "BUDGET_SECONDS",
    "MIN_LLM_SECONDS",
    "AnalysisError",
    "AnalysisOutput",
    "analyze_cv",
    "guess_lang",
    "prompt_version",
]
