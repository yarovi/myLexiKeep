import json
import os
import urllib.request
import urllib.error


def main(args):

    print(
        "[INFO] deletelanguagenote - version 1.0.0"
    )

    record_id = args.get("id")

    if not record_id:

        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "id is required"
            }
        }

    google_script_delete_url = os.environ.get(
        "GOOGLE_SCRIPT_DELETE_URL"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_DELETE_URL configured: "
        f"{bool(google_script_delete_url)}"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_DELETE_URL valid: "
        f"{bool(google_script_delete_url and google_script_delete_url.startswith('https://'))}"
    )

    if (
        not google_script_delete_url
        or not google_script_delete_url.startswith(
            "https://"
        )
    ):

        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_DELETE_URL is not configured"
            }
        }

    payload = {
        "id": str(record_id).strip()
    }

    data = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

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
            request
        ) as response:

            response.read().decode(
                "utf-8"
            )

        return {
            "statusCode": 200,
            "body": {
                "message": "Word deleted successfully",
                "id": payload["id"]
            }
        }

    except urllib.error.HTTPError as ex:

        print(
            f"[ERROR] HTTPError: {ex}"
        )

        return {
            "statusCode": ex.code,
            "body": {
                "error": "UPSTREAM_ERROR",
                "message": "Google Script returned an error"
            }
        }

    except Exception as ex:

        print(
            f"[ERROR] {str(ex)}"
        )

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Unable to delete word"
            }
        }