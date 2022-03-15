import json
import os
from flask import Flask, request, send_from_directory, render_template, Response
from smtp import mail

try:
    import config
except Exception as e:
    print(e)

# Config
debug = True

# App #
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)


# Functions #

# Send a mail
def send_mail(sender, recipient, subject, content, file=None):
    status = mail.send_mail_raw(sender, recipient, subject, content, file)
    message = f"{status}: Error, check logs."
    if status == 200:
        message = "Mail sent successfully!"
    return {"status": status, "message": message}


# Router #

# Default index
@app.route("/")
def index():
    return render_template("base.html")


# Favicon for old browsers
@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# the send route
@app.route("/api/send", methods=["POST"])
def send_route():
    use_json = request.args.get("json", default=False, type=lambda v: v.lower() == 'true')
    file = None
    if use_json:
        content = request.json

        print(content)

        if "sender" not in content or not content["sender"]:
            return Response(json.dumps({"status": 400, "message": "No sender."}), status=400,
                            mimetype='application/json')
        if "recipient" not in content or not content["recipient"]:
            return Response(json.dumps({"status": 400, "message": "No recipient."}), status=400,
                            mimetype='application/json')
        if "subject" not in content or not content["subject"]:
            return Response(json.dumps({"status": 400, "message": "No subject."}), status=400,
                            mimetype='application/json')
        if "content" not in content or not content["content"]:
            return Response(json.dumps({"status": 400, "message": "No content."}), status=400,
                            mimetype='application/json')

        if "file" in content and content["file"]:
            file = content["file"]

        # get fields
        sender = content["sender"]
        recipient = content["recipient"]
        subject = content["subject"]
        content = content["content"]
    else:
        print(request.form)

        if "sender" not in request.form or not request.form["sender"]:
            return Response(json.dumps({"status": 400, "message": "No sender."}), status=400,
                            mimetype='application/json')
        if "recipient" not in request.form or not request.form["recipient"]:
            return Response(json.dumps({"status": 400, "message": "No recipient."}), status=400,
                            mimetype='application/json')
        if "subject" not in request.form or not request.form["subject"]:
            return Response(json.dumps({"status": 400, "message": "No subject."}), status=400,
                            mimetype='application/json')
        if "content" not in request.form or not request.form["content"]:
            return Response(json.dumps({"status": 400, "message": "No content."}), status=400,
                            mimetype='application/json')

        if "file" in request.form and request.form["file"]:
            file = request.form["file"]


        sender = request.form["sender"]
        recipient = request.form["recipient"]
        subject = request.form["subject"]
        content = request.form["content"]

    status = send_mail(sender, recipient, subject, content, file)

    return Response(json.dumps({"status": status["status"], "message": status["message"]}), status=status["status"],
                    mimetype='application/json')


# Run #
if __name__ == "__main__":
    app.run(debug=debug)
