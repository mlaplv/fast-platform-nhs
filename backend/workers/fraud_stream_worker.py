import sys

def main() -> None:
    print("ℹ️ [FraudStreamWorker] Retired in favor of high-efficiency on-demand arq task architecture.")
    print("Forensic analysis is now executed on-demand by backend/arq_worker.py (run_fraud_forensic task).")
    print("This worker process is deactivated to preserve VPS memory (saves 384MB RAM).")
    sys.exit(0)

if __name__ == "__main__":
    main()
