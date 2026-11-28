
import json
import os
import urllib.request
import urllib.error


def main(args):

    print("[INFO] deletelanguagenote - version 1.0.1")

    record_id = args.get("id")

    # Validaciones
    if not isinstance(record_id, str) or not record_id.strip():
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "id is required and must be a string"
            }
        }

    google_script_delete_url = os.environ.get(
        "GOOGLE_SCRIPT_DELETE_URL"
    )

    if (
        not google_script_delete_url
        or not google_script_delete_url.startswith("https://")
    ):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_DELETE_URL is not configured"
            }
        }

    payload = {
        "id": record_id.strip()
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        google_script_delete_url,
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

        # Procesar respuesta real de Google
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
        if (
            not isinstance(result.get("id"), str)
            or result["id"] != payload["id"]
            or not isinstance(result.get("message"), str)
        ):
            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Google Script response violates the contract"
                }
            }

        print("[INFO] Word deleted successfully")

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
                "message": "Unable to delete word"
            }
        }
