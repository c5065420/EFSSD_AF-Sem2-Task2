# KickOff Connect - Phase 1 Skeleton
# A minimal Flask app to verify the project structure works.

from flask import Flask, render_template

# Create a Flask application instance
app = Flask(__name__)

# Global variable for site name: Used in templates
siteName = "KickOff Connect"

@app.context_processor
def inject_site_name():
    return dict(siteName=siteName)


# Routes Definition
#===================
# Home Page
@app.route('/')
def index():
    return render_template('index.html', title="Welcome")


# Run application
if __name__ == '__main__':
    print("Starting KickOff Connect...")
    print("Open Your Application in Your Browser: http://localhost:81")
    app.run(host='0.0.0.0', port=81, debug=True)