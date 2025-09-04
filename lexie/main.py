# main.py
import sys, json, datetime as dt
from pathlib import Path
from call_agent import route
from pdf_reporter import generate_report

def usage():
    print("Usage:")
    print('  python main.py free-text "your sentence here"', flush=True)
    print('  python main.py document "C:/path/to/file.pdf"', flush=True)
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        usage()

    mode = sys.argv[1].lower()
    arg  = sys.argv[2]

    if mode == "free-text":
        payload = {
            "mode": "free_text",
            "user_text": arg,
            "policies": ["gdpr", "ai_act"],
            "top_k": 12
        }
    elif mode == "document":
        payload = {
            "mode": "document",
            "document_path": arg,
            "policies": ["gdpr", "ai_act"],
            "top_k": 12
        }
    else:
        usage()

    print(f"[Lexie] Running mode={mode}", flush=True)

    try:
        result = route(payload)  # route non genera il PDF
    except Exception as e:
        print("[Lexie] ERROR in route():", e, flush=True)
        raise

    # Log JSON su disco
    Path("runtime/logs").mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = Path(f"runtime/logs/result-{mode}-{ts}.json")
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=== LEXIE RESULT (JSON) ===", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print(f"[Lexie] Saved JSON: {log_path}", flush=True)

    # Genera PDF
    Path("runtime/outputs").mkdir(parents=True, exist_ok=True)
    pdf_path = Path(f"runtime/outputs/report_{ts}.pdf")
    try:
        generate_report(result, str(pdf_path))
        print(f"PDF: {pdf_path}", flush=True)  # <-- i test cercano questa riga
    except Exception as e:
        print("[Lexie] ERROR generating PDF:", e, flush=True)
        raise

if __name__ == "__main__":
    main()
