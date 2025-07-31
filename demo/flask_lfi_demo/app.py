"""
Flask Local File Inclusion (LFI) Demo Application

This application contains intentional LFI vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Direct file path inclusion from user input
2. Path traversal via URL parameters
3. Template file inclusion without sanitization
4. Configuration file exposure
"""

from flask import Flask, request, render_template_string, send_file, jsonify, abort
import os
import logging
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'demo_secret_key_unsafe'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo data directory
DEMO_DATA_DIR = Path(__file__).parent / 'data'
DEMO_DATA_DIR.mkdir(exist_ok=True)

# Create some demo files for testing
def setup_demo_files():
    """Create demo files for LFI testing"""
    # Public files that should be accessible
    public_dir = DEMO_DATA_DIR / 'public'
    public_dir.mkdir(exist_ok=True)
    
    (public_dir / 'welcome.txt').write_text('Welcome to our demo application!')
    (public_dir / 'help.txt').write_text('This is the help documentation.')
    
    # Sensitive files that should NOT be accessible
    sensitive_dir = DEMO_DATA_DIR / 'sensitive'
    sensitive_dir.mkdir(exist_ok=True)
    
    (sensitive_dir / 'config.ini').write_text('[database]\npassword=super_secret_password\napi_key=sk-1234567890abcdef')
    (sensitive_dir / 'users.txt').write_text('admin:admin_password\nuser1:password123')
    (sensitive_dir / 'private_key.pem').write_text('-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhki...\n-----END PRIVATE KEY-----')

setup_demo_files()

@app.route('/')
def index():
    """Main page with navigation to vulnerable endpoints"""
    return '''
    <h1>Flask LFI Demo Application</h1>
    <p>This application demonstrates Local File Inclusion vulnerabilities.</p>
    <h2>Vulnerable Endpoints:</h2>
    <ul>
        <li><a href="/read_file?file=welcome.txt">Read File (Basic LFI)</a></li>
        <li><a href="/view_template?template=user_profile">View Template (Template LFI)</a></li>
        <li><a href="/download?filename=help.txt">Download File (Path Traversal)</a></li>
        <li><a href="/config?section=app">Config Reader (Config Exposure)</a></li>
        <li><a href="/logs?date=2024-01-01">Log Viewer (Log File LFI)</a></li>
    </ul>
    <h2>Test Payloads:</h2>
    <ul>
        <li><code>../sensitive/config.ini</code></li>
        <li><code>../../etc/passwd</code></li>
        <li><code>../../../proc/self/environ</code></li>
    </ul>
    '''

@app.route('/read_file')
def read_file():
    """
    VULNERABILITY 1: Direct file inclusion without sanitization
    User input directly used in file path construction
    """
    filename = request.args.get('file', 'welcome.txt')
    
    # VULNERABLE: No path sanitization or validation
    file_path = os.path.join(DEMO_DATA_DIR, 'public', filename)
    
    try:
        # VULNERABLE: Could read any file on the system
        with open(file_path, 'r') as f:
            content = f.read()
        
        logger.info(f"File read: {file_path}")
        return f'<h2>File Content:</h2><pre>{content}</pre>'
    
    except FileNotFoundError:
        return f'File not found: {filename}', 404
    except Exception as e:
        return f'Error reading file: {str(e)}', 500

@app.route('/view_template')
def view_template():
    """
    VULNERABILITY 2: Template file inclusion with path traversal
    User-controlled template path without proper validation
    """
    template_name = request.args.get('template', 'default')
    
    # VULNERABLE: Template path construction allows traversal
    template_path = f"templates/{template_name}.html"
    
    try:
        # VULNERABLE: Could include any file as template
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Render the template (potential for template injection too)
        return render_template_string(template_content)
    
    except FileNotFoundError:
        # Fallback template with user input (XSS opportunity)
        fallback_template = f"""
        <h1>Template not found: {template_name}</h1>
        <p>Available templates: user_profile, admin_panel</p>
        """
        return render_template_string(fallback_template)

