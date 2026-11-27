import json
import os
import urllib.request
import urllib.error


def main(args):

    print("[INFO] listlanguagenotes - version 2.0.0")

    google_script_list_url = os.environ.get(
        "GOOGLE_SCRIPT_LIST_URL"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_LIST_URL configured: "
        f"{bool(google_script_list_url)}"
    )

    print(
        f"[INFO] GOOGLE_SCRIPT_LIST_URL valid: "
        f"{bool(google_script_list_url and google_script_list_url.startswith('https://'))}"
    )

    if (
        not google_script_list_url
        or not google_script_list_url.startswith("https://")
    ):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR"
            }
        }

    page = args.get("page", 1)

    page_size = args.get(
        "pageSize",
        20
    )

    try:

        page = int(page)
        page_size = int(page_size)

        if page <= 0:
            page = 1

        if page_size <= 0:
            page_size = 20

    except Exception:

        page = 1
        page_size = 20

    url = (
        f"{google_script_list_url}"
        f"?page={page}"
        f"&pageSize={page_size}"
    )

    print(
        f"[INFO] Request URL: {url}"
    )

    try:

        request = urllib.request.Request(
            url,
            method="GET"
        )

        with urllib.request.urlopen(
            request
        ) as response:

            response_body = (
                response.read()
                .decode("utf-8")
            )

        payload = json.loads(
            response_body
        )

        print(
            "[INFO] Response received successfully"
        )

        return {
            "statusCode": 200,
            "body": payload
        }

    except urllib.error.URLError as error:

        print(
            f"[ERROR] URLError: {error}"
        )

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR"
            }
        }

    except Exception as error:

        print(
            f"[ERROR] {error}"
        )

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR"
            }
        }