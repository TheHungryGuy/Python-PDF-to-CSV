import os
from converter import convert_PDF_to_CSV
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
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
            
            # Convert PDF to CSV
            try:
                csv_filename = convert_PDF_to_CSV(file_path)
                flash(f'File converted to CSV: {csv_filename}')
            except Exception as e:
                flash(f'Error converting file: {str(e)}')
            
            # Clean up the uploaded PDF file
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} deleted successfully")
            else:
                print(f"File {file_path} does not exist")
                
            return redirect(url_for("index"))
        else:
            flash("Invalid file type. Only PDF files are allowed.")
    
    # Get list of CSV files (not PDFs since we delete them after conversion)
    csv_files = []
    if os.path.exists(UPLOAD_FOLDER):
        csv_files = [
            f
            for f in os.listdir(UPLOAD_FOLDER)
            if os.path.isfile(os.path.join(UPLOAD_FOLDER, f)) and f.endswith('.csv')
        ]

    return render_template("index.html", uploaded_files=csv_files)

@app.route('/download/<filename>')
def download_file(filename):
    """Route to download converted CSV files"""
    try:
        # Security check to prevent directory traversal
        safe_filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            flash('File not found.')
            return redirect(url_for('index'))
            
        return send_file(file_path, as_attachment=True, download_name=safe_filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)