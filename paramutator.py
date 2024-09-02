import sys
import json
import argparse
import requests
from urllib3.exceptions import InsecureRequestWarning
from utils import json_file_handler, list_file_handler, identify_datatype

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

modifiers = [
    # parameter name modifiers
    {"param": "{}[]", "value": "{}"}, # array injection
    {"param": "{}'", "value": "{}"}, # special char in param name

    # parameter value modifiers
    {"value": [1,2,3], "param": "{}", "types": ["str", "int"]}, # array in field with other data type
    {"value": {"a": 1}, "param": "{}", "types": ["str", "int"]}, # object in field with other data type
    {"value": str(10**4000), "param": "{}"}, # long string
    {"value": 2**7000, "param": "{}"}, # large integer
    {"value": "😁😛😋🤣", "param": "{}"}, # emojis
    {"value": "\\u0000\\u0007\\u0008\\u0009\\u000a\\u000b\\u000c\\u000d\\u001b\\u005c", "param": "{}"}, # null byte and escape sequences in unicode
    {"value": "\\x00\\x07\\x08\\x09\\x0a\\x0b\\x0c\\x0d\\x1b\\x5c", "param": "{}"}, # null byte and escape sequences in hex
    {"value": "%C0%80%C0%AF%c1%9c%c0%a2", "param": "{}"}, # overlong utf-8 encoding
    {"value": """!@#$%^&*()-_=+[]:'"`<>,./?""", "param": "{}"}, # almost all special characters
    {"value": """ハッキングされた 被黑客入侵 ହ୍ୟାକ୍ହୋଇଛି""", "param": "{}"}, # japanese, chinese and odiax letters
    {"value": """{}'")""", "param": "{}"}, # special characters for SQLi test
    {"value": """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE foo [<!ENTITY test "HACKED"> ]><root><tag>&test;</tag></root>""", "param": "{}"}, # xxe payload
]

proxies = {"http":"http://127.0.0.1:8080", "https":"http://127.0.0.1:8080"}

class RequestHandler:
    """Handles requests with modifications for testing"""

    def __init__(self, req, allow_redirects, proxies):
        self.__dict__.update(req)
        self.allow_redirects = allow_redirects
        self.proxies = proxies

    def handle(self, part_to_modify):
        """Modifies request parts and sends requests"""

        backup_part = getattr(self, part_to_modify, None)
        if not isinstance(backup_part, dict):
            return
            
        for param, value in backup_part.items():
            value_datatype = identify_datatype(value)
            for modifier in modifiers:
                if value_datatype not in modifier.get("types", [value_datatype]):
                    continue

                modified_part = backup_part.copy()
                modified_param = modifier["param"].format(param) if isinstance(modifier["param"], str) else modifier["param"]
                modified_value = modifier["value"].format(value) if isinstance(modifier["value"], str) else modifier["param"]

                del modified_part[param]
                modified_part[modified_param] = modified_value
                setattr(self, part_to_modify, modified_part)
                print(f"Before: {backup_part}. Now: {getattr(self, part_to_modify)}")
                self.send_request(modifier, part_to_modify)
                setattr(self, part_to_modify, backup_part)

    def send_request(self, modifier, part_to_modify):
        """Sends the HTTP request with the modified parameters"""

        request_args = {
            "method": self.method,
            "url": self.url,
            "params": self.query,
            "headers": self.headers,
            "allow_redirects": self.allow_redirects,
            "cookies": self.cookies,
            "proxies": self.proxies,
            "verify": False,
        }
        if "application/json" in self.headers.get("Content-Type", ""):
            request_args["json"] = self.body
        else:
            request_args["data"] = self.body
        
        try:
            response = requests.request(**request_args)
            print("Response Code:", response.status_code)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-l", "--list", help="Path to file with list of URLs")
    group.add_argument("-j", "--json", help="Path to JSON file with exported requests")
    parser.add_argument("-c", "--config", help="Config file for HTTP headers", required=False)
    parser.add_argument("-r", "--redirect", help="Allow redirects. Default: true", required=False, default="true", choices=["true", "false"])
    
    args = parser.parse_args()
    file_path = args.list or args.json
    header_config_file = args.config
    allow_redirects = args.redirect.lower() == "true"
    header_config = None

    if header_config_file:
        with open(header_config_file, "r") as f:
            header_config = json.load(f)

    reqs = json_file_handler(file_path) if args.json else list_file_handler(file_path) if args.list else []
        
    for req in reqs:
        try:
            print(f"Currently testing: {req['method']} {req['url']}")
            if header_config:
                req["headers"].update(header_config)

            reqHandler = RequestHandler(req, allow_redirects, proxies)
            reqHandler.handle("query")
            reqHandler.handle("body")

        except KeyboardInterrupt:
            if input("Skip current request (S), Exit (E): ") == "E":
                sys.exit()
    