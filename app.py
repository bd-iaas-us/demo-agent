from flask import Flask, request, jsonify
import hmac
import hashlib
import json

import threading
import time
from magic import magic
import os

app = Flask(__name__)

#webhook secret is set in github website

#read from environment variable
webhook_secret = os.environ.get("WEBHOOK_SECRET")
if webhook_secret is None:
    print("WEBHOOK_SECRET is not set")
    exit(1)

helper_name = "dev009527"


def handle_issue(html_url):
    print(f"I am working on this issue:{html_url}")
    magic(html_url)
    print("done...")

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature')

    data = request.data

    secret_bytes = bytes(webhook_secret, 'utf-8')
    hash_signature = hmac.new(secret_bytes, data, hashlib.sha1).hexdigest()

    if hmac.compare_digest(signature, f"sha1={hash_signature}"):
        event_type = request.headers.get('X-GitHub-Event')
        if event_type == 'issues' and request.json['action'] == 'opened':
            #the assignee of the issue
            #title of the issue
            title = request.json['issue']['title']
            assignees = [e["login"] for e in request.json['issue']['assignees']]
            if helper_name in assignees or title.startswith(f"@{helper_name}"):
                html_url = request.json['issue']['html_url']
                print(f"Issue opened for helper, {html_url}")
                #create a new process for a long running AI tasks
                #thread will report "ValueError: signal only works in main thread of the main interpreter"
                threading.Thread(target=handle_issue, args=(html_url,)).start()

        elif event_type == 'ping':
            print("Ping event received")
        else:
            print(f"Unhandled event type: {event_type}.{request.json['action']}")
        #print(data)
        
        return jsonify({'message': 'Webhook received'}), 200
    else:
        return jsonify({'error': 'Invalid signature'}), 403

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=8080, threaded=True)
