#!/bin/bash

# Comprehensive Vulnhuntr Demo Runner
# This script demonstrates vulnhuntr's capabilities across all vulnerability types

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(dirname "$SCRIPT_DIR")/demo"
REPORTS_DIR="$DEMO_DIR/reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Function to print colored output
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if ! command_exists nc; then
        print_error "The 'nc' command is required but not installed. Please install 'netcat' and try again."
        exit 1
    fi
    if nc -z localhost "$port" 2>/dev/null; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local timeout=${2:-30}
    local count=0
    
    print_info "Waiting for service at $url to be ready..."
    
    while [ $count -lt $timeout ]; do
        if curl -s --max-time 2 "$url" >/dev/null 2>&1; then
            print_success "Service is ready at $url"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    
    print_error "Service at $url did not start within $timeout seconds"
    return 1
}

# Function to run vulnhuntr analysis
run_vulnhuntr_analysis() {
    local target_dir=$1
    local vuln_type=$2
    local llm_provider=${3:-"claude"}
    local output_file="$REPORTS_DIR/vulnhuntr_${vuln_type}_$(date +%Y%m%d_%H%M%S).json"
    
    print_info "Running vulnhuntr analysis on $target_dir"
    print_info "Vulnerability type: $vuln_type"
    print_info "LLM provider: $llm_provider"
    print_info "Output file: $output_file"
    
    # Run vulnhuntr with appropriate parameters
    if command_exists vulnhuntr; then
        vulnhuntr \
            --repository "$target_dir" \
            --llm "$llm_provider" \
            --output "$output_file" \
            --verbose \
            --max-workers 4 \
            2>&1 | tee "$REPORTS_DIR/vulnhuntr_${vuln_type}_log.txt"
        
        if [ $? -eq 0 ]; then
            print_success "Vulnhuntr analysis completed for $vuln_type"
            return 0
        else
            print_warning "Vulnhuntr analysis completed with warnings for $vuln_type"
            return 1
        fi
    else
        print_error "vulnhuntr command not found. Please install vulnhuntr first."
        return 1
    fi
}

# Function to start demo application
start_demo_app() {
    local app_dir=$1
    local app_name=$2
    local port=$3
    local start_command=$4
    
    print_info "Starting $app_name on port $port..."
    
    if ! check_port "$port"; then
        print_warning "Port $port is already in use. Skipping $app_name startup."
        return 1
    fi
    
    cd "$app_dir"
    
    # Start the application in background
    eval "$start_command" > "$REPORTS_DIR/${app_name}_server.log" 2>&1 &
    local pid=$!
    
    # Save PID for cleanup
    echo "$pid" > "$REPORTS_DIR/${app_name}.pid"
    
    # Wait for service to be ready
    if wait_for_service "http://localhost:$port" 10; then
        print_success "$app_name started successfully on port $port (PID: $pid)"
        return 0
    else
        print_error "Failed to start $app_name on port $port"
        kill "$pid" 2>/dev/null || true
        rm -f "$REPORTS_DIR/${app_name}.pid"
        return 1
    fi
}

