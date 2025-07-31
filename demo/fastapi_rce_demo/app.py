"""
FastAPI Remote Code Execution (RCE) Demo Application

This application contains intentional RCE vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Direct eval() of user input
2. Subprocess execution with user-controlled commands
3. Dynamic import of user-specified modules
4. Unsafe pickle deserialization
5. Template injection leading to RCE
6. YAML deserialization with unsafe loader
"""

from fastapi import FastAPI, HTTPException, Form, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import subprocess
import os
import sys
import pickle
import base64
import yaml
import importlib
import tempfile
from typing import Dict, Any, Optional
import logging
import json

app = FastAPI(title="FastAPI RCE Demo", description="Intentionally vulnerable FastAPI application for testing")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecuteRequest(BaseModel):
    command: str
    timeout: int = 30

class EvalRequest(BaseModel):
    expression: str
    context: Dict[str, Any] = {}

class ImportRequest(BaseModel):
    module_name: str
    function_name: str
    arguments: Dict[str, Any] = {}

class PickleRequest(BaseModel):
    data: str  # Base64 encoded pickle data

class TemplateRequest(BaseModel):
    template: str
    variables: Dict[str, Any] = {}

@app.get("/", response_class=HTMLResponse)
async def index():
    """Main page with links to vulnerable endpoints"""
    return """
    <html>
    <head><title>FastAPI RCE Demo</title></head>
    <body>
        <h1>FastAPI Remote Code Execution Demo</h1>
        <p>This application demonstrates various RCE vulnerabilities in FastAPI applications.</p>
        
        <h2>Vulnerable Endpoints:</h2>
        <ul>
            <li><a href="/docs">API Documentation (Swagger UI)</a></li>
            <li><strong>GET /eval</strong> - Direct eval() of user input</li>
            <li><strong>POST /execute</strong> - Subprocess execution</li>
            <li><strong>POST /import</strong> - Dynamic module import</li>
            <li><strong>POST /deserialize</strong> - Unsafe pickle deserialization</li>
            <li><strong>POST /template</strong> - Template injection</li>
            <li><strong>POST /yaml_load</strong> - YAML deserialization</li>
            <li><strong>GET /calculate</strong> - Math expression evaluation</li>
        </ul>
        
        <h2>Test Payloads:</h2>
        <h3>Eval Injection:</h3>
        <ul>
            <li><code>__import__('os').system('id')</code></li>
            <li><code>exec("import subprocess; subprocess.run(['whoami'], shell=True)")</code></li>
        </ul>
        
        <h3>Command Injection:</h3>
        <ul>
            <li><code>whoami</code></li>
            <li><code>cat /etc/passwd</code></li>
            <li><code>ls -la /</code></li>
        </ul>
        
        <h3>Import Injection:</h3>
        <ul>
            <li>module: <code>subprocess</code>, function: <code>run</code></li>
            <li>module: <code>os</code>, function: <code>system</code></li>
        </ul>
    </body>
    </html>
    """

@app.get("/eval")
async def eval_expression(expr: str = Query(..., description="Python expression to evaluate")):
    """
    VULNERABILITY 1: Direct eval() of user input
    Allows execution of arbitrary Python code
    """
    try:
        # VULNERABLE: Direct eval without any sandboxing
        result = eval(expr)
        
        logger.warning(f"Eval executed: {expr}")
        return {
            "expression": expr,
            "result": str(result),
            "type": str(type(result).__name__)
        }
    except Exception as e:
        return {
            "expression": expr,
            "error": str(e),
            "type": "error"
        }

@app.post("/eval_advanced")
async def eval_with_context(request: EvalRequest):
    """
    VULNERABILITY 2: Eval with user-controlled context
    Even more dangerous as user can control the evaluation context
    """
    try:
        # VULNERABLE: User controls both expression and context
        context = request.context.copy()
        
        # Add some "helpful" functions to context (making it worse)
        context.update({
            'os': __import__('os'),
            'sys': __import__('sys'),
            'subprocess': __import__('subprocess'),
            'open': open,
            'exec': exec,
            'eval': eval
        })
        
        result = eval(request.expression, {"__builtins__": __builtins__}, context)
        
        logger.warning(f"Advanced eval executed: {request.expression} with context: {request.context}")
        return {
            "expression": request.expression,
            "context": request.context,
            "result": str(result)
        }
    except Exception as e:
        return {
            "expression": request.expression,
            "error": str(e)
        }

@app.post("/execute")
async def execute_command(request: ExecuteRequest):
    """
    VULNERABILITY 3: Direct subprocess execution of user input
    Allows execution of arbitrary system commands
    """
    try:
        # VULNERABLE: Direct subprocess execution without sanitization
        result = subprocess.run(
            request.command,
            shell=True,  # DANGEROUS: Enables shell injection
            capture_output=True,
            text=True,
            timeout=request.timeout
        )
        
        logger.warning(f"Command executed: {request.command}")
        return {
            "command": request.command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {request.timeout} seconds"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/system")
