from urllib.parse import urlparse, parse_qs, quote, unquote
import json
import xml.etree.ElementTree as ET

def params_normalizer(params, contenttype):
    contenttype_tested = identify_contenttype(params)
    if contenttype_tested != contenttype:
        contenttype = contenttype_tested
    match contenttype:
        case "application/x-www-form-urlencoded" | "querystring":
            params = {key: value for key, value in [part.split("=") for part in params.split("&")]}
        case "application/json":
            params = json.loads(params)
        case "application/xml":
            params = ET.fromstring(params)
    return params

def json_file_handler(file_path):
    with open(file_path, "r") as f:
        json_data = json.load(f)

    reqs = []
    for row in json_data:
        request = row.get("Request", {})
        method = request.get("Method", "GET")
        host = request.get("Host", "")
        path = request.get("Path", "")
        query = request.get("Query", {})
        headers = request.get("Headers", {})
        contenttype = request.get("ContentType", "")
        parameters = request.get("Parameters", [])
        cookies = request.get("Cookies", "")
        body = request.get("Body", "")

        if query:
            try:
                query = params_normalizer(query, "querystring")
            except Exception as e:
                print("Invalid query string")
        if body:
            body = params_normalizer(body, contenttype)
        
        headers = {header.split(":")[0]: header.split(":")[1].strip() for header in headers.strip().split("\n")}
        reqs.append({
            "method": method,
            "url": f"{host}{path}",
            "query": query,
            "contenttype": contenttype,
            "body": body,
            "cookies": cookies,
            "headers": headers
        })
    
    return reqs

def list_file_handler(file_path):
    reqs = []
    with open(file_path, "r") as f:
        for url in f:
            url = unquote(url.strip())
            parsed = urlparse(url)
            scheme = parsed.scheme
            domain = parsed.netloc
            path = parsed.path
            query_params = parse_qs(parsed.query)
            base_url = "{}://{}{}".format(scheme, domain, path)
            reqs.append({
                "method": "GET",
                "url": base_url,
                "query": query_params,
                "contenttype": "",
                "body": "",
                "cookies": [],
                "headers": {}
            })
    return reqs

def identify_datatype(value):
    if isinstance(value, dict):
        return "dict"
    elif isinstance(value, list):
        return 'list'
    else:
        try:
            float(value)
            if value.isdigit():
                return "int"
            else:
                return 'float'
        except:
            return "other"

def identify_contenttype(value):
    try:
        json.loads(value)
        return "application/json"
    except:
        try:
            ET.fromstring(value)
            return "application/xml"
        except:
            return "application/x-www-form-urlencoded"
