# test_article_guardrails.py
from tools.postprocess import enforce_rules

def test_transfer_maps_to_gdpr_46():
    data = {"violations":[
        {"law":"GDPR","article":"42","title":"Transfers", "reason":"transfer outside EU"},
    ], "citations":[]}
    out, _ = enforce_rules(data)
    v = out["violations"][0]
    assert "46" in v["article"]
    assert v.get("autocorrected_from") == "42"

def test_conformity_maps_to_ai_act_43_single():
    data = {"violations":[
        {"law":"AI Act","article":"41","title":"Conformity assessment", "reason":"assessment"},
        {"law":"AI Act","article":"43","title":"Conformity assessment", "reason":"duplicate"},
    ], "citations":[]}
    out, _ = enforce_rules(data)
    arts = [vi["article"] for vi in out["violations"]]
    assert any("43" in a for a in arts)