async def system_command(cmd: str = Query(..., description="System command to execute")):
    """
    VULNERABILITY 4: os.system() execution
    Alternative RCE vector using os.system
    """
    try:
        # VULNERABLE: Direct os.system call
        exit_code = os.system(cmd)
        
        logger.warning(f"System command executed: {cmd}")
        return {
            "command": cmd,
            "exit_code": exit_code,
            "message": "Command executed (check server logs for output)"
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/import")
async def dynamic_import(request: ImportRequest):
    """
    VULNERABILITY 5: Dynamic import with user-controlled module/function
    Allows importing and executing arbitrary modules
    """
    try:
        # VULNERABLE: User controls module name and function
        module = importlib.import_module(request.module_name)
        function = getattr(module, request.function_name)
        
        # VULNERABLE: Execute function with user-controlled arguments
        if request.arguments:
            result = function(**request.arguments)
        else:
            result = function()
        
        logger.warning(f"Dynamic import executed: {request.module_name}.{request.function_name}")
        return {
            "module": request.module_name,
            "function": request.function_name,
            "arguments": request.arguments,
            "result": str(result)
        }
    except Exception as e:
        return {
            "module": request.module_name,
            "function": request.function_name,
            "error": str(e)
        }

@app.post("/deserialize")
async def unsafe_deserialize(request: PickleRequest):
    """
    VULNERABILITY 6: Unsafe pickle deserialization
    Allows arbitrary code execution via crafted pickle payloads
    """
    try:
        # VULNERABLE: Unsafe pickle.loads without any validation
        pickle_data = base64.b64decode(request.data)
        result = pickle.loads(pickle_data)
        
        logger.warning(f"Pickle deserialized: {len(pickle_data)} bytes")
        return {
            "success": True,
            "result": str(result),
            "type": str(type(result).__name__)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/template")
async def template_injection(request: TemplateRequest):
    """
    VULNERABILITY 7: Server-Side Template Injection (SSTI)
    Using Python string formatting with user-controlled template
    """
    try:
        # VULNERABLE: Direct string formatting with user template
        # This can lead to RCE in many template engines
        
        # Simulate Jinja2-style template processing (vulnerable)
        if '{{' in request.template and '}}' in request.template:
            # Extract expressions between {{ }}
            import re
            expressions = re.findall(r'\{\{(.*?)\}\}', request.template)
            
            template = request.template
            for expr in expressions:
                try:
                    # VULNERABLE: Eval expressions in template
                    value = eval(expr.strip(), {"__builtins__": __builtins__}, request.variables)
                    template = template.replace('{{' + expr + '}}', str(value))
                except:
                    template = template.replace('{{' + expr + '}}', '[ERROR]')
            
            result = template
        else:
            # VULNERABLE: Python string format with user variables
            result = request.template.format(**request.variables)
        
        logger.warning(f"Template processed: {request.template}")
        return {
            "template": request.template,
            "variables": request.variables,
            "result": result
        }
    except Exception as e:
        return {
            "template": request.template,
            "error": str(e)
        }

@app.post("/yaml_load")
async def yaml_deserialize(yaml_content: str = Form(...)):
    """
    VULNERABILITY 8: Unsafe YAML deserialization
    Using yaml.load() without safe loader
    """
    try:
        # VULNERABLE: Using unsafe yaml.load() instead of yaml.safe_load()
        data = yaml.load(yaml_content, Loader=yaml.Loader)
        
        logger.warning(f"YAML loaded: {len(yaml_content)} characters")
        return {
            "yaml_content": yaml_content,
            "parsed_data": data,
            "success": True
        }
    except Exception as e:
        return {
            "yaml_content": yaml_content,
            "error": str(e),
            "success": False
        }

@app.get("/calculate")
async def calculate_expression(math_expr: str = Query(..., description="Mathematical expression")):
    """
    VULNERABILITY 9: Math expression evaluation without proper sandboxing
    Appears safe but can be exploited
    """
    try:
        # VULNERABLE: Attempting to be "safe" but still exploitable
        # Blacklist approach is insufficient
        dangerous_words = ['import', 'exec', 'eval', 'open', 'file', '__']
        
        if any(word in math_expr.lower() for word in dangerous_words):
            return {"error": "Expression contains dangerous keywords"}
        
        # VULNERABLE: Still uses eval, bypassable
        result = eval(math_expr, {"__builtins__": {}}, {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "divmod": divmod
        })
        
        return {
            "expression": math_expr,
            "result": result
        }
    except Exception as e:
        return {
            "expression": math_expr,
            "error": str(e)
        }

@app.post("/code_exec")
async def execute_code(code: str = Form(...), language: str = Form(default="python")):
    """
    VULNERABILITY 10: Code execution endpoint
    Meant to be a "code runner" but completely unsafe
    """
    try:
        if language.lower() == "python":
            # VULNERABLE: Direct exec of user code
            
            # Capture stdout
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            try:
                exec(code)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            logger.warning(f"Python code executed: {len(code)} characters")
            return {
                "language": language,
                "code": code,
                "output": output,
                "success": True
            }
        
        elif language.lower() == "bash":
            # VULNERABLE: Shell command execution
            result = subprocess.run(code, shell=True, capture_output=True, text=True)
            return {
                "language": language,
                "code": code,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": True
            }
        
        else:
            return {"error": f"Unsupported language: {language}"}
            
    except Exception as e:
        return {
            "language": language,
            "code": code,
            "error": str(e),
            "success": False
        }

@app.get("/debug")
async def debug_info():
    """
    VULNERABILITY 11: Debug endpoint exposing system information
    Reveals sensitive server information
    """
    import platform
    import psutil
    
    return {
        "system": {
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        },
        "process": {
            "pid": os.getpid(),
            "cwd": os.getcwd(),
            "user": os.getenv('USER', 'unknown'),
            "path": os.getenv('PATH', ''),
            "env_vars": dict(os.environ)  # DANGEROUS: Exposes all environment variables
        },
        "memory": {
            "available": psutil.virtual_memory().available,
            "total": psutil.virtual_memory().total,
            "percent": psutil.virtual_memory().percent
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)