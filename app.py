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
        
        file = request.files["file"]
        
        # If user does not select file, browser might submit an empty part
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url), 400  
        
        if file and allowed_file(file.filename):
            try:
                # read file into memory
                file_bytes = file.read()
                
                # check if the file is empty
                if len(file_bytes) == 0:
                    flash("Uploaded file is empty")
                    return redirect(request.url), 400  
                
                original_filename = file.filename
                
                # convert PDF to CSV in memory
                csv_data, base_filename = convert_PDF_to_CSV(file_bytes, original_filename)
                
                # store in session for download
                session['converted_file'] = {
                    'csv_data': csv_data,
                    'filename': f"{base_filename}.csv"
                }
                
                flash(f'File "{original_filename}" converted successfully! Ready for download.')
                
            except Exception as e:
                flash(f'Error converting file: {str(e)}')
                return redirect(request.url), 500  
            
            return redirect(url_for("index"))
        else:
            flash("Invalid file type. Only PDF files are allowed.")
            return redirect(request.url), 400  
    
    # check if we have a converted file ready and get the filename
    converted_file = session.get('converted_file')
    filename = converted_file['filename'] if converted_file else None
    return render_template("index.html", filename=filename)

@app.route('/download')
def download_file():
    """Route to download converted CSV from session"""
    try:
        converted_file = session.get('converted_file')
        if not converted_file:
            flash('No file found to download. Please upload a file first.')
            return redirect(url_for('index')), 404  
            
        # create an inmemory file from session data
        csv_data = converted_file['csv_data']
        filename = converted_file['filename']
        
        # turn object into file and send it
        csv_buffer = BytesIO()
        csv_buffer.write(csv_data.encode('utf-8'))  # encode string to bytes
        csv_buffer.seek(0)
        
        return send_file(
            csv_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv',
        )
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect(url_for('index')), 500  

@app.route('/clear')
def clear_session():
    """Clear the converted file from session"""
    session.pop('converted_file', None)
    flash('Session cleared. You can upload a new file.')
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