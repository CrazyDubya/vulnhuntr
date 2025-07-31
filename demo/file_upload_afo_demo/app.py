"""
File Upload Arbitrary File Overwrite (AFO) Demo Application

This application contains intentional file upload vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Path traversal in uploaded file names
2. Unrestricted file type uploads
3. Executable file uploads
4. Archive extraction without path validation (Zip Slip)
5. Symlink attacks in file uploads
6. Overwriting system files
7. Race conditions in file operations
"""

from flask import Flask, request, jsonify, render_template_string, send_file, abort
import os
import shutil
import zipfile
import tarfile
import tempfile
import logging
import mimetypes
import subprocess
from pathlib import Path
from werkzeug.utils import secure_filename
import hashlib
import time
import json
from datetime import datetime
import threading

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Upload directories
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads'
SAFE_UPLOAD_DIR = BASE_DIR / 'safe_uploads'
EXTRACT_DIR = BASE_DIR / 'extracted'

# Create directories
for directory in [UPLOAD_DIR, SAFE_UPLOAD_DIR, EXTRACT_DIR]:
    directory.mkdir(exist_ok=True)

# Create some sensitive files to demonstrate AFO
SENSITIVE_DIR = BASE_DIR / 'sensitive'
SENSITIVE_DIR.mkdir(exist_ok=True)

# Create demo sensitive files
(SENSITIVE_DIR / 'config.ini').write_text('[database]\npassword=super_secret_db_password\napi_key=sk-secret123')
(SENSITIVE_DIR / 'admin_key.txt').write_text('admin_secret_key_12345')
(SENSITIVE_DIR / 'users.json').write_text('{"admin": {"password": "admin123", "role": "administrator"}}')

@app.route('/')
def index():
    """Main page with file upload demos"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>File Upload AFO Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .upload-form { border: 1px solid #ccc; padding: 20px; margin: 20px 0; }
            .vulnerability { background: #ffe6e6; padding: 10px; margin: 10px 0; }
            .payload { background: #f0f0f0; padding: 5px; margin: 5px 0; font-family: monospace; }
            .warning { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>📁 File Upload AFO Vulnerability Demo</h1>
        <p class="warning">⚠️ WARNING: This application contains intentional security vulnerabilities!</p>
        
        <h2>Vulnerable Upload Endpoints:</h2>
        
        <div class="upload-form">
            <h3>1. Basic File Upload (Path Traversal)</h3>
            <form action="/upload_basic" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required>
                <input type="text" name="filename" placeholder="Custom filename (optional)">
                <input type="submit" value="Upload">
            </form>
            <div class="vulnerability">
                <strong>Vulnerability:</strong> No path validation allows overwriting arbitrary files
                <div class="payload">Try filename: ../../../sensitive/config.ini</div>
            </div>
        </div>
        
        <div class="upload-form">
            <h3>2. Archive Extraction (Zip Slip)</h3>
            <form action="/extract_archive" method="post" enctype="multipart/form-data">
                <input type="file" name="archive" accept=".zip,.tar,.tar.gz" required>
                <input type="submit" value="Extract Archive">
            </form>
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Archive extraction without path validation
                <div class="payload">Create zip with: ../../../sensitive/overwritten.txt</div>
            </div>
        </div>
        
        <div class="upload-form">
            <h3>3. Image Upload with Resize</h3>
            <form action="/upload_image" method="post" enctype="multipart/form-data">
                <input type="file" name="image" accept="image/*" required>
                <input type="text" name="output_path" placeholder="Output path" value="resized_image.jpg">
                <input type="submit" value="Upload & Resize">
            </form>
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Output path allows arbitrary file overwrite
                <div class="payload">Try output_path: ../sensitive/users.json</div>
            </div>
        </div>
        
        <div class="upload-form">
            <h3>4. Document Converter</h3>
            <form action="/convert_document" method="post" enctype="multipart/form-data">
                <input type="file" name="document" required>
                <select name="output_format">
                    <option value="pdf">PDF</option>
                    <option value="txt">Text</option>
                    <option value="html">HTML</option>
                </select>
                <input type="text" name="output_name" placeholder="Output filename">
                <input type="submit" value="Convert">
            </form>
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Output filename allows path traversal
                <div class="payload">Try output_name: ../../sensitive/admin_key.txt</div>
            </div>
        </div>
        
        <div class="upload-form">
            <h3>5. Backup Upload</h3>
            <form action="/upload_backup" method="post" enctype="multipart/form-data">
                <input type="file" name="backup_file" required>
                <input type="text" name="restore_path" placeholder="Restore to path" value="/tmp/restore/">
                <input type="submit" value="Upload Backup">
            </form>
            <div class="vulnerability">
                <strong>Vulnerability:</strong> Backup restoration allows arbitrary file placement
                <div class="payload">Try restore_path: /tmp/../sensitive/</div>
            </div>
        </div>

        <h2>Test Payloads:</h2>
        <h3>Path Traversal Filenames:</h3>
        <div class="payload">../../../etc/passwd</div>
        <div class="payload">..\\..\\..\\windows\\system32\\drivers\\etc\\hosts</div>
        <div class="payload">....//....//....//sensitive/config.ini</div>
        <div class="payload">%2e%2e%2f%2e%2e%2f%2e%2e%2fsensitive/users.json</div>
        
        <h3>Dangerous File Types:</h3>
        <div class="payload">malicious.php (executable)</div>
        <div class="payload">shell.jsp (executable)</div>
        <div class="payload">backdoor.py (executable)</div>
        <div class="payload">virus.exe (executable)</div>
        
        <h3>Archive Zip Slip:</h3>
        <div class="payload">Create zip containing: ../../../sensitive/overwritten.txt</div>
        <div class="payload">Symlink pointing to: /etc/passwd</div>
        
        <h2>Uploaded Files:</h2>
        <a href="/list_uploads">View Uploaded Files</a>
    </body>
    </html>
    """)

