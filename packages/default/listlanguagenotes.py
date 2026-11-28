
import json
import os
import re
import urllib.request
import urllib.error
import urllib.parse


def parse_positive_integer(value):

    if type(value) is int:
        number = value

    elif isinstance(value, str) and re.fullmatch(
        r"[0-9]+", value.strip()
    ):
        number = int(value.strip())

    else:
        raise ValueError("Invalid integer")

    if number <= 0 or number > 9007199254740991:
        raise ValueError("Integer out of range")

    return number


def is_valid_record(record):

    return (
        isinstance(record, dict)
        and isinstance(record.get("id"), str)
        and bool(record["id"].strip())
        and isinstance(record.get("date"), str)
        and re.fullmatch(
            r"[0-9]{2}/[0-9]{2}/[0-9]{4}",
            record["date"]
        ) is not None
        and isinstance(record.get("word"), str)
        and bool(record["word"].strip())
        and isinstance(record.get("translations"), list)
        and len(record["translations"]) > 0
        and all(
            isinstance(item, str) and bool(item.strip())
            for item in record["translations"]
        )
        and type(record.get("gamy")) is int
    )


def is_valid_response(result, page, page_size):

    records = result.get("data")
    pagination = result.get("pagination")

    if (
        not isinstance(records, list)
        or not isinstance(pagination, dict)
    ):
        return False

    required_fields = (
        "page",
        "pageSize",
        "totalItems",
        "totalPages"
    )

    if any(
        type(pagination.get(field)) is not int
        for field in required_fields
    ):
        return False

    total_items = pagination["totalItems"]
    total_pages = pagination["totalPages"]

    if (
        pagination["page"] != page
        or pagination["pageSize"] != page_size
        or total_items < 0
        or total_pages < 0
    ):
        return False

    expected_pages = (
        total_items + page_size - 1
    ) // page_size

    expected_records = min(
        page_size,
        max(0, total_items - (page - 1) * page_size)
    )

    if (
        total_pages != expected_pages
        or len(records) != expected_records
    ):
        return False

    return all(
        is_valid_record(record)
        for record in records
    )


def main(args):

    print("[INFO] listlanguagenotes - version 2.0.1")

    # Validar parámetros
    try:

        page = parse_positive_integer(
            args.get("page", 1)
        )

        page_size = parse_positive_integer(
            args.get("pageSize", 20)
        )

    except (ValueError, TypeError):

        return {
            "statusCode": 400,
            "body": {
                "error": "BAD_REQUEST",
                "message": "page and pageSize must be positive integers"
            }
        }

    google_script_list_url = os.environ.get(
        "GOOGLE_SCRIPT_LIST_URL"
    )

    if (
        not google_script_list_url
        or not google_script_list_url.startswith("https://")
    ):
        return {
            "statusCode": 500,
            "body": {
                "error": "CONFIGURATION_ERROR",
                "message": "GOOGLE_SCRIPT_LIST_URL is not configured"
            }
        }

    query = urllib.parse.urlencode({
        "page": page,
        "pageSize": page_size
    })

    url = f"{google_script_list_url}?{query}"

    print(
        f"[INFO] page={page}, pageSize={page_size}"
    )

    try:

        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            response_body = response.read().decode("utf-8")

        result = json.loads(response_body)

        if not isinstance(result, dict):

            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Invalid Google Script response"
                }
            }

        # Validar errores funcionales
        if (
            "error" in result
            or result.get("success") is not True
        ):

            if result.get("error") == "BAD_REQUEST":

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
        if not is_valid_response(
            result,
            page,
            page_size
        ):

            return {
                "statusCode": 502,
                "body": {
                    "error": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Google Script response violates the contract"
                }
            }

        print(
            f"[INFO] Records returned: {len(result['data'])}"
        )

        return {
            "statusCode": 200,
            "body": result
        }

    except urllib.error.HTTPError as error:

        print(f"[ERROR] HTTPError: {error}")

        return {
            "statusCode": 502,
            "body": {
                "error": "UPSTREAM_ERROR",
                "message": "Google Script returned an HTTP error"
            }
        }

    except (TimeoutError, urllib.error.URLError) as error:

        print(f"[ERROR] Connection error: {error}")

        return {
            "statusCode": 502,
            "body": {
                "error": "UPSTREAM_ERROR",
                "message": "Unable to connect to Google Script"
            }
        }

    except (json.JSONDecodeError, UnicodeDecodeError):

        return {
            "statusCode": 502,
            "body": {
                "error": "INVALID_UPSTREAM_RESPONSE",
                "message": "Google Script returned invalid JSON"
            }
        }

    except Exception as error:

        print(f"[ERROR] {error}")

        return {
            "statusCode": 500,
            "body": {
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Unable to list words"
            }
        }
