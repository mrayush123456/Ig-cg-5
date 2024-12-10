from flask import Flask, render_template_string, request, flash, redirect, url_for
from instagrapi import Client
import time
import threading

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Global Variables to control the process
is_running = False
stop_signal = False

# HTML Template with UI for input
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Group Messaging</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #282c34;
            color: #ffffff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: #44475a;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            max-width: 400px;
            width: 100%;
        }
        h1 {
            text-align: center;
            color: #ff79c6;
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin: 10px 0 5px;
            font-weight: bold;
        }
        input, select, button {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #6272a4;
            border-radius: 5px;
            font-size: 16px;
            background-color: #f8f8f2;
            color: #44475a;
        }
        button {
            background-color: #ff79c6;
            color: #ffffff;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #ff92d6;
        }
        .message {
            color: red;
            font-size: 14px;
            text-align: center;
        }
        .success {
            color: green;
            font-size: 14px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Instagram Messenger</h1>
        <form action="/" method="POST" enctype="multipart/form-data">
            <label for="username">Instagram Username:</label>
            <input type="text" id="username" name="username" placeholder="Enter your username" required>

            <label for="password">Instagram Password:</label>
            <input type="password" id="password" name="password" placeholder="Enter your password" required>

            <label for="choice">Send To:</label>
            <select id="choice" name="choice" required>
                <option value="inbox">Inbox</option>
                <option value="group">Group</option>
            </select>

            <label for="target_ids">Target IDs (Comma-separated for multiple):</label>
            <input type="text" id="target_ids" name="target_ids" placeholder="Enter usernames or thread IDs" required>

            <label for="haters_name">Haters Name:</label>
            <input type="text" id="haters_name" name="haters_name" placeholder="Enter hater's name" required>

            <label for="message_file">Message File:</label>
            <input type="file" id="message_file" name="message_file" accept=".txt" required>

            <label for="delay">Delay (seconds):</label>
            <input type="number" id="delay" name="delay" placeholder="Enter delay in seconds" required>

            <button type="submit">Start Sending</button>
        </form>
        <form action="/stop" method="POST" style="margin-top: -10px;">
            <button type="submit" style="background-color: #ff5555;">Stop Sending</button>
        </form>
    </div>
</body>
</html>
'''

# Function to send messages
def send_messages(api, target_ids, messages, delay, choice, haters_name):
    global is_running, stop_signal
    is_running = True
    stop_signal = False

    for message in messages:
        if stop_signal:
            print("[INFO] Stopping message sending process.")
            break
        for target in target_ids:
            try:
                personalized_message = f"Hello {haters_name}, {message}"
                if choice == "inbox":
                    api.direct_send(personalized_message, [target])
                elif choice == "group":
                    api.direct_send(personalized_message, thread_id=target)
                print(f"[SUCCESS] Message sent to {target}: {personalized_message}")
                time.sleep(delay)
            except Exception as e:
                print(f"[ERROR] Failed to send message to {target}: {e}")
    is_running = False

# Flask Routes
@app.route("/", methods=["GET", "POST"])
def index():
    global is_running
    if request.method == "POST":
        try:
            # Get form data
            username = request.form["username"]
            password = request.form["password"]
            choice = request.form["choice"]
            target_ids = request.form["target_ids"].split(",")
            haters_name = request.form["haters_name"]
            delay = int(request.form["delay"])
            message_file = request.files["message_file"]

            # Read messages from file
            messages = message_file.read().decode("utf-8").splitlines()
            if not messages:
                flash("Message file is empty!", "error")
                return redirect(url_for("index"))

            # Login to Instagram
            api = Client()
            api.login(username, password)
            print("[INFO] Logged in successfully.")

            # Start message sending in a separate thread
            if not is_running:
                threading.Thread(
                    target=send_messages,
                    args=(api, target_ids, messages, delay, choice, haters_name),
                ).start()
                flash("Message sending started!", "success")
            else:
                flash("Message sending is already running.", "info")

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            print(f"[ERROR] {e}")

    return render_template_string(HTML_TEMPLATE)

@app.route("/stop", methods=["POST"])
def stop():
    global stop_signal
    stop_signal = True
    flash("Message sending process stopped!", "info")
    return redirect(url_for("index"))

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
