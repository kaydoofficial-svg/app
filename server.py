import os
import subprocess
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import tempfile
import shutil

load_dotenv("config.env")

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

UPLOAD_DIR = tempfile.mkdtemp()


def convert_to_mp3(mp4_path: str, mp3_path: str) -> bool:
    """Convert an MP4 file to MP3 using ffmpeg."""
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",               # overwrite output if exists
                "-i", mp4_path,     # input file
                "-vn",              # no video
                "-acodec", "libmp3lame",
                "-q:a", "2",        # high quality VBR (~190 kbps)
                mp3_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600,            # 10-minute timeout for large files
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg not found. Please install ffmpeg and make sure it's on your PATH."
        )


def send_to_telegram(mp3_path: str, filename: str) -> dict:
    """Send the MP3 file to the configured Telegram channel."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    with open(mp3_path, "rb") as audio_file:
        response = requests.post(
            url,
            data={"chat_id": CHANNEL_ID},
            files={"audio": (filename, audio_file, "audio/mpeg")},
            timeout=300,
        )
    return response.json()


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".mp4"):
        return jsonify({"success": False, "error": "Only .mp4 files are accepted."}), 400

    if not BOT_TOKEN or not CHANNEL_ID:
        return jsonify({
            "success": False,
            "error": "Telegram credentials not set. Check config.env."
        }), 500

    # Build file paths
    base_name = os.path.splitext(file.filename)[0]
    mp3_filename = base_name + ".mp3"
    mp4_path = os.path.join(UPLOAD_DIR, file.filename)
    mp3_path = os.path.join(UPLOAD_DIR, mp3_filename)

    try:
        # Save uploaded MP4
        file.save(mp4_path)

        # Convert to MP3
        try:
            success = convert_to_mp3(mp4_path, mp3_path)
        except RuntimeError as e:
            return jsonify({"success": False, "error": str(e)}), 500

        if not success:
            return jsonify({"success": False, "error": "Conversion failed. Check that the file is a valid MP4."}), 500

        # Send to Telegram
        tg_response = send_to_telegram(mp3_path, mp3_filename)

        if not tg_response.get("ok"):
            error_desc = tg_response.get("description", "Unknown Telegram error.")
            return jsonify({"success": False, "error": f"Telegram error: {error_desc}"}), 500

        return jsonify({
            "success": True,
            "message": f"✅ '{mp3_filename}' sent to the channel successfully."
        })

    finally:
        # Clean up temp files
        for path in [mp4_path, mp3_path]:
            if os.path.exists(path):
                os.remove(path)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/health", methods=["GET"])
def health():
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    creds_ok = bool(BOT_TOKEN and CHANNEL_ID)
    return jsonify({
        "ffmpeg": "found" if ffmpeg_ok else "NOT FOUND — install ffmpeg",
        "credentials": "set" if creds_ok else "missing — fill in config.env",
    })


if __name__ == "__main__":
    print("━" * 50)
    print("  MP4 → MP3 Class Recorder")
    print("  Open http://localhost:5050 in your browser")
    print("━" * 50)
    app.run(host="0.0.0.0", port=5050, debug=False)
