# Postwoman

Simple GUI tool to send HTTP requests with support for parallel execution.

## Features
- Choose HTTP method and URL
- Add custom headers
- Specify request body as raw text, JSON, form-urlencoded or form-data
- For form-data use **Add field** to create key/value pairs and select files with the **File...** button
- Set number of parallel requests to send concurrently
- View status code, response time and body snippet

## Usage
Run the tool with Python 3 and the `requests` library installed:

```bash
pip install requests
python http_client.py
```

Enter your request details and press **Send**.
