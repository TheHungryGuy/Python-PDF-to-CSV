import os
from converter import convert_PDF_to_CSV
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this for production

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 128 * 1024 * 1024  # 128MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If user does not select file, browser might submit an empty part
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            flash(f'File "{filename}" uploaded successfully!')
            convert_PDF_to_CSV(file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted successfully")
            else:
                print(f"File {file_path} does not exist")
            return redirect(url_for("index"))
        else:
            flash("Invalid file type. Only PDF files are allowed.")

    
    
    
    # Get list of uploaded files
    uploaded_files = []
    if os.path.exists(UPLOAD_FOLDER):
        uploaded_files = [
            f
            for f in os.listdir(UPLOAD_FOLDER)
            if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))
        ]

    return render_template("index.html", uploaded_files=uploaded_files)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