@app.route('/download')
def download_file():
    """
    VULNERABILITY 3: File download with insufficient path validation
    Allows downloading files outside intended directory
    """
    filename = request.args.get('filename', '')
    
    if not filename:
        return 'Filename parameter required', 400
    
    # VULNERABLE: Basic attempt at security but bypassable
    if '..' in filename or filename.startswith('/'):
        # Weak validation - can be bypassed with encoding or other techniques
        return 'Invalid filename', 400
    
    # VULNERABLE: Still allows access to files in subdirectories
    file_path = os.path.join(DEMO_DATA_DIR, filename)
    
    try:
        # Check if file exists and send it
        if os.path.isfile(file_path):
            return send_file(file_path)
        else:
            return 'File not found', 404
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/config')
def read_config():
    """
    VULNERABILITY 4: Configuration file exposure
    User can specify which config section to read
    """
    section = request.args.get('section', 'app')
    config_file = request.args.get('config_file', 'app.conf')
    
    # VULNERABLE: User controls both config file and section
    config_path = os.path.join(DEMO_DATA_DIR, config_file)
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Return the entire config file (should filter by section)
        return f'<h2>Configuration [{section}]:</h2><pre>{content}</pre>'
    
    except FileNotFoundError:
        # Attempt to read from system directories
        system_config_path = f'/etc/{config_file}'
        try:
            with open(system_config_path, 'r') as f:
                content = f.read()
            return f'<h2>System Configuration:</h2><pre>{content}</pre>'
        except:
            return f'Configuration file not found: {config_file}', 404

@app.route('/logs')
def view_logs():
    """
    VULNERABILITY 5: Log file inclusion based on user input
    Date parameter used to construct log file path
    """
    date = request.args.get('date', '2024-01-01')
    log_type = request.args.get('type', 'app')
    
    # VULNERABLE: User input directly used in file path
    log_filename = f"{log_type}_{date}.log"
    log_path = os.path.join('/var/log', log_filename)
    
    # Also try application log directory
    app_log_path = os.path.join(DEMO_DATA_DIR, 'logs', log_filename)
    
    try:
        # Try app logs first
        with open(app_log_path, 'r') as f:
            content = f.read()
        source = 'Application Logs'
    except FileNotFoundError:
        try:
            # VULNERABLE: Try system logs
            with open(log_path, 'r') as f:
                content = f.read()
            source = 'System Logs'
        except FileNotFoundError:
            return f'Log file not found for date: {date}', 404
        except PermissionError:
            return f'Permission denied accessing logs for: {date}', 403
    
    return f'<h2>{source} - {date}</h2><pre>{content[:1000]}...</pre>'

@app.route('/include_file')
def include_file():
    """
    VULNERABILITY 6: File inclusion via POST data
    Demonstrates LFI through different HTTP methods and parameters
    """
    if request.method == 'POST':
        file_to_include = request.form.get('include_path')
    else:
        file_to_include = request.args.get('path')
    
    if not file_to_include:
        return '''
        <form method="post">
            <label>File to include:</label><br>
            <input type="text" name="include_path" placeholder="path/to/file"><br>
            <input type="submit" value="Include File">
        </form>
        '''
    
    # VULNERABLE: Direct file inclusion
    try:
        with open(file_to_include, 'r') as f:
            content = f.read()
        return f'<h2>Included File:</h2><pre>{content}</pre>'
    except Exception as e:
        return f'Error including file: {str(e)}', 500

@app.route('/api/file')
def api_file_access():
    """
    VULNERABILITY 7: API endpoint with file path parameter
    JSON API that returns file contents
    """
    file_path = request.args.get('path')
    encoding = request.args.get('encoding', 'utf-8')
    
    if not file_path:
        return jsonify({'error': 'path parameter required'}), 400
    
    try:
        # VULNERABLE: No path validation in API endpoint
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'content': content,
            'size': len(content)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'file_path': file_path
        }), 500

if __name__ == '__main__':
    # Create demo log files
    log_dir = DEMO_DATA_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    (log_dir / 'app_2024-01-01.log').write_text('2024-01-01 12:00:00 INFO: Application started\n2024-01-01 12:01:00 DEBUG: User login attempt')
    
    # Run in debug mode for demo purposes
    app.run(debug=True, host='0.0.0.0', port=5000)