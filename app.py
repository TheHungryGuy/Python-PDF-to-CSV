import os
from converter import convert_PDF_to_CSV
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from werkzeug.utils import secure_filename
from io import BytesIO, StringIO
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this for production

# Configuration
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 128 * 1024 * 1024  # 128MB
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

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
            try:
                # Read file content into memory
                file_bytes = file.read()
                original_filename = file.filename
                
                # Convert PDF to CSV in memory
                csv_data, base_filename = convert_PDF_to_CSV(file_bytes, original_filename)
                
                # Store in session for download
                session['converted_file'] = {
                    'csv_data': csv_data,
                    'filename': f"{base_filename}.csv"
                }
                
                flash(f'File "{original_filename}" converted successfully! Ready for download.')
                
            except Exception as e:
                flash(f'Error converting file: {str(e)}')
            
            return redirect(url_for("index"))
        else:
            flash("Invalid file type. Only PDF files are allowed.")
    
    # Check if we have a converted file ready
    converted_file = session.get('converted_file')
    return render_template("index.html", has_file=converted_file is not None)

@app.route('/download')
def download_file():
    """Route to download converted CSV from session"""
    try:
        converted_file = session.get('converted_file')
        if not converted_file:
            flash('No file found to download. Please upload a file first.')
            return redirect(url_for('index'))
            
        # Create in-memory file from session data
        csv_data = converted_file['csv_data']
        filename = converted_file['filename']
        
        # Create BytesIO object (not StringIO) and send as file
        csv_buffer = BytesIO()
        csv_buffer.write(csv_data.encode('utf-8'))  # Encode string to bytes
        csv_buffer.seek(0)
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv',
            
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/clear')
def clear_session():
    """Clear the converted file from session"""
    session.pop('converted_file', None)
    flash('Session cleared. You can upload a new file.')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)