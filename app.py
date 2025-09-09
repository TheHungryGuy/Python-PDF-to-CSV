import os
from converter import convert_PDF_to_CSV
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, abort
from werkzeug.utils import secure_filename
from io import BytesIO, StringIO
import uuid
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  

# Configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    session.permanent = True
    
    if request.method == "POST":
        # Check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url), 400  
        
        files = request.files.getlist("file")  # Get list of files
        
        # If user does not select file, browser might submit an empty part
        if not files or all(file.filename == '' for file in files):
            flash("No files selected")
            return redirect(request.url), 400  
        
        successful_conversions = 0
        converted_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                try:
                    # Read file content into memory
                    file_bytes = file.read()
                    
                    # Check if file is empty
                    if len(file_bytes) == 0:
                        flash(f"Uploaded file '{file.filename}' is empty")
                        continue
                    
                    original_filename = file.filename
                    
                    # Convert PDF to CSV in memory
                    csv_data, base_filename = convert_PDF_to_CSV(file_bytes, original_filename)
                    
                    # Store file info for session
                    converted_files.append({
                        'csv_data': csv_data,
                        'filename': f"{base_filename}.csv",
                        'original_name': original_filename
                    })
                    
                    successful_conversions += 1
                    
                except Exception as e:
                    flash(f'Error converting file "{file.filename}": {str(e)}')
        
        if successful_conversions > 0:
            # Store all converted files in session
            session['converted_files'] = converted_files
            flash(f'Successfully converted {successful_conversions} file(s)! Ready for download.')
        
        return redirect(url_for("index"))
    
    # Check if we have converted files ready
    converted_files = session.get('converted_files', [])
    return render_template("index.html", converted_files=converted_files)

@app.route('/download/<int:file_index>')
def download_file(file_index):
    """Route to download individual converted CSV files"""
    try:
        converted_files = session.get('converted_files', [])
        if not converted_files or file_index >= len(converted_files):
            flash('File not found. Session Expired. Please upload files.')
            return redirect(url_for('index'))
        
        file_data = converted_files[file_index]
        csv_buffer = BytesIO()
        csv_buffer.write(file_data['csv_data'].encode('utf-8'))
        csv_buffer.seek(0)
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=file_data['filename'],
            mimetype='text/csv',
        )
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index')), 500

@app.route('/clear')
def clear_session():
    """Clear the converted files from session and refresh the page"""
    session.pop('converted_files', None)
    flash('Session cleared. You can upload new files.')
    return redirect(url_for('index'))  

@app.errorhandler(404)
def not_found_error(error):
    flash('The requested resource was not found.')
    return redirect(url_for('index')), 404

@app.errorhandler(500)
def internal_error(error):
    flash('An internal server error occurred. Please try again.')
    return redirect(url_for('index')), 500

@app.errorhandler(413)
def too_large(error):
    flash('File too large. Maximum size is 16MB.')
    return redirect(url_for('index')), 413

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)