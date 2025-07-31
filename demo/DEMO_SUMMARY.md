# Vulnhuntr Demo Suite

This directory contains comprehensive demonstrations of vulnhuntr's vulnerability detection capabilities across various Python frameworks and vulnerability types.

## 📊 Overview

- **Total Applications**: 7
- **Vulnerability Types**: 7
- **Total Vulnerabilities**: 36
- **Lines of Code**: 3,453
- **Files Analyzed**: 7

## 🎯 Demo Applications

### ✅ Flask LFI Demo

**Vulnerability Type**: LFI  
**Port**: 5000  
**Directory**: `flask_lfi_demo/`

Demonstrates Local File Inclusion vulnerabilities in Flask applications through path traversal and unsafe file operations.

**Demonstrated Vulnerabilities**:
- Direct file path inclusion from user input
- Path traversal via URL parameters
- Template file inclusion without sanitization
- Configuration file exposure

**Test Commands**:
```bash
# Start the application
cd flask_lfi_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r flask_lfi_demo/ -l claude -v
```

### ✅ FastAPI RCE Demo

**Vulnerability Type**: RCE  
**Port**: 8000  
**Directory**: `fastapi_rce_demo/`

Showcases Remote Code Execution vulnerabilities through eval(), subprocess calls, and unsafe deserialization.

**Demonstrated Vulnerabilities**:
- Direct eval() of user input
- Subprocess execution with shell=True
- Dynamic import of user-specified modules
- Unsafe pickle deserialization
- Server-Side Template Injection (SSTI)
- YAML deserialization with unsafe loader

**Test Commands**:
```bash
# Start the application
cd fastapi_rce_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r fastapi_rce_demo/ -l claude -v
```

### ✅ Gradio XSS Demo

**Vulnerability Type**: XSS  
**Port**: 7860  
**Directory**: `gradio_xss_demo/`

Illustrates Cross-Site Scripting vulnerabilities in Gradio applications through unsafe HTML rendering.

**Demonstrated Vulnerabilities**:
- Reflected XSS in text input processing
- Stored XSS in file upload comments
- DOM-based XSS in dynamic content
- XSS in markdown rendering
- XSS through unsafe HTML sanitization

**Test Commands**:
```bash
# Start the application
cd gradio_xss_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r gradio_xss_demo/ -l claude -v
```

### ✅ Django SQLI Demo

**Vulnerability Type**: SQLI  
**Port**: 8001  
**Directory**: `django_sqli_demo/`

Demonstrates SQL Injection vulnerabilities in Django applications through raw queries and ORM bypasses.

**Demonstrated Vulnerabilities**:
- Raw SQL queries with string concatenation
- ORM bypasses with raw() method
- Custom SQL with user-controlled parameters
- UNION-based SQL injection
- Blind SQL injection vulnerabilities

**Test Commands**:
```bash
# Start the application
cd django_sqli_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r django_sqli_demo/ -l claude -v
```

### ✅ aiohttp SSRF Demo

**Vulnerability Type**: SSRF  
**Port**: 8002  
**Directory**: `aiohttp_ssrf_demo/`

Shows Server-Side Request Forgery vulnerabilities through unvalidated URL fetching and callback mechanisms.

**Demonstrated Vulnerabilities**:
- URL fetching without validation
- Internal service requests
- Webhook URL handling
- Image/file proxy functionality
- XML External Entity (XXE) processing
- Cloud metadata service access

**Test Commands**:
```bash
# Start the application
cd aiohttp_ssrf_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r aiohttp_ssrf_demo/ -l claude -v
```

### ✅ File Upload AFO Demo

**Vulnerability Type**: AFO  
**Port**: 8003  
**Directory**: `file_upload_afo_demo/`

Exhibits Arbitrary File Overwrite vulnerabilities through path traversal in file uploads and archive extraction.

**Demonstrated Vulnerabilities**:
- Path traversal in uploaded file names
- Unrestricted file type uploads
- Archive extraction without path validation (Zip Slip)
- Symlink attacks in file uploads
- Overwriting system files

**Test Commands**:
```bash
# Start the application
cd file_upload_afo_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r file_upload_afo_demo/ -l claude -v
```

### ✅ API IDOR Demo

**Vulnerability Type**: IDOR  
**Port**: 8004  
**Directory**: `api_idor_demo/`

Demonstrates Insecure Direct Object Reference vulnerabilities through missing authorization checks in API endpoints.

**Demonstrated Vulnerabilities**:
- Direct object access without authorization
- Predictable resource identifiers
- Missing access controls on API endpoints
- Privilege escalation through IDOR
- Information disclosure via enumeration

**Test Commands**:
```bash
# Start the application
cd api_idor_demo/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r api_idor_demo/ -l claude -v
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- vulnhuntr installed (`pipx install vulnhuntr`)
- API keys for Claude or OpenAI

### Run All Demos
```bash
# Interactive demo runner
./scripts/run_comprehensive_demo.sh

# Or run comprehensive analysis
./scripts/run_comprehensive_demo.sh comprehensive
```

### Run Individual Demos
```bash
# Start specific demo
cd <demo_directory>/
python3 app.py

# Analyze with vulnhuntr
vulnhuntr -r <demo_directory>/ -l claude -v
```

## 🔧 Demo Script Features

The `run_comprehensive_demo.sh` script provides:

- **Comprehensive Analysis**: Runs vulnhuntr against all demo applications
- **Individual Testing**: Start and test specific applications
- **Report Generation**: Creates detailed HTML and JSON reports
- **Service Management**: Automatically starts/stops demo services
- **Requirements Checking**: Validates environment setup

## 📈 Expected Results

Vulnhuntr should successfully identify:

- **Local File Inclusion (LFI)** vulnerabilities in Flask applications
- **Remote Code Execution (RCE)** flaws in FastAPI applications
- **Cross-Site Scripting (XSS)** issues in Gradio applications
- **SQL Injection (SQLI)** vulnerabilities in Django applications
- **Server-Side Request Forgery (SSRF)** in aiohttp applications
- **Arbitrary File Overwrite (AFO)** in file upload handlers
- **Insecure Direct Object Reference (IDOR)** in API endpoints

## ⚠️ Security Warning

**These applications contain intentional security vulnerabilities and should never be deployed in production environments.** They are designed solely for educational and testing purposes.

## 📚 Additional Resources

- [Vulnhuntr Documentation](https://github.com/protectai/vulnhuntr)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)
- [Vulnerability Testing Guide](https://owasp.org/www-community/Vulnerability_Scanning_Tools)

---

*Report generated on July 31, 2025*
