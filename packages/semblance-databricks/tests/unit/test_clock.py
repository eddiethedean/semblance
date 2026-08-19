from semblance_databricks.state import DatabricksState


def test_cluster_pending_to_running() -> None:
    state = DatabricksState(seed=42)
    rec = state.add_cluster("c", state="PENDING", ticks_remaining=1)
    assert rec.state == "PENDING"
    state.tick()
    assert rec.state == "RUNNING"


def test_cluster_startup_error() -> None:
    state = DatabricksState(seed=42)
    rec = state.add_cluster("c", state="PENDING", ticks_remaining=1, fail_after=True)
    state.tick()
    assert rec.state == "ERROR"


def test_run_cancel() -> None:
    from semblance_databricks.state import RunRecord

    state = DatabricksState(seed=42)
    run = RunRecord(
        run_id="1",
        job_id=None,
        run_name="x",
        life_cycle_state="RUNNING",
        canceling=True,
    )
    run.life_cycle_state = "TERMINATING"
    state.runs["1"] = run
    state.tick()
    assert run.life_cycle_state == "TERMINATED"
    assert run.result_state == "CANCELED"
