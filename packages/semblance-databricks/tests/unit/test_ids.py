from semblance_databricks.ids import make_id


def test_id_is_stable() -> None:
    a = make_id("cluster", "ingest", seed=42)
    b = make_id("cluster", "ingest", seed=42)
    assert a == b
    assert a.startswith("0101-")
    assert a != make_id("cluster", "ingest", seed=7)


def test_id_differs_by_kind() -> None:
    assert make_id("job", "nightly", 42) != make_id("run", "nightly", 42)
