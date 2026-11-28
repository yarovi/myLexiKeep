
import json
import os
import urllib.request
import urllib.error


def main(args):

    print("[INFO] updatelanguagenote - version 1.0.1")

    record_id = args.get("id")
    word = args.get("word")
    translations = args.get("translations")
    gamy = args.get("gamy")

    # Validaciones
    if not isinstance(record_id, str) or not record_id.strip():
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "id is required and must be a string"
            }
        }

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

    google_script_update_url = os.environ.get(
        "GOOGLE_SCRIPT_UPDATE_URL"
    )

    if (
        not google_script_update_url
        or not google_script_update_url.startswith("https://")
    ):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_UPDATE_URL is not configured"
            }
        }

    payload = {
        "id": record_id.strip(),
        "word": word.strip(),
        "translations": normalized_translations,
        "gamy": gamy
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        google_script_update_url,
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

        # Validar errores funcionales
        if "error" in result or result.get("success") is not True:

            error_code = result.get("error")

            if error_code == "NOT_FOUND":
                return {
                    "statusCode": 404,
                    "body": {
                        "error": "NOT_FOUND",
                        "message": "Record not found"
                    }
                }

            if error_code == "BAD_REQUEST":
                return {
                    "statusCode": 400,
                    "body": {
                        "error": "BAD_REQUEST",
                        "message": result.get(
                            "message",
                            "Invalid request"
                        )
                    }
                }

            print("[ERROR] Google Script rejected the operation")

            return {
                "statusCode": 502,
                "body": {
                    "error": "UPSTREAM_ERROR",
                    "message": "Google Script rejected the operation"
                }
            }

        # Validar contrato de respuesta
        required_fields = [
            "id",
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

        if (
            not isinstance(result["id"], str)
            or result["id"] != payload["id"]
            or not isinstance(result["word"], str)
            or not isinstance(result["translations"], list)
            or not all(
                isinstance(item, str)
                for item in result["translations"]
            )
            or type(result["gamy"]) is not int
        ):
            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Google Script response violates the contract"
                }
            }

        print("[INFO] Word updated successfully")

        return {
            "statusCode": 200,
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
                "message": "Unable to update word"
            }
        }
