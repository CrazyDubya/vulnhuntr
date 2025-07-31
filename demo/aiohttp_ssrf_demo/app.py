"""
aiohttp Server-Side Request Forgery (SSRF) Demo Application

This application contains intentional SSRF vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. URL fetching without validation
2. Internal service requests
3. Webhook URL handling
4. Image/file proxy functionality
5. XML External Entity (XXE) processing
6. DNS rebinding attacks
7. Cloud metadata service access
"""

import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
import aiofiles
import asyncio
import json
import logging
import os
import re
import time
import hashlib
import base64
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from datetime import datetime
import socket
import ipaddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global HTTP client session
client_session = None

async def init_client_session(app):
    """Initialize global HTTP client session"""
    global client_session
    timeout = ClientTimeout(total=30)  # Intentionally high timeout for demo
    client_session = ClientSession(timeout=timeout)

async def cleanup_client_session(app):
    """Cleanup global HTTP client session"""
    global client_session
    if client_session:
        await client_session.close()

async def index(request):
    """Main page with navigation to vulnerable endpoints"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>aiohttp SSRF Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { margin: 10px 0; }
            .payload { background: #f0f0f0; padding: 5px; margin: 5px 0; font-family: monospace; }
            .warning { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🌐 aiohttp SSRF Vulnerability Demo</h1>
        <p class="warning">⚠️ WARNING: This application contains intentional security vulnerabilities for educational purposes only!</p>
        
        <h2>Vulnerable Endpoints:</h2>
        
        <div class="endpoint">
            <h3>1. URL Fetcher (Basic SSRF)</h3>
            <p><a href="/fetch?url=http://httpbin.org/json">GET /fetch?url=...</a></p>
            <p>Fetches content from any URL without validation</p>
        </div>
        
        <div class="endpoint">
            <h3>2. Webhook Handler (Callback SSRF)</h3>
            <p><a href="/webhook?callback_url=http://httpbin.org/post">GET /webhook?callback_url=...</a></p>
            <p>Sends data to callback URLs without validation</p>
        </div>
        
        <div class="endpoint">
            <h3>3. Image Proxy (File SSRF)</h3>
            <p><a href="/image_proxy?image_url=http://httpbin.org/image/png">GET /image_proxy?image_url=...</a></p>
            <p>Proxies images and files from external URLs</p>
        </div>
        
        <div class="endpoint">
            <h3>4. URL Validator (Bypass Testing)</h3>
            <p><a href="/validate_url?url=https://google.com">GET /validate_url?url=...</a></p>
            <p>Attempts URL validation but can be bypassed</p>
        </div>
        
        <div class="endpoint">
            <h3>5. XML Parser (XXE SSRF)</h3>
            <p><strong>POST /parse_xml</strong></p>
            <p>Parses XML that may contain external entities</p>
        </div>
        
        <div class="endpoint">
            <h3>6. Health Check (Internal Services)</h3>
            <p><a href="/health_check?service_url=http://localhost:8080/health">GET /health_check?service_url=...</a></p>
            <p>Checks health of internal services</p>
        </div>
        
        <div class="endpoint">
            <h3>7. Metadata Service (Cloud SSRF)</h3>
            <p><a href="/metadata?path=latest/meta-data/">GET /metadata?path=...</a></p>
            <p>Accesses cloud metadata services</p>
        </div>

        <h2>Test Payloads:</h2>
        
        <h3>Internal Network Access:</h3>
        <div class="payload">http://127.0.0.1:22</div>
        <div class="payload">http://localhost:3306</div>
        <div class="payload">http://192.168.1.1/admin</div>
        <div class="payload">http://10.0.0.1:8080</div>
        
        <h3>Cloud Metadata Services:</h3>
        <div class="payload">http://169.254.169.254/latest/meta-data/</div>
        <div class="payload">http://metadata.google.internal/computeMetadata/v1/</div>
        <div class="payload">http://100.100.100.200/latest/meta-data/</div>
        
        <h3>URL Bypass Techniques:</h3>
        <div class="payload">http://localhost#.evil.com/</div>
        <div class="payload">http://127.0.0.1.evil.com/</div>
        <div class="payload">http://[::1]:22/</div>
        <div class="payload">http://0x7f000001/</div>
        
        <h3>Protocol Smuggling:</h3>
        <div class="payload">gopher://127.0.0.1:6379/_*1%0d%0a$4%0d%0aeval%0d%0a</div>
        <div class="payload">file:///etc/passwd</div>
        <div class="payload">ftp://internal.ftp.server/secret</div>
        
        <h3>DNS Rebinding:</h3>
        <div class="payload">http://7f000001.1time.run/</div>
        <div class="payload">http://makeup.127.0.0.1.nip.io/</div>
        
        <h3>XXE Payloads:</h3>
        <div class="payload">
        &lt;?xml version="1.0"?&gt;<br>
        &lt;!DOCTYPE data [<br>
        &lt;!ENTITY xxe SYSTEM "http://127.0.0.1:22"&gt;<br>
        ]&gt;<br>
        &lt;data&gt;&amp;xxe;&lt;/data&gt;
        </div>

        <h2>Testing Instructions:</h2>
        <ol>
            <li>Try accessing internal services like databases, admin panels</li>
            <li>Attempt to read local files using file:// protocol</li>
            <li>Test cloud metadata service endpoints</li>
            <li>Use URL encoding and bypass techniques</li>
            <li>Test different protocols (gopher, ftp, etc.)</li>
            <li>Try XML external entity attacks</li>
        </ol>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def vulnerable_fetch(request):
    """
    VULNERABILITY 1: Basic SSRF - Fetch any URL without validation
    Allows accessing internal services and external URLs
    """
    url = request.query.get('url')
    
    if not url:
        return web.json_response({'error': 'URL parameter required'})
    
    logger.warning(f"Fetching URL without validation: {url}")
    
    try:
        # VULNERABLE: No URL validation or restrictions
        async with client_session.get(url) as response:
            content = await response.text()
            headers = dict(response.headers)
            
            return web.json_response({
                'url': url,
                'status': response.status,
                'headers': headers,
                'content': content[:1000],  # Limit content for readability
                'content_length': len(content),
                'vulnerability': 'No URL validation allows SSRF attacks'
            })
    
    except Exception as e:
        return web.json_response({
            'url': url,
            'error': str(e),
            'vulnerability': 'Exception occurred but URL was still processed'
        })

async def vulnerable_webhook(request):
    """
    VULNERABILITY 2: Webhook callback SSRF
    Sends POST data to user-controlled callback URLs
    """
    callback_url = request.query.get('callback_url')
    
    if not callback_url:
        return web.json_response({'error': 'callback_url parameter required'})
    
    # Simulate webhook data
    webhook_data = {
        'event': 'user_action',
        'timestamp': datetime.now().isoformat(),
        'user_id': 'demo_user_123',
        'action': 'button_click',
        'metadata': {
            'ip_address': request.remote,
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }
    }
    
    logger.warning(f"Sending webhook to unvalidated URL: {callback_url}")
    
    try:
        # VULNERABLE: Send POST request to user-controlled URL
        async with client_session.post(
            callback_url,
            json=webhook_data,
            headers={'Content-Type': 'application/json'}
        ) as response:
            response_text = await response.text()
            
            return web.json_response({
                'callback_url': callback_url,
                'webhook_data': webhook_data,
                'response_status': response.status,
                'response_content': response_text[:500],
                'vulnerability': 'Webhook sent to unvalidated callback URL'
            })
    
    except Exception as e:
        return web.json_response({
            'callback_url': callback_url,
            'webhook_data': webhook_data,
            'error': str(e),
            'vulnerability': 'Webhook attempt made to potentially malicious URL'
        })

async def vulnerable_image_proxy(request):
    """
    VULNERABILITY 3: Image proxy SSRF
    Proxies images from external URLs without validation
    """
    image_url = request.query.get('image_url')
    
    if not image_url:
        return web.json_response({'error': 'image_url parameter required'})
    
    logger.warning(f"Proxying image from unvalidated URL: {image_url}")
    
    try:
        # VULNERABLE: Fetch any URL claiming to be an image
        async with client_session.get(image_url) as response:
            content = await response.read()
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            
            # Return the content as-is (dangerous!)
            return web.Response(
                body=content,
                content_type=content_type,
                headers={
                    'X-Proxied-From': image_url,
                    'X-Vulnerability': 'Image proxy allows SSRF to any URL'
                }
            )
    
    except Exception as e:
        return web.json_response({
            'image_url': image_url,
            'error': str(e),
            'vulnerability': 'Image proxy attempted to fetch from potentially malicious URL'
        })

async def vulnerable_url_validator(request):
    """
    VULNERABILITY 4: Bypassable URL validation
    Attempts to validate URLs but can be easily bypassed
    """
    url = request.query.get('url')
    
    if not url:
        return web.json_response({'error': 'URL parameter required'})
    
    # VULNERABLE: Weak validation that can be bypassed
    def weak_validation(url):
        """Weak URL validation with multiple bypass opportunities"""
        
        # Check 1: Blacklist approach (bypassable)
        blacklisted_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        parsed = urlparse(url)
        
        if any(blocked in url.lower() for blocked in blacklisted_hosts):
            return False, "Blocked: URL contains blacklisted host"
        
        # Check 2: Protocol whitelist (bypassable with case variations)
        if not url.lower().startswith(('http://', 'https://')):
            return False, "Blocked: Only HTTP/HTTPS protocols allowed"
        
        # Check 3: IP address check (bypassable with encoding)
        try:
            if parsed.hostname:
                ip = socket.gethostbyname(parsed.hostname)
                if ipaddress.ip_address(ip).is_private:
                    return False, "Blocked: Private IP address detected"
        except:
            pass  # If hostname resolution fails, allow it (vulnerable!)
        
        return True, "URL validation passed"
    
    is_valid, validation_message = weak_validation(url)
    
    logger.warning(f"URL validation result for {url}: {validation_message}")
    
    if not is_valid:
        return web.json_response({
            'url': url,
            'valid': False,
            'message': validation_message,
            'vulnerability': 'Validation can be bypassed with various techniques'
        })
    
    try:
        # VULNERABLE: Even "validated" URLs can be malicious
        async with client_session.get(url) as response:
            content = await response.text()
            
            return web.json_response({
                'url': url,
                'valid': True,
                'validation_message': validation_message,
                'status': response.status,
                'content': content[:500],
                'vulnerability': 'Weak validation allows bypass techniques'
            })
    
    except Exception as e:
        return web.json_response({
            'url': url,
            'valid': True,
            'validation_message': validation_message,
            'error': str(e),
            'vulnerability': 'URL passed validation but caused error'
        })

async def vulnerable_xml_parser(request):
    """
    VULNERABILITY 5: XXE (XML External Entity) SSRF
    Parses XML that may contain external entity references
    """
    if request.method != 'POST':
        return web.Response(text="""
        <html>
        <head><title>XML Parser</title></head>
        <body>
            <h2>XML Parser (Vulnerable to XXE)</h2>
            <form method="post" enctype="text/plain">
                <p>XML Data:</p>
                <textarea name="xml_data" rows="10" cols="80" placeholder='<?xml version="1.0"?>