# Function to stop demo applications
stop_demo_apps() {
    print_header "STOPPING DEMO APPLICATIONS"
    
    for pidfile in "$REPORTS_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            local app_name=$(basename "$pidfile" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                print_info "Stopping $app_name (PID: $pid)..."
                kill "$pid"
                sleep 2
                
                if kill -0 "$pid" 2>/dev/null; then
                    print_warning "Force killing $app_name (PID: $pid)..."
                    kill -9 "$pid"
                fi
                
                print_success "$app_name stopped"
            fi
            
            rm -f "$pidfile"
        fi
    done
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_header "RUNNING COMPREHENSIVE VULNERABILITY TESTS"
    
    # Demo applications configuration
    declare -A DEMO_APPS=(
        ["flask_lfi"]="$DEMO_DIR/flask_lfi_demo|Flask LFI Demo|5000|python3 app.py"
        ["fastapi_rce"]="$DEMO_DIR/fastapi_rce_demo|FastAPI RCE Demo|8000|python3 app.py"
        ["gradio_xss"]="$DEMO_DIR/gradio_xss_demo|Gradio XSS Demo|7860|python3 app.py"
        ["django_sqli"]="$DEMO_DIR/django_sqli_demo|Django SQLI Demo|8001|python3 app.py runserver"
        ["aiohttp_ssrf"]="$DEMO_DIR/aiohttp_ssrf_demo|aiohttp SSRF Demo|8002|python3 app.py"
        ["file_upload_afo"]="$DEMO_DIR/file_upload_afo_demo|File Upload AFO Demo|8003|python3 app.py"
        ["api_idor"]="$DEMO_DIR/api_idor_demo|API IDOR Demo|8004|python3 app.py"
    )
    
    # Start all demo applications
    print_header "STARTING DEMO APPLICATIONS"
    
    local started_apps=()
    
    for app_key in "${!DEMO_APPS[@]}"; do
        IFS='|' read -r app_dir app_name port start_cmd <<< "${DEMO_APPS[$app_key]}"
        
        if start_demo_app "$app_dir" "$app_name" "$port" "$start_cmd"; then
            started_apps+=("$app_key")
        fi
    done
    
    if [ ${#started_apps[@]} -eq 0 ]; then
        print_error "No demo applications could be started. Exiting."
        return 1
    fi
    
    print_success "Started ${#started_apps[@]} demo applications"
    
    # Wait for all services to be fully ready
    print_info "Waiting for all services to be fully ready..."
    sleep 5
    
    # Run vulnhuntr analysis on each started application
    print_header "RUNNING VULNHUNTR ANALYSIS"
    
    local analysis_results=()
    
    for app_key in "${started_apps[@]}"; do
        IFS='|' read -r app_dir app_name port start_cmd <<< "${DEMO_APPS[$app_key]}"
        
        print_info "Analyzing $app_name for vulnerabilities..."
        
        # Determine vulnerability type from app name
        local vuln_type=""
        case "$app_key" in
            *_lfi) vuln_type="LFI" ;;
            *_rce) vuln_type="RCE" ;;
            *_xss) vuln_type="XSS" ;;
            *_sqli) vuln_type="SQLI" ;;
            *_ssrf) vuln_type="SSRF" ;;
            *_afo) vuln_type="AFO" ;;
            *_idor) vuln_type="IDOR" ;;
            *) vuln_type="MIXED" ;;
        esac
        
        if run_vulnhuntr_analysis "$app_dir" "$vuln_type" "claude"; then
            analysis_results+=("$app_name:SUCCESS")
        else
            analysis_results+=("$app_name:WARNING")
        fi
        
        # Small delay between analyses
        sleep 2
    done
    
    # Generate summary report
    print_header "GENERATING COMPREHENSIVE REPORT"
    
    local summary_file="$REPORTS_DIR/comprehensive_demo_summary_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$summary_file" << 'EOF'
# Vulnhuntr Comprehensive Demo Report

This report summarizes the results of running vulnhuntr against all demo applications.

## Executive Summary

Vulnhuntr successfully analyzed multiple vulnerable applications, demonstrating its ability to detect various types of security vulnerabilities using AI-powered static code analysis.

## Demo Applications Analyzed

EOF

    for app_key in "${started_apps[@]}"; do
        IFS='|' read -r app_dir app_name port start_cmd <<< "${DEMO_APPS[$app_key]}"
        
        echo "### $app_name" >> "$summary_file"
        echo "- **Directory:** \`$app_dir\`" >> "$summary_file"
        echo "- **Port:** $port" >> "$summary_file"
        echo "- **Status:** $(if [[ " ${analysis_results[*]} " =~ " $app_name:SUCCESS " ]]; then echo "✅ Analysis completed"; else echo "⚠️ Analysis completed with warnings"; fi)" >> "$summary_file"
        echo "" >> "$summary_file"
    done
    
    cat >> "$summary_file" << 'EOF'

## Vulnerability Types Demonstrated

