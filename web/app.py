
import os
import psycopg
from flask import Flask, request, redirect, url_for
from markupsafe import escape

# We're going to write a function that constructs an URL for the database
def get_database_url():
    # The app can run in two 'modes' — production mode, or development mode.
    # This is determined by the `APP_ENV` environment variable.
    # Having dev and production modes is quite a common pattern and you will
    # see it in many real-world applications.
    if os.environ.get("APP_ENV") == "PRODUCTION":
        password = os.environ.get("POSTGRES_PASSWORD")
        hostname = os.environ.get("POSTGRES_HOSTNAME")
        # This URL below is constructed out of the password and hostname
        # We'll use this URL to connect to the database in production
        return f"postgres://postgres:{password}@{hostname}:5432/postgres"
    else:
        # This URL is for our local database. You may need to edit it.
        return "postgres://localhost:5432/postgres"

# We're going to write a function that sets up the database with the right table
def setup_database(url):
    # We connect using the URL
    connection = psycopg.connect(url)

    # Get a 'cursor' object that we can use to run SQL
    cursor = connection.cursor()

    # Execute some SQL to create the table
    cursor.execute("CREATE TABLE IF NOT EXISTS messages (message TEXT, username TEXT);")
    connection.commit()
    cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS username TEXT;")

    # And commit the changes to ensure that they 'stick' in the database.
    connection.commit()

# We run the two functions above
POSTGRES_URL = get_database_url()
setup_database(POSTGRES_URL)

app = Flask(__name__)

# Below are two fairly ordinary Flask routes

@app.route("/")
def get_messages():
    # Connect to the database
    connection = psycopg.connect(POSTGRES_URL)

    # Run some SQL
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM messages;")

    # Get the results
    rows = cursor.fetchall()

    # Format the results and add a form too
    return generate_form() + format_messages(rows)

# These two methods generate HTML lists and forms
def format_messages(messages):
    output = "<ul>"
    for message in messages:
        # We escape the message to avoid the user sending us HTML and tricking
        # us into rendering it.
        escaped_message = escape(message[0])
        escaped_user = escape(message[1])
        output += f"<li>{escaped_message}</li><br><i> by {escaped_user}</i><hr>"
    output += "</ul>"
    return output

def generate_form():
    return """
    <form action="/" method="POST">
        <label for="title">Message</label>
        <input type="text" name="message">
        
        <label for="title">Username</label>
        <input type="text" name="username">

        <input type="submit" value="Send">
    </form>
    """

# This method receives the POST request from the form above
@app.route("/", methods=["POST"])
def post_message():
    # We extract the message from the request
    message = request.form["message"]
    username = request.form["username"]


    # Insert a new message record into the database
    connection = psycopg.connect(POSTGRES_URL)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO messages (message, username) VALUES (%s, %s);", (message, username))
    connection.commit()

    # And redirect to the main page
    return redirect(url_for("get_messages"))

if __name__ == '__main__':
    # We also run the server differently depending on the environment.
    # In production we don't want the fancy error messages — users won't know
    # what to do with them. So no `debug=True`
    if os.environ.get("APP_ENV") == "PRODUCTION":
        app.run(port=5000, host='0.0.0.0')
    else:
        app.run(debug=True, port=5001, host='0.0.0.0')
