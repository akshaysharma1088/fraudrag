"""Minimal stand-in for the Ollama chat API, used only to test the pipeline end to end."""
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        props = body["format"]["properties"]
        if "links" in props:
            user = json.loads(body["messages"][1]["content"])
            content = {"links": [{"line_id": x["line_id"], "option": x["options"][0]["option"], "same_payee": True}
                                 for x in user["statement_lines"]]}
        else:
            content = {"label": "DEFER", "line_ids": [], "reason": "fake"}
        out = {"message": {"content": json.dumps(content)}, "prompt_eval_count": 100, "eval_count": 10}
        data = json.dumps(out).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(data)
    def log_message(self, *a): pass

HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 11434), H).serve_forever()