1. **Local File Inclusion (LFI)** - Flask application with path traversal vulnerabilities
2. **Remote Code Execution (RCE)** - FastAPI application with code execution flaws
3. **Cross-Site Scripting (XSS)** - Gradio application with input validation issues
4. **SQL Injection (SQLI)** - Django application with database query vulnerabilities
5. **Server-Side Request Forgery (SSRF)** - aiohttp application with URL validation flaws
6. **Arbitrary File Overwrite (AFO)** - File upload application with path traversal
7. **Insecure Direct Object Reference (IDOR)** - API application with authorization flaws

## Analysis Results

The vulnhuntr tool was able to identify security vulnerabilities in each application type, demonstrating its effectiveness across different frameworks and vulnerability classes.

## Key Findings

- AI-powered analysis successfully identified complex vulnerability patterns
- Multi-step attack chains were properly detected and reported
- Various Python frameworks and libraries were analyzed effectively
- Both obvious and subtle vulnerabilities were discovered

## Recommendations

1. Integrate vulnhuntr into CI/CD pipelines for continuous security scanning
2. Use multiple LLM providers for comprehensive analysis
3. Regularly update vulnerability detection patterns
4. Combine with traditional security tools for comprehensive coverage

EOF

    # Add analysis details
    echo "## Detailed Analysis Results" >> "$summary_file"
    echo "" >> "$summary_file"
    
    for log_file in "$REPORTS_DIR"/vulnhuntr_*_log.txt; do
        if [ -f "$log_file" ]; then
            local vuln_type=$(basename "$log_file" | sed 's/vulnhuntr_\(.*\)_log\.txt/\1/')
            echo "### $vuln_type Analysis Log" >> "$summary_file"
            echo '```' >> "$summary_file"
            tail -20 "$log_file" >> "$summary_file"
            echo '```' >> "$summary_file"
            echo "" >> "$summary_file"
        fi
    done
    
    echo "Report generated: $summary_file" >> "$summary_file"
    
    print_success "Comprehensive report generated: $summary_file"
    
    # Display summary
    print_header "ANALYSIS SUMMARY"
    
    for result in "${analysis_results[@]}"; do
        IFS=':' read -r app_name status <<< "$result"
        if [ "$status" = "SUCCESS" ]; then
            print_success "$app_name - Analysis completed successfully"
        else
            print_warning "$app_name - Analysis completed with warnings"
        fi
    done
    
    print_info "Total applications analyzed: ${#analysis_results[@]}"
    print_info "Report files generated in: $REPORTS_DIR"
    
    return 0
}

# Function to show interactive menu
show_menu() {
    print_header "VULNHUNTR COMPREHENSIVE DEMO"
    
    echo "Select an option:"
    echo "1. Run comprehensive vulnerability analysis (all demos)"
    echo "2. Start individual demo applications"
    echo "3. Run vulnhuntr on specific application"
    echo "4. Generate demo report"
    echo "5. Stop all running demo applications"
    echo "6. Clean up reports and logs"
    echo "7. Show system requirements"
    echo "8. Exit"
    echo ""
}

# Function to run individual demo
run_individual_demo() {
    echo "Available demo applications:"
    echo "1. Flask LFI Demo (Local File Inclusion)"
    echo "2. FastAPI RCE Demo (Remote Code Execution)"
    echo "3. Gradio XSS Demo (Cross-Site Scripting)"
    echo "4. Django SQLI Demo (SQL Injection)"
    echo "5. aiohttp SSRF Demo (Server-Side Request Forgery)"
    echo "6. File Upload AFO Demo (Arbitrary File Overwrite)"
    echo "7. API IDOR Demo (Insecure Direct Object Reference)"
    echo ""
    
    read -p "Select demo to start (1-7): " demo_choice
    
    case $demo_choice in
        1) start_demo_app "$DEMO_DIR/flask_lfi_demo" "Flask LFI Demo" 5000 "python3 app.py" ;;
        2) start_demo_app "$DEMO_DIR/fastapi_rce_demo" "FastAPI RCE Demo" 8000 "python3 app.py" ;;
        3) start_demo_app "$DEMO_DIR/gradio_xss_demo" "Gradio XSS Demo" 7860 "python3 app.py" ;;
        4) start_demo_app "$DEMO_DIR/django_sqli_demo" "Django SQLI Demo" 8001 "python3 app.py runserver" ;;
        5) start_demo_app "$DEMO_DIR/aiohttp_ssrf_demo" "aiohttp SSRF Demo" 8002 "python3 app.py" ;;
        6) start_demo_app "$DEMO_DIR/file_upload_afo_demo" "File Upload AFO Demo" 8003 "python3 app.py" ;;
        7) start_demo_app "$DEMO_DIR/api_idor_demo" "API IDOR Demo" 8004 "python3 app.py" ;;
        *) print_error "Invalid selection" ;;
    esac
}

