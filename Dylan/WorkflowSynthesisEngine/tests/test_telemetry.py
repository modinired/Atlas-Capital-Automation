
from cesar_src.telemetry.ledger import TelemetryLedger

def test_telemetry_log_and_summarize(tmp_path):
    db = tmp_path / "telemetry.db"
    led = TelemetryLedger(str(db))
    led.log_interaction(agent="extractor", role="system", inputs={"x":1}, outputs={"y":2}, meta={"m":3})
    summary = led.summarize()
    assert summary["count"] >= 1
    assert any(ev["agent"] == "extractor" for ev in summary["events"])
