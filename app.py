from flask import Flask, request, jsonify
import hmac
import hashlib
import json

import threading
import time
from magic import magic
import os

import lark_oapi
from lark_oapi.api.im.v1 import *

from lark_config import *

from openai import BadRequestError, OpenAI
import config


app = Flask(__name__)

larkClient = lark_oapi.Client.builder() \
    .app_id(APP_ID) \
    .app_secret(APP_SECRET) \
    .log_level(lark_oapi.LogLevel.DEBUG) \
    .build()


cfg = config.Config(os.path.join(os.getcwd(), "keys.cfg"))
openAIClient = OpenAI(api_key=cfg["OPENAI_API_KEY"])    

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


def lark_send_message(chatId, msg):
    reply = {"text": msg}

    req = CreateMessageRequest.builder() \
		.receive_id_type("chat_id") \
		.request_body(CreateMessageRequestBody.builder()
					  .receive_id(chatId)
					  .msg_type("text")
					  .content(json.dumps(reply))
					  .build()) \
		.build()

    resp = larkClient.im.v1.message.create(req)

    if not resp.success():
        lark_oapi.logger.error(
			f"client.im.v1.message.create failed, code: {resp.code}, msg: {resp.msg}, log_id: {resp.get_log_id()}")
        return {}

    lark_oapi.logger.info(lark_oapi.JSON.marshal(resp.data, indent=4))

def handle_lark(event):
    # print(event)
    message = event['message']
    content = message['content']
    msg = json.loads(content)['text']
    print(msg)

    # pass the issue url to swe-agent
    # magic(msg)

    response = openAIClient.chat.completions.create(
        messages=[{"role": "user", "content": msg}],
        model='gpt-3.5-turbo',
        temperature=0.0,
        max_tokens=512,
        n=1,
        stop=None
    )    
    
    lark_send_message(message['chat_id'], response.choices[0].message.content)

@app.route('/lark', methods=['POST'])
def lark():
    data = request.data    

    # challenge = json.loads(data.decode('utf-8'))['challenge']
    # resp['challenge'] = {"challenge": challenge}

    event = json.loads(data.decode('utf-8'))['event']
    threading.Thread(target=handle_lark, args=(event,)).start()

    return {}, 200   

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080, threaded=True)
