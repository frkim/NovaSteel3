from knowledge_orchestrator import run_evaluation


def test_evaluation_all_pass(fixtures_dir):
    report = run_evaluation(fixtures_dir)
    failed = [r for r in report.results if not r.passed]
    assert report.all_passed(), f"failing cases: {[(r.name, r.detail) for r in failed]}"
    assert report.total >= 10
    assert report.pass_rate == 1.0


def test_evaluation_report_serialises(fixtures_dir):
    report = run_evaluation(fixtures_dir)
    d = report.to_dict()
    assert d["passed"] == d["total"]
    assert "results" in d and len(d["results"]) == report.total


def test_evaluation_covers_injection_and_grounding(fixtures_dir):
    report = run_evaluation(fixtures_dir)
    kinds = {r.kind for r in report.results}
    assert "injection" in kinds
    assert "grounding" in kinds
    assert "safe-prompt" in kinds
