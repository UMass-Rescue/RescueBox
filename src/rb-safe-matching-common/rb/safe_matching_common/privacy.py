from functools import cache
from typing import Final

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

PII_ENTITIES: Final[list[str]] = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"]
SPACY_MODEL: Final[str] = "en_core_web_lg"


@cache
def _engines() -> tuple[AnalyzerEngine, AnonymizerEngine]:
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
        }
    ).create_engine()
    return AnalyzerEngine(nlp_engine=nlp_engine), AnonymizerEngine()


def redact_text(text: str) -> str:
    analyzer, anonymizer = _engines()
    results = analyzer.analyze(text=text, entities=PII_ENTITIES, language="en")
    redacted = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("redact")},
    ).text
    return " ".join(redacted.split())
