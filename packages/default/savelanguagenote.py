import json
import os
import urllib.request
import urllib.error


def main(args):
    print("[INFO] savelanguagenote - version 2.0.0")

    word = args.get("word")
    translations = args.get("translations")
    game = args.get("game")

    # Validaciones
    if not word:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "word is required"
            }
        }

    if not translations:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "translations is required"
            }
        }

    if not isinstance(translations, list):
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "translations must be an array"
            }
        }

    if game is None:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "game is required"
            }
        }

    GOOGLE_SCRIPT_SAVE_URL = os.environ.get(
        "GOOGLE_SCRIPT_SAVE_URL"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_SAVE_URL configured: "
        f"{bool(GOOGLE_SCRIPT_SAVE_URL)}"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_SAVE_URL valid: "
        f"{bool(GOOGLE_SCRIPT_SAVE_URL and GOOGLE_SCRIPT_SAVE_URL.startswith('https://'))}"
    )

    if (
        not GOOGLE_SCRIPT_SAVE_URL
        or not GOOGLE_SCRIPT_SAVE_URL.startswith("https://")
    ):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_SAVE_URL is not configured"
            }
        }

    payload = {
        "word": word.strip(),
        "translations": [
            str(item).strip()
            for item in translations
            if str(item).strip()
        ],
        "game": game
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        GOOGLE_SCRIPT_SAVE_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request) as response:
            google_response = response.read().decode("utf-8")

        return {
            "statusCode": 201,
            "body": {
                "message": "Word saved successfully",
                "word": payload["word"],
                "translations": payload["translations"],
                "game": payload["game"]
            }
        }

    except urllib.error.HTTPError as ex:
        print(f"[ERROR] HTTPError: {ex}")

        return {
            "statusCode": ex.code,
            "body": {
                "error": "UPSTREAM_ERROR",
                "message": "Google Script returned an error"
            }
        }

    except Exception as ex:
        print(f"[ERROR] {str(ex)}")

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Unable to save word"
            }
        }