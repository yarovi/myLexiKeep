
import json
import os
import urllib.request
import urllib.error


def main(args):
    print("[INFO] savelanguagenote - version 2.0.1")

    word = args.get("word")
    translations = args.get("translations")
    gamy = args.get("gamy")

    # Validaciones
    if not isinstance(word, str) or not word.strip():
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "word is required"
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

    if type(gamy) is not int:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "gamy must be an integer"
            }
        }

    normalized_translations = [
        str(item).strip()
        for item in translations
        if str(item).strip()
    ]

    if not normalized_translations:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "translations is required"
            }
        }

    GOOGLE_SCRIPT_SAVE_URL = os.environ.get(
        "GOOGLE_SCRIPT_SAVE_URL"
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
        "translations": normalized_translations,
        "gamy": gamy
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
        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:
            google_response = response.read().decode("utf-8")

        # Procesar la respuesta real de Google
        result = json.loads(google_response)

        if not isinstance(result, dict):
            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Invalid Google Script response"
                }
            }

        # Validar errores funcionales de Google
        if "error" in result or result.get("success") is not True:
            print("[ERROR] Google Script rejected the operation")

            return {
                "statusCode": 502,
                "body": {
                    "error": "UPSTREAM_ERROR",
                    "message": "Google Script rejected the operation"
                }
            }

        # Validar el contrato de respuesta
        required_fields = [
            "id",
            "date",
            "word",
            "translations",
            "gamy"
        ]

        if any(
            field not in result or result[field] is None
            for field in required_fields
        ):
            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Google Script response is incomplete"
                }
            }

        print("[INFO] Word saved successfully")

        return {
            "statusCode": 201,
            "body": result
        }

    except urllib.error.HTTPError as ex:
        print(f"[ERROR] HTTPError: {ex}")

        return {
            "statusCode": 502,
            "body": {
                "error": "UPSTREAM_ERROR",
                "message": "Google Script returned an HTTP error"
            }
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 502,
            "body": {
                "error": "INVALID_UPSTREAM_RESPONSE",
                "message": "Google Script returned invalid JSON"
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
