# test_postprocess_rules.py
# Test delle regole indipendenti dal PDF (unit)
import pytest
from tools.postprocess import enforce_rules

def _mk_sample(violations, citations, max_citations=None):
    """Crea un payload minimo per postprocess."""
    data = {
        "conclusion": {"risk": "high", "score": 80},
        "violations": violations,
        "citations": citations,
    }
    if max_citations is not None:
        data["config"] = {"max_citations": max_citations}
    return data

def test_multi_hit_same_article_allowed():
    """Lo stesso articolo può comparire più volte per violazioni diverse: non è errore."""
    data_in = _mk_sample(
        violations=[
            {"law": "gdpr", "article": "6", "title": "Lawfulness", "msg": "missing lawful basis"},
            {"law": "gdpr", "article": "6", "title": "Lawfulness", "msg": "consent not explicit"},
        ],
        citations=[
            {"law": "gdpr", "article": "6", "ref": "Art.6(1)"},
            {"law": "gdpr", "article": "6", "ref": "Art.6(1)(a)"},
        ],
    )
    data_out, warnings = enforce_rules(data_in)
    assert len(data_out["violations"]) == 2
    # nessun errore sul “duplice articolo”
    assert not any("duplicate" in w.lower() and "article" in w.lower() for w in warnings)

def test_title_article_incoherence_is_warning_not_error():
    """Se il titolo non combacia con l’articolo, deve uscire un WARNING (non bloccare)."""
    data_in = _mk_sample(
        violations=[{"law": "gdpr", "article": "6", "title": "Purpose limitation", "msg": "..."},],
        citations=[{"law": "gdpr", "article": "6", "ref": "Art.6(1)"}],
    )
    data_out, warnings = enforce_rules(data_in)
    assert len(data_out["violations"]) == 1
    assert warnings, "Atteso almeno un warning su incoerenza titolo/articolo"

def test_max_citations_cap_if_configured():
    """Se configurato, il cap su citazioni deve essere rispettato (taglio non distruttivo)."""
    data_in = _mk_sample(
        violations=[
            {"law": "gdpr", "article": "6", "title": "Lawfulness", "msg": "x"},
            {"law": "gdpr", "article": "5", "title": "Purpose limitation", "msg": "y"},
        ],
        citations=[
            {"law": "gdpr", "article": "6", "ref": "A"},
            {"law": "gdpr", "article": "6", "ref": "B"},
            {"law": "gdpr", "article": "5", "ref": "C"},
            {"law": "gdpr", "article": "5", "ref": "D"},
        ],
        max_citations=3,
    )
    data_out, warnings = enforce_rules(data_in)
    assert len(data_out["citations"]) <= 3, "Cap citazioni non rispettato"
    # Le violazioni restano intatte
    assert len(data_out["violations"]) == 2