@app.route('/upload_basic', methods=['POST'])
def vulnerable_basic_upload():
    """
    VULNERABILITY 1: Basic file upload with path traversal
    User can specify filename to overwrite arbitrary files
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'})
    
    file = request.files['file']
    custom_filename = request.form.get('filename')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    # Use custom filename if provided, otherwise use original
    filename = custom_filename if custom_filename else file.filename
    
    # VULNERABLE: No path validation or sanitization
    file_path = UPLOAD_DIR / filename
    
    logger.warning(f"Uploading file to potentially dangerous path: {file_path}")
    
    try:
        # VULNERABLE: Create directories if they don't exist (path traversal)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # VULNERABLE: Save file without validation
        file.save(str(file_path))
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'vulnerability': 'No path validation allows arbitrary file overwrite'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'filename': filename,
            'error': str(e),
            'vulnerability': 'File operation failed but path traversal was attempted'
        })

@app.route('/extract_archive', methods=['POST'])
def vulnerable_archive_extraction():
    """
    VULNERABILITY 2: Archive extraction without path validation (Zip Slip)
    Allows overwriting files outside the extraction directory
    """
    if 'archive' not in request.files:
        return jsonify({'error': 'No archive file provided'})
    
    archive_file = request.files['archive']
    
    if archive_file.filename == '':
        return jsonify({'error': 'No archive selected'})
    
    # Save uploaded archive temporarily
    temp_archive_path = UPLOAD_DIR / f"temp_archive_{int(time.time())}_{archive_file.filename}"
    archive_file.save(str(temp_archive_path))
    
    extracted_files = []
    
    logger.warning(f"Extracting archive without path validation: {archive_file.filename}")
    
    try:
        if archive_file.filename.endswith('.zip'):
            # VULNERABLE: Zip extraction without path validation
            with zipfile.ZipFile(str(temp_archive_path), 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # VULNERABLE: No path validation
                    extract_path = EXTRACT_DIR / member
                    
                    # Create parent directories
                    extract_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Extract file
                    with zip_ref.open(member) as source, open(extract_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    extracted_files.append({
                        'archive_path': member,
                        'extracted_to': str(extract_path),
                        'size': extract_path.stat().st_size
                    })
        
        elif archive_file.filename.endswith(('.tar', '.tar.gz', '.tgz')):
            # VULNERABLE: Tar extraction without path validation
            mode = 'r:gz' if archive_file.filename.endswith(('.tar.gz', '.tgz')) else 'r'
            
            with tarfile.open(str(temp_archive_path), mode) as tar_ref:
                for member in tar_ref.getmembers():
                    if member.isfile():
                        # VULNERABLE: No path validation
                        extract_path = EXTRACT_DIR / member.name
                        
                        # Create parent directories
                        extract_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Extract file
                        with tar_ref.extractfile(member) as source, open(extract_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        extracted_files.append({
                            'archive_path': member.name,
                            'extracted_to': str(extract_path),
                            'size': extract_path.stat().st_size
                        })
        
        else:
            return jsonify({'error': 'Unsupported archive format'})
        
        # Clean up temporary archive
        temp_archive_path.unlink()
        
        return jsonify({
            'success': True,
            'archive_filename': archive_file.filename,
            'extracted_files': extracted_files,
            'total_files': len(extracted_files),
            'vulnerability': 'Archive extraction allows Zip Slip attacks'
        })
    
    except Exception as e:
        # Clean up on error
        if temp_archive_path.exists():
            temp_archive_path.unlink()
        
        return jsonify({
            'success': False,
            'archive_filename': archive_file.filename,
            'error': str(e),
            'vulnerability': 'Archive extraction failed but path traversal was attempted'
        })

@app.route('/upload_image', methods=['POST'])
def vulnerable_image_upload():
    """
    VULNERABILITY 3: Image upload with arbitrary output path
    Allows overwriting files through output path parameter
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'})
    
    image_file = request.files['image']
    output_path = request.form.get('output_path', 'resized_image.jpg')
    
    if image_file.filename == '':
        return jsonify({'error': 'No image selected'})
    
    # Save uploaded image temporarily
    temp_image_path = UPLOAD_DIR / f"temp_image_{int(time.time())}_{image_file.filename}"
    image_file.save(str(temp_image_path))
    
    # VULNERABLE: User controls output path
    final_output_path = UPLOAD_DIR / output_path
    
    logger.warning(f"Processing image with user-controlled output path: {final_output_path}")
    
    try:
        # VULNERABLE: Create directories for output path
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simulate image processing (just copy the file for demo)
        shutil.copy2(str(temp_image_path), str(final_output_path))
        
        # Clean up temporary file
        temp_image_path.unlink()
        
        return jsonify({
            'success': True,
            'original_filename': image_file.filename,
            'output_path': str(final_output_path),
            'file_size': final_output_path.stat().st_size,
            'vulnerability': 'Output path allows arbitrary file overwrite'
        })
    
    except Exception as e:
        # Clean up on error
        if temp_image_path.exists():
            temp_image_path.unlink()
        
        return jsonify({
            'success': False,
            'original_filename': image_file.filename,
            'output_path': output_path,
            'error': str(e),
            'vulnerability': 'Image processing failed but arbitrary path was attempted'
        })