<!DOCTYPE data [
<!ENTITY xxe SYSTEM "http://127.0.0.1:22">
]>
<data>&xxe;</data>'></textarea><br>
                <input type="submit" value="Parse XML">
            </form>
        </body>
        </html>
        """, content_type='text/html')
    
    try:
        body = await request.text()
        
        # Extract XML data from form submission
        if 'xml_data=' in body:
            xml_data = body.split('xml_data=', 1)[1]
            xml_data = xml_data.replace('+', ' ')  # Basic URL decoding
        else:
            xml_data = body
        
        logger.warning(f"Parsing XML with potential XXE: {xml_data[:100]}...")
        
        # VULNERABLE: Parse XML without disabling external entities
        try:
            # This is intentionally vulnerable to XXE
            root = ET.fromstring(xml_data)
            
            # Extract text content
            def extract_text(element):
                text = element.text or ''
                for child in element:
                    text += extract_text(child)
                return text
            
            parsed_content = extract_text(root)
            
            return web.json_response({
                'xml_data': xml_data,
                'parsed_root_tag': root.tag,
                'parsed_content': parsed_content,
                'vulnerability': 'XML parser allows XXE attacks for SSRF'
            })
        
        except ET.ParseError as e:
            return web.json_response({
                'xml_data': xml_data,
                'parse_error': str(e),
                'vulnerability': 'XML parsing failed but external entities may have been processed'
            })
    
    except Exception as e:
        return web.json_response({
            'error': str(e),
            'vulnerability': 'XML processing error but XXE may have occurred'
        })

async def vulnerable_health_check(request):
    """
    VULNERABILITY 6: Internal service health check SSRF
    Checks health of internal services using user-provided URLs
    """
    service_url = request.query.get('service_url')
    timeout = int(request.query.get('timeout', '5'))
    
    if not service_url:
        return web.json_response({'error': 'service_url parameter required'})
    
    # Ensure URL has a health endpoint
    if not service_url.endswith('/health'):
        service_url = service_url.rstrip('/') + '/health'
    
    logger.warning(f"Health checking internal service: {service_url}")
    
    start_time = time.time()
    
    try:
        # VULNERABLE: No validation for internal service URLs
        timeout_obj = ClientTimeout(total=timeout)
        async with ClientSession(timeout=timeout_obj) as session:
            async with session.get(service_url) as response:
                content = await response.text()
                end_time = time.time()
                
                return web.json_response({
                    'service_url': service_url,
                    'status': 'healthy' if response.status == 200 else 'unhealthy',
                    'http_status': response.status,
                    'response_time_ms': round((end_time - start_time) * 1000, 2),
                    'response_content': content[:200],
                    'vulnerability': 'Health check allows SSRF to internal services'
                })
    
    except asyncio.TimeoutError:
        return web.json_response({
            'service_url': service_url,
            'status': 'timeout',
            'response_time_ms': timeout * 1000,
            'vulnerability': 'Health check timeout but connection was attempted'
        })
    
    except Exception as e:
        end_time = time.time()
        return web.json_response({
            'service_url': service_url,
            'status': 'error',
            'error': str(e),
            'response_time_ms': round((end_time - start_time) * 1000, 2),
            'vulnerability': 'Health check failed but internal network was probed'
        })

async def vulnerable_metadata_service(request):
    """
    VULNERABILITY 7: Cloud metadata service access
    Accesses cloud metadata services without restrictions
    """
    path = request.query.get('path', 'latest/meta-data/')
    service = request.query.get('service', 'aws')  # aws, gcp, azure
    
    # Define metadata service URLs
    metadata_urls = {
        'aws': f'http://169.254.169.254/{path}',
        'gcp': f'http://metadata.google.internal/computeMetadata/v1/{path}',
        'azure': f'http://169.254.169.254/metadata/{path}?api-version=2021-02-01'
    }
    
    if service not in metadata_urls:
        return web.json_response({'error': f'Unknown service: {service}. Use: aws, gcp, azure'})
    
    metadata_url = metadata_urls[service]
    
    logger.warning(f"Accessing cloud metadata service: {metadata_url}")
    
    try:
        headers = {}
        
        # Add required headers for different cloud providers
        if service == 'gcp':
            headers['Metadata-Flavor'] = 'Google'
        elif service == 'azure':
            headers['Metadata'] = 'true'
        
        # VULNERABLE: Access cloud metadata without restrictions
        async with client_session.get(metadata_url, headers=headers) as response:
            content = await response.text()
            
            return web.json_response({
                'service': service,
                'path': path,
                'metadata_url': metadata_url,
                'status': response.status,
                'headers_sent': headers,
                'metadata_content': content,
                'vulnerability': 'Unrestricted access to cloud metadata services'
            })
    
    except Exception as e:
        return web.json_response({
            'service': service,
            'path': path,
            'metadata_url': metadata_url,
            'error': str(e),
            'vulnerability': 'Metadata service access attempted'
        })

async def vulnerable_file_inclusion(request):
    """
    VULNERABILITY 8: File inclusion via URL
    Includes files from URLs that may use file:// protocol
    """
    file_url = request.query.get('file_url')
    
    if not file_url:
        return web.json_response({'error': 'file_url parameter required'})
    
    logger.warning(f"Including file from URL: {file_url}")
    
    try:
        # VULNERABLE: Allow any protocol including file://
        async with client_session.get(file_url) as response:
            content = await response.text()
            
            return web.json_response({
                'file_url': file_url,
                'status': response.status,
                'content': content,
                'content_type': response.headers.get('Content-Type', 'unknown'),
                'vulnerability': 'File inclusion allows local file access via file:// protocol'
            })
    
    except Exception as e:
        return web.json_response({
            'file_url': file_url,
            'error': str(e),
            'vulnerability': 'File inclusion attempted with potentially malicious URL'
        })

def create_app():
    """Create the aiohttp application with vulnerable routes"""
    app = web.Application()
    
    # Setup and cleanup
    app.on_startup.append(init_client_session)
    app.on_cleanup.append(cleanup_client_session)
    
    # Routes
    app.router.add_get('/', index)
    app.router.add_get('/fetch', vulnerable_fetch)
    app.router.add_get('/webhook', vulnerable_webhook)
    app.router.add_get('/image_proxy', vulnerable_image_proxy)
    app.router.add_get('/validate_url', vulnerable_url_validator)
    app.router.add_route('*', '/parse_xml', vulnerable_xml_parser)
    app.router.add_get('/health_check', vulnerable_health_check)
    app.router.add_get('/metadata', vulnerable_metadata_service)
    app.router.add_get('/file_include', vulnerable_file_inclusion)
    
    return app

if __name__ == '__main__':
    print("🌐 aiohttp SSRF Demo Application")
    print("================================")
    print("Starting server on http://0.0.0.0:8002")
    print("")
    print("Test endpoints:")
    print("- Basic SSRF: http://localhost:8002/fetch?url=http://127.0.0.1:22")
    print("- Webhook SSRF: http://localhost:8002/webhook?callback_url=http://internal.service/")
    print("- Image Proxy: http://localhost:8002/image_proxy?image_url=file:///etc/passwd")
    print("- Metadata: http://localhost:8002/metadata?service=aws&path=latest/user-data")
    print("")
    
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8002)