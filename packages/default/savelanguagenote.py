import json
import os
import urllib.request
import urllib.error


def main(args):

    print("[INFO] savelanguagenote - version 1.2.0 - deployed from local project")
    word = args.get("word")
    translate = args.get("translate")

    # Validar parámetros
    if not word or not translate:
        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "word and translate are required"
            }
        }

    google_script_url = os.environ.get("GOOGLE_SCRIPT_URL")

    print(f"[INFO] GOOGLE_SCRIPT_URL configured: {bool(google_script_url)}")
    print(f"[INFO] GOOGLE_SCRIPT_URL valid: {bool(google_script_url and google_script_url.startswith('https://'))}")

    if not google_script_url or not google_script_url.startswith("https://"):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_URL is not configured"
            }
        }

    payload = {
        "word": word.strip(),
        "translate": translate.strip()
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        google_script_url,
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
                "word": word,
                "translate": translate
            }
        }

    except Exception as ex:

        print("ERROR:", str(ex))

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Unable to save word"
            }
        }

'''def mai_vn_v0(args):
    name = args.get("name", "stranger")
    greeting = "Hello " + name + "!"
    print(greeting)
    return {"body": greeting}
'''