@app.route('/convert_document', methods=['POST'])
def vulnerable_document_converter():
    """
    VULNERABILITY 4: Document converter with path traversal in output filename
    Allows overwriting arbitrary files through conversion output
    """
    if 'document' not in request.files:
        return jsonify({'error': 'No document file provided'})
    
    document_file = request.files['document']
    output_format = request.form.get('output_format', 'txt')
    output_name = request.form.get('output_name')
    
    if document_file.filename == '':
        return jsonify({'error': 'No document selected'})
    
    # Generate output filename
    if output_name:
        # VULNERABLE: User controls output filename
        output_filename = f"{output_name}.{output_format}"
    else:
        base_name = os.path.splitext(document_file.filename)[0]
        output_filename = f"{base_name}_converted.{output_format}"
    
    # Save uploaded document temporarily
    temp_doc_path = UPLOAD_DIR / f"temp_doc_{int(time.time())}_{document_file.filename}"
    document_file.save(str(temp_doc_path))
    
    # VULNERABLE: Output path with user input
    output_path = UPLOAD_DIR / output_filename
    
    logger.warning(f"Converting document with user-controlled output: {output_path}")
    
    try:
        # VULNERABLE: Create directories for output path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simulate document conversion
        content = temp_doc_path.read_bytes()
        
        if output_format == 'txt':
            # Convert to text (simplified)
            converted_content = f"Converted document: {document_file.filename}\nContent length: {len(content)} bytes\nConverted at: {datetime.now()}"
        elif output_format == 'html':
            # Convert to HTML (simplified)
            converted_content = f"<html><body><h1>Converted Document</h1><p>Original: {document_file.filename}</p><p>Size: {len(content)} bytes</p></body></html>"
        else:  # pdf
            # Simulate PDF conversion
            converted_content = f"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n% Converted from {document_file.filename}"
        
        # VULNERABLE: Write to user-controlled path
        output_path.write_text(converted_content)
        
        # Clean up temporary file
        temp_doc_path.unlink()
        
        return jsonify({
            'success': True,
            'original_filename': document_file.filename,
            'output_format': output_format,
            'output_path': str(output_path),
            'output_size': len(converted_content),
            'vulnerability': 'Output filename allows path traversal attacks'
        })
    
    except Exception as e:
        # Clean up on error
        if temp_doc_path.exists():
            temp_doc_path.unlink()
        
        return jsonify({
            'success': False,
            'original_filename': document_file.filename,
            'output_filename': output_filename,
            'error': str(e),
            'vulnerability': 'Document conversion failed but path traversal was attempted'
        })

