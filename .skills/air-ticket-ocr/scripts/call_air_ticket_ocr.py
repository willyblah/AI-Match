#!/usr/bin/env python3
"""
Call Baidu air-ticket (itinerary) OCR and print the structured recognition result.
Base64 data never enters the LLM context.

Usage:
    # Local image file
    python3 call_air_ticket_ocr.py --image /path/to/ticket.jpg

    # Remote image URL
    python3 call_air_ticket_ocr.py --url "https://example.com/ticket.jpg"

    # PDF / OFD file
    python3 call_air_ticket_ocr.py --pdf-file /path/to/doc.pdf [--pdf-file-num 1]
    python3 call_air_ticket_ocr.py --ofd-file /path/to/doc.ofd [--ofd-file-num 1]

Environment:
    INTEGRATIONS_API_KEY - platform-injected API key (required)

Exit codes:
    0 - success, prints one line of JSON with the API response
    1 - API or argument error
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error


ENDPOINT = "https://app-dvtmyuucfs3l-api-DLEO7Vjd8Qea-gateway.appmiaoda.com/rest/2.0/ocr/v1/air_ticket"


def parse_args():
    """Parse command-line arguments."""
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--image", help="Local image path")
    g.add_argument("--url", help="Full image URL")
    g.add_argument("--pdf-file", dest="pdf_file", help="Local PDF path")
    g.add_argument("--ofd-file", dest="ofd_file", help="Local OFD path")
    p.add_argument("--pdf-file-num", dest="pdf_file_num", default=None, help="PDF page number, default is page 1")
    p.add_argument("--ofd-file-num", dest="ofd_file_num", default=None, help="OFD page number, default is page 1")
    return p.parse_args()


def build_params(args) -> dict:
    """Build form params and base64-encode local files internally."""
    params = {}
    if args.image:
        with open(args.image, "rb") as f:
            params["image"] = base64.b64encode(f.read()).decode()
    elif args.url:
        params["url"] = args.url
    elif args.pdf_file:
        with open(args.pdf_file, "rb") as f:
            params["pdf_file"] = base64.b64encode(f.read()).decode()
        if args.pdf_file_num:
            params["pdf_file_num"] = args.pdf_file_num
    elif args.ofd_file:
        with open(args.ofd_file, "rb") as f:
            params["ofd_file"] = base64.b64encode(f.read()).decode()
        if args.ofd_file_num:
            params["ofd_file_num"] = args.ofd_file_num
    return params


def call_api(api_key: str, params: dict) -> dict:
    """Call the air-ticket OCR endpoint and return the decoded response body."""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Gateway-Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Build params, call the API, and print a one-line JSON response."""
    args = parse_args()
    api_key = os.environ.get("INTEGRATIONS_API_KEY", "")
    if not api_key:
        print("INTEGRATIONS_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    d = call_api(api_key, build_params(args))
    if d.get("error_code"):
        print(f"API error {d['error_code']}: {d.get('error_msg')}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
