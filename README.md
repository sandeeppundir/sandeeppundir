# Real-time Fraud Management System (FMS)

This project contains a demonstrable real-time Fraud Management System that focuses on replay attack prevention, velocity checks, and dynamic risk profiling powered by AI. The service exposes a FastAPI endpoint that evaluates incoming transactions in milliseconds and explains every decision.

## Features

- **Replay attack prevention** – cryptographic fingerprints of recent transactions ensure duplicates or near-duplicates are blocked instantly.
- **Transaction velocity monitoring** – sliding-window analysis per consumer with configurable risk-based thresholds for counts and cumulative amounts.
- **Dynamic risk profiling** – an Isolation Forest model combined with heuristic rules generates explainable risk scores influenced by the consumer's risk profile.
- **Bot and automation detection** – repetitive transactions with identical amounts/merchants are flagged as potential automation, malware, or bot attacks.
- **REST API** – FastAPI makes it easy to integrate and demonstrate the FMS locally.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs to interact with the API.

## Example usage

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
        "transaction_id": "txn-001",
        "consumer_id": "c-123",
        "merchant_id": "m-456",
        "channel": "web",
        "amount": 950.0,
        "location": "US",
        "risk_profile": "medium"
      }'
```

Sample output:

```json
{
  "transaction_id": "txn-001",
  "decision": "review",
  "risk_score": 0.61,
  "reasons": [
    "IsolationForest flagged the transaction as anomalous compared to learned behavior"
  ],
  "blocked": false
}
```

Replay attacks or suspicious velocity will return a 403 response that includes the reasons for blocking inside the `detail` field.

## Design overview

| Component | Description |
| --- | --- |
| ReplayDetector | Maintains a rolling cache of transaction fingerprints (consumer, merchant, amount, device) and blocks duplicates within the replay window. |
| VelocityChecker | Tracks the frequency and cumulative value of consumer transactions, comparing them to risk-profile thresholds (low/medium/high). It highlights bot-like repetitive behavior. |
| RiskProfiler | Uses an AI Isolation Forest model trained on synthetic benign data to score anomalies. Thresholds are dynamically adjusted by the consumer's risk profile. |
| FraudManager | Orchestrates the above detectors and returns an explainable decision (`approve`, `review`, or `block`). |

## Extending

- Replace the in-memory data stores with Redis or Kafka for distributed deployments.
- Feed the Isolation Forest with production telemetry or swap in a supervised model.
- Push assessments to SIEM/SOAR tools via webhooks for automated incident response.

## License

This project is provided under the MIT License.