@app.route('/upload_backup', methods=['POST'])
def vulnerable_backup_upload():
    """
    VULNERABILITY 5: Backup upload with arbitrary restore path
    Allows placing files in arbitrary locations through restore path
    """
    if 'backup_file' not in request.files:
        return jsonify({'error': 'No backup file provided'})
    
    backup_file = request.files['backup_file']
    restore_path = request.form.get('restore_path', '/tmp/restore/')
    
    if backup_file.filename == '':
        return jsonify({'error': 'No backup file selected'})
    
    # VULNERABLE: User controls restore path
    restore_dir = Path(restore_path)
    
    logger.warning(f"Uploading backup to user-controlled path: {restore_dir}")
    
    try:
        # VULNERABLE: Create restore directory
        restore_dir.mkdir(parents=True, exist_ok=True)
        
        # VULNERABLE: Save backup file to user-controlled location
        backup_path = restore_dir / backup_file.filename
        backup_file.save(str(backup_path))
        
        # Simulate backup verification
        file_hash = hashlib.md5(backup_path.read_bytes()).hexdigest()
        
        return jsonify({
            'success': True,
            'backup_filename': backup_file.filename,
            'restore_path': str(restore_dir),
            'backup_file_path': str(backup_path),
            'file_size': backup_path.stat().st_size,
            'file_hash': file_hash,
            'vulnerability': 'Restore path allows arbitrary file placement'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'backup_filename': backup_file.filename,
            'restore_path': restore_path,
            'error': str(e),
            'vulnerability': 'Backup upload failed but arbitrary path was attempted'
        })

@app.route('/upload_executable', methods=['POST'])
def vulnerable_executable_upload():
    """
    VULNERABILITY 6: Executable file upload without restrictions
    Allows uploading and potentially executing dangerous files
    """
    if 'executable' not in request.files:
        return jsonify({'error': 'No executable file provided'})
    
    executable_file = request.files['executable']
    auto_execute = request.form.get('auto_execute', 'false').lower() == 'true'
    
    if executable_file.filename == '':
        return jsonify({'error': 'No executable selected'})
    
    # VULNERABLE: No file type restrictions
    executable_path = UPLOAD_DIR / executable_file.filename
    
    logger.warning(f"Uploading potentially dangerous executable: {executable_path}")
    
    try:
        # VULNERABLE: Save executable file without validation
        executable_file.save(str(executable_path))
        
        # Make file executable
        os.chmod(str(executable_path), 0o755)
        
        result = {
            'success': True,
            'executable_filename': executable_file.filename,
            'executable_path': str(executable_path),
            'file_size': executable_path.stat().st_size,
            'permissions': oct(executable_path.stat().st_mode)[-3:],
            'vulnerability': 'No restrictions on executable file uploads'
        }
        
        if auto_execute:
            # VULNERABLE: Auto-execute uploaded files
            try:
                execution_result = subprocess.run(
                    [str(executable_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                result['execution'] = {
                    'returncode': execution_result.returncode,
                    'stdout': execution_result.stdout,
                    'stderr': execution_result.stderr
                }
            except subprocess.TimeoutExpired:
                result['execution'] = {'error': 'Execution timed out'}
            except Exception as e:
                result['execution'] = {'error': str(e)}
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'executable_filename': executable_file.filename,
            'error': str(e),
            'vulnerability': 'Executable upload failed but dangerous file was processed'
        })

@app.route('/list_uploads')
def list_uploaded_files():
    """List all uploaded files"""
    uploaded_files = []
    
    for directory in [UPLOAD_DIR, EXTRACT_DIR]:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    uploaded_files.append({
                        'filename': file_path.name,
                        'path': str(file_path.relative_to(BASE_DIR)),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except:
                    pass
    
    return jsonify({
        'uploaded_files': uploaded_files,
        'total_files': len(uploaded_files)
    })

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download uploaded files (vulnerable to path traversal)"""
    try:
        # VULNERABLE: No path validation for downloads
        file_path = UPLOAD_DIR / filename
        
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            abort(404)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("📁 File Upload AFO Demo Application")
    print("===================================")
    print("Starting server on http://0.0.0.0:8003")
    print("")
    print("Test scenarios:")
    print("1. Upload file with path traversal: ../../../sensitive/config.ini")
    print("2. Create malicious zip with Zip Slip vulnerability")
    print("3. Upload executable files (.py, .sh, .exe)")
    print("4. Use path traversal in output paths for converters")
    print("")
    print("⚠️  This demo creates vulnerable file operations!")
    
    app.run(debug=True, host='0.0.0.0', port=8003)