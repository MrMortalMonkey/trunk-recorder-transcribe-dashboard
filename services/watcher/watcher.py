
import os
import time
import json
import re
import requests
import psycopg2
from pathlib import Path

RECORDINGS_DIR = Path("/recordings")
PROCESSED_DB = Path("/data/processed.txt")

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
MEILI_HOST = os.getenv("MEILI_HOST")
MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")

WHISPER_URL = "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3"
WS_BROADCAST_URL = os.getenv("WS_BROADCAST_URL", "http://ws-server:9000/broadcast")


def connect_db():
    return psycopg2.connect(DATABASE_URL)


def ensure_tables():
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS transcripts (
                    id SERIAL PRIMARY KEY,
                    filename TEXT UNIQUE,
                    transcript TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """
            )
        conn.commit()


def already_in_db(filename: str) -> bool:
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM transcripts WHERE filename = %s LIMIT 1",
                (filename,),
            )
            return cur.fetchone() is not None


def load_processed():
    if not PROCESSED_DB.exists():
        return set()
    return set(PROCESSED_DB.read_text().splitlines())


def save_processed(name: str):
    with PROCESSED_DB.open("a") as f:
        f.write(name + "\n")


def sanitize_id(name: str) -> str:
    base = Path(name).stem
    return re.sub(r"[^a-zA-Z0-9_-]", "_", base)


def transcribe(file_path: Path) -> str:
    with file_path.open("rb") as f:
        response = requests.post(
            WHISPER_URL,
            headers={"Authorization": f"Bearer {DEEPINFRA_API_KEY}"},
            files={"audio": f},
            timeout=300,
        )

    response.raise_for_status()
    return response.json()["text"]


def index_meili(doc: dict):
    url = f"{MEILI_HOST}/indexes/transcripts/documents"
    headers = {
        "Authorization": f"Bearer {MEILI_MASTER_KEY}",
        "Content-Type": "application/json",
    }

    r = requests.post(url, json=[doc], headers=headers, timeout=30)
    r.raise_for_status()


def broadcast_ws(doc: dict):
    try:
        requests.post(WS_BROADCAST_URL, json=doc, timeout=1)
    except:
        pass


def save_db(filename: str, transcript: str, metadata: dict):
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transcripts (filename, transcript, metadata)
                VALUES (%s, %s, %s)
                ON CONFLICT (filename) DO NOTHING
                """,
                (filename, transcript, json.dumps(metadata)),
            )
        conn.commit()


def find_metadata(wav: Path) -> dict:
    json_path = wav.with_suffix(".json")
    if json_path.exists():
        return json.loads(json_path.read_text())
    return {}


def process_file(wav: Path, processed: set):
    if wav.name in processed or already_in_db(wav.name):
        processed.add(wav.name)
        return

    print(f"Transcribing {wav.name}...")

    transcript = transcribe(wav)
    metadata = find_metadata(wav)

    save_db(wav.name, transcript, metadata)

    doc_id = sanitize_id(wav.name)
    start_time = metadata.get("start_time", int(time.time()))

    document = {
        "id": doc_id,
        "filename": wav.name,
        "transcript": transcript,
        "metadata": metadata,
        "start_time": start_time,
    }

    index_meili(document)
    broadcast_ws(document)

    save_processed(wav.name)
    processed.add(wav.name)

    print(f"Done: {wav.name}")


def main():
    print("🚀 Starting trunk watcher (WebSocket enabled)...")
    ensure_tables()
    processed = load_processed()

    while True:
        for wav in RECORDINGS_DIR.rglob("*.wav"):
            try:
                process_file(wav, processed)
            except Exception as e:
                print(f"Error processing {wav.name}: {e}")

        time.sleep(10)


if __name__ == "__main__":
    main()
