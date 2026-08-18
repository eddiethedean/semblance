from semblance_foundry.ids import make_rid


def test_rid_is_stable() -> None:
    a = make_rid("ontology", "acme", seed=42)
    b = make_rid("ontology", "acme", seed=42)
    assert a == b
    assert a.startswith("ri.ontology.main.ontology.")
    assert a != make_rid("ontology", "acme", seed=7)


def test_rid_differs_by_identity() -> None:
    assert make_rid("objectType", "acme:Employee", 42) != make_rid(
        "objectType", "acme:Office", 42
    )
