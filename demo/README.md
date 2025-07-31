# Vulnhuntr Demo Suite

This directory contains a comprehensive demonstration of vulnhuntr's vulnerability detection capabilities, optimized for Mac Studio M2 and latest macOS versions.

## Demo Applications

Each subdirectory contains intentionally vulnerable Python applications that demonstrate different vulnerability classes:

- `flask_lfi_demo/` - Local File Inclusion vulnerabilities in Flask applications
- `fastapi_rce_demo/` - Remote Code Execution vulnerabilities in FastAPI applications  
- `django_sqli_demo/` - SQL Injection vulnerabilities in Django applications
- `gradio_xss_demo/` - Cross-Site Scripting vulnerabilities in Gradio applications
- `aiohttp_ssrf_demo/` - Server-Side Request Forgery vulnerabilities in aiohttp applications
- `file_upload_afo_demo/` - Arbitrary File Overwrite vulnerabilities in file upload handlers
- `api_idor_demo/` - Insecure Direct Object Reference vulnerabilities in REST APIs

## Running the Demo

1. **Setup Environment (Mac Studio M2 Optimized)**:
   ```bash
   # Use the Mac-optimized setup script
   ./scripts/setup_mac_studio.sh
   ```

2. **Run Individual Demos**:
   ```bash
   # Analyze specific vulnerability type
   python -m vulnhuntr -r demo/flask_lfi_demo/ -l claude -v
   ```

3. **Run Complete Demo Suite**:
   ```bash
   # Run comprehensive demo showing all vulnerability types
   ./scripts/run_comprehensive_demo.sh
   ```

4. **Generate Demo Report**:
   ```bash
   # Create visual demo report with screenshots and analysis
   python demo/generate_demo_report.py
   ```

## Mac Studio M2 Optimizations

- ARM64 native dependencies
- Optimized Python environment setup
- Enhanced performance configurations
- Metal acceleration where applicable
- macOS-specific security considerations

## Demo Features

- **Interactive Analysis**: Step-by-step vulnerability discovery
- **Visual Reports**: Rich HTML reports with code highlighting
- **Performance Metrics**: Timing and resource usage statistics
- **False Positive Testing**: Examples of secure code patterns
- **Multi-LLM Comparison**: Side-by-side analysis using different LLMs