import json
import os
import urllib.request
import urllib.error


def main(args):

    print(
        "[INFO] updatelanguagenote - version 1.0.0"
    )

    record_id = args.get("id")
    word = args.get("word")
    translations = args.get("translations")
    gamy = args.get("gamy")

    if not record_id:

        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "id is required"
            }
        }

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

    if not isinstance(
        translations,
        list
    ):

        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "translations must be an array"
            }
        }

    if gamy is None:

        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "gamy is required"
            }
        }

    google_script_update_url = os.environ.get(
        "GOOGLE_SCRIPT_UPDATE_URL"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_UPDATE_URL configured: "
        f"{bool(google_script_update_url)}"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_UPDATE_URL valid: "
        f"{bool(google_script_update_url and google_script_update_url.startswith('https://'))}"
    )

    if (
        not google_script_update_url
        or not google_script_update_url.startswith(
            "https://"
        )
    ):

        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_UPDATE_URL is not configured"
            }
        }

    payload = {

        "id": str(record_id).strip(),

        "word": str(word).strip(),

        "translations": [
            str(item).strip()
            for item in translations
            if str(item).strip()
        ],

        "gamy": gamy

    }

    data = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

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
            request
        ) as response:

            response.read().decode(
                "utf-8"
            )

        return {
            "statusCode": 200,
            "body": {
                "message": "Word updated successfully",
                "id": payload["id"],
                "word": payload["word"],
                "translations": payload["translations"],
                "gamy": payload["gamy"]
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
                "message": "Unable to update word"
            }
        }