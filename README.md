# ParaMutator

ParaMutator is an API fuzzer that bombards entry points with unexpected inputs to cause anomalies, signifying potential security vulnerabilities.

## Workflow

This tool needs to be fed with API endpoints to be probed and any HTTP headers required to send a successful request. It will then:

1. Identify entry points - query and body parameters;
2. For each entry point, provide different values which might be unexpected by the server;
3. Proxy all requests through Burp Suite.

## Usage

You need to provide either a JSON file with request details or a TXT file with a list of URLs. Burp Suite must be open during scan, so that you can view responses in proxy history. 

```
usage: paramutator.py [-h] (-l LIST | -j JSON) [-c CONFIG] [-r REDIRECT]

options:
  -h, --help            show this help message and exit
  -l LIST, --list LIST  Path to file with list of URLs
  -j JSON, --json JSON
                        Path to JSON file with exported requests
  -c CONFIG, --config CONFIG
                        Config file for HTTP headers
  -r REDIRECT, --redirect REDIRECT
                        Allow redirects. Default: true
```

### How to generate JSON file

1. Open Burp Suite.
2. Install Logger++ extension.
3. Get requests logged, by sending them via repeater or through proxy.
4. Export necessary requests in JSON format. 

### Config syntax

Configuration file used to update headers must be in JSON format:
```json
{
    "Cookie": "Something",
    "Content-Type": "application/json"
}
```

### Some handy features

- During scan, you can press CTRL+C to pause. Typing "E" will terminate the program, while "S" will skip the request currently tested. 


## Test cases

- Unexpected data type - providing string in integer field
- Overly long integer or string
- Array injection in parameter name
- Emojis
- Data encoded with hex and unicode schemes
- Escape sequences - \n, \r, \t, \b, \f, \v, \a, \e
- Null byte
- Special characters
- Injection payloads
- Overlong UTF-8 Encoding - Using overly long UTF-8 sequences to represent characters (e.g., A as %C0%80 instead of %41)
- Japanese, chinese and odiax letters