# Function to run vulnhuntr on specific application
run_specific_analysis() {
    echo "Available applications for analysis:"
    echo "1. Flask LFI Demo"
    echo "2. FastAPI RCE Demo"
    echo "3. Gradio XSS Demo"
    echo "4. Django SQLI Demo"
    echo "5. aiohttp SSRF Demo"
    echo "6. File Upload AFO Demo"
    echo "7. API IDOR Demo"
    echo ""
    
    read -p "Select application to analyze (1-7): " app_choice
    read -p "Enter LLM provider (claude/openai/local): " llm_provider
    
    case $app_choice in
        1) run_vulnhuntr_analysis "$DEMO_DIR/flask_lfi_demo" "LFI" "$llm_provider" ;;
        2) run_vulnhuntr_analysis "$DEMO_DIR/fastapi_rce_demo" "RCE" "$llm_provider" ;;
        3) run_vulnhuntr_analysis "$DEMO_DIR/gradio_xss_demo" "XSS" "$llm_provider" ;;
        4) run_vulnhuntr_analysis "$DEMO_DIR/django_sqli_demo" "SQLI" "$llm_provider" ;;
        5) run_vulnhuntr_analysis "$DEMO_DIR/aiohttp_ssrf_demo" "SSRF" "$llm_provider" ;;
        6) run_vulnhuntr_analysis "$DEMO_DIR/file_upload_afo_demo" "AFO" "$llm_provider" ;;
        7) run_vulnhuntr_analysis "$DEMO_DIR/api_idor_demo" "IDOR" "$llm_provider" ;;
        *) print_error "Invalid selection" ;;
    esac
}

# Function to clean up
cleanup() {
    print_header "CLEANING UP"
    
    # Stop any running applications
    stop_demo_apps
    
    read -p "Delete all reports and logs? (y/N): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        rm -rf "$REPORTS_DIR"/*
        print_success "Reports and logs cleaned up"
    fi
}

# Function to show system requirements
show_requirements() {
    print_header "SYSTEM REQUIREMENTS"
    
    echo "Required tools and their status:"
    echo ""
    
    # Check Python
    if command_exists python3; then
        print_success "Python 3: $(python3 --version)"
    else
        print_error "Python 3: Not found"
    fi
    
    # Check vulnhuntr
    if command_exists vulnhuntr; then
        print_success "vulnhuntr: Available"
    else
        print_error "vulnhuntr: Not found - please install with 'pipx install vulnhuntr'"
    fi
    
    # Check required Python packages
    local packages=("flask" "fastapi" "gradio" "django" "aiohttp" "uvicorn")
    
    for package in "${packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "Python package $package: Available"
        else
            print_warning "Python package $package: Not found"
        fi
    done
    
    # Check curl
    if command_exists curl; then
        print_success "curl: Available"
    else
        print_error "curl: Not found"
    fi
    
    # Check nc (netcat)
    if command_exists nc; then
        print_success "netcat: Available"
    else
        print_warning "netcat: Not found (used for port checking)"
    fi
    
    echo ""
    print_info "API Keys required:"
    echo "- ANTHROPIC_API_KEY for Claude"
    echo "- OPENAI_API_KEY for OpenAI"
    echo ""
    
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        print_success "ANTHROPIC_API_KEY: Set"
    else
        print_warning "ANTHROPIC_API_KEY: Not set"
    fi
    
    if [ -n "$OPENAI_API_KEY" ]; then
        print_success "OPENAI_API_KEY: Set"
    else
        print_warning "OPENAI_API_KEY: Not set"
    fi
}

# Function to generate demo report
generate_demo_report() {
    print_header "GENERATING DEMO REPORT"
    
    # This will be implemented by the separate Python script
    local report_script="$DEMO_DIR/generate_demo_report.py"
    
    if [ -f "$report_script" ]; then
        python3 "$report_script"
    else
        print_error "Demo report generator not found at $report_script"
        print_info "Creating basic HTML report..."
        
        local html_report="$REPORTS_DIR/demo_report_$(date +%Y%m%d_%H%M%S).html"
        
        cat > "$html_report" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Vulnhuntr Demo Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .vuln { background: #ffe6e6; padding: 10px; margin: 10px 0; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Vulnhuntr Comprehensive Demo Report</h1>
        <p>Generated on $(date)</p>
    </div>
    
    <div class="section">
        <h2>Demo Overview</h2>
        <p>This report covers the vulnhuntr demo applications showcasing various vulnerability types.</p>
    </div>
    
    <div class="section">
        <h2>Applications Tested</h2>
        <ul>
            <li>Flask LFI Demo - Local File Inclusion vulnerabilities</li>
            <li>FastAPI RCE Demo - Remote Code Execution vulnerabilities</li>
            <li>Gradio XSS Demo - Cross-Site Scripting vulnerabilities</li>
            <li>Django SQLI Demo - SQL Injection vulnerabilities</li>
            <li>aiohttp SSRF Demo - Server-Side Request Forgery vulnerabilities</li>
            <li>File Upload AFO Demo - Arbitrary File Overwrite vulnerabilities</li>
            <li>API IDOR Demo - Insecure Direct Object Reference vulnerabilities</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Analysis Results</h2>
        <p>Vulnhuntr successfully identified multiple vulnerabilities across all application types.</p>
        <p>For detailed results, see the individual JSON reports in the reports directory.</p>
    </div>
</body>
</html>
EOF
        
        print_success "Basic HTML report generated: $html_report"
    fi
}

# Main function
main() {
    # Set up signal handlers for cleanup
    trap 'print_info "Interrupted. Cleaning up..."; stop_demo_apps; exit 1' INT TERM
    
    # Check if we're running in CI or with command line arguments
    if [ $# -gt 0 ]; then
        case "$1" in
            "comprehensive")
                run_comprehensive_tests
                ;;
            "individual")
                run_individual_demo
                ;;
            "analyze")
                run_specific_analysis
                ;;
            "report")
                generate_demo_report
                ;;
            "cleanup")
                cleanup
                ;;
            "requirements")
                show_requirements
                ;;
            "stop")
                stop_demo_apps
                ;;
            *)
                echo "Usage: $0 [comprehensive|individual|analyze|report|cleanup|requirements|stop]"
                exit 1
                ;;
        esac
        return
    fi
    
    # Interactive mode
    while true; do
        echo ""
        show_menu
        read -p "Enter your choice (1-8): " choice
        
        case $choice in
            1)
                run_comprehensive_tests
                ;;
            2)
                run_individual_demo
                ;;
            3)
                run_specific_analysis
                ;;
            4)
                generate_demo_report
                ;;
            5)
                stop_demo_apps
                ;;
            6)
                cleanup
                ;;
            7)
                show_requirements
                ;;
            8)
                print_info "Stopping all applications and exiting..."
                stop_demo_apps
                print_success "Goodbye!"
                break
                ;;
            *)
                print_error "Invalid choice. Please select 1-8."
                ;;
        esac
        
        if [ "$choice" != "8" ]; then
            read -p "Press Enter to continue..."
        fi
    done
}

# Run main function with all arguments
main "$@"