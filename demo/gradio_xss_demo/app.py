"""
Gradio Cross-Site Scripting (XSS) Demo Application

This application contains intentional XSS vulnerabilities for demonstration purposes.
DO NOT USE IN PRODUCTION - FOR EDUCATIONAL/TESTING PURPOSES ONLY.

Vulnerabilities included:
1. Reflected XSS in text input processing
2. Stored XSS in file upload comments
3. DOM-based XSS in dynamic content generation
4. XSS in markdown rendering
5. XSS through unsafe HTML sanitization
"""

import gradio as gr
import os
import json
import html
import markdown
from datetime import datetime
from typing import List, Tuple, Optional
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for demo (don't use in production)
user_comments = []
uploaded_files_data = []
chat_history = []

def vulnerable_text_processor(user_input: str) -> str:
    """
    VULNERABILITY 1: Reflected XSS in text processing
    User input is directly embedded in HTML response without sanitization
    """
    logger.warning(f"Processing user input: {user_input[:50]}...")
    
    # VULNERABLE: Direct HTML embedding without escaping
    html_response = f"""
    <div style="border: 1px solid #ccc; padding: 10px; margin: 10px;">
        <h3>Your Input:</h3>
        <p>{user_input}</p>
        <hr>
        <p><em>Processed at: {datetime.now()}</em></p>
    </div>
    """
    
    return html_response

def vulnerable_comment_system(name: str, comment: str) -> Tuple[str, str]:
    """
    VULNERABILITY 2: Stored XSS in comment system
    Comments are stored and displayed without proper sanitization
    """
    if not name or not comment:
        return "Please provide both name and comment", ""
    
    # VULNERABLE: Store raw user input without sanitization
    comment_data = {
        "name": name,
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }
    user_comments.append(comment_data)
    
    logger.warning(f"Comment stored from {name}: {comment[:30]}...")
    
    # VULNERABLE: Display all comments without escaping
    comments_html = "<h3>Recent Comments:</h3>"
    for c in user_comments[-5:]:  # Show last 5 comments
        comments_html += f"""
        <div style="border-bottom: 1px solid #eee; padding: 5px; margin: 5px 0;">
            <strong>{c['name']}</strong> ({c['timestamp'][:19]}):
            <br>
            {c['comment']}
        </div>
        """
    
    return "Comment added successfully!", comments_html

def vulnerable_markdown_renderer(markdown_text: str) -> str:
    """
    VULNERABILITY 3: XSS through unsafe markdown rendering
    Markdown is converted to HTML without proper sanitization
    """
    if not markdown_text:
        return ""
    
    logger.warning(f"Rendering markdown: {markdown_text[:50]}...")
    
    # VULNERABLE: Convert markdown to HTML without sanitization
    # This allows HTML injection through markdown
    html_output = markdown.markdown(markdown_text, extensions=['extra'])
    
    # Make it even worse by allowing some "safe" HTML tags
    # VULNERABLE: Insufficient HTML filtering
    unsafe_html = html_output.replace('&lt;script&gt;', '<script>').replace('&lt;/script&gt;', '</script>')
    unsafe_html = unsafe_html.replace('&lt;img', '<img').replace('&gt;', '>')
    
    return f"""
    <div style="border: 2px solid #4CAF50; padding: 15px; background: #f9f9f9;">
        <h4>Rendered Markdown:</h4>
        {unsafe_html}
    </div>
    """

def vulnerable_file_processor(file_path: str, description: str) -> Tuple[str, str]:
    """
    VULNERABILITY 4: XSS through file upload description
    File descriptions are displayed without sanitization
    """
    if not file_path:
        return "No file uploaded", ""
    
    # Read file info
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    file_name = os.path.basename(file_path)
    
    # VULNERABLE: Store file data with unsanitized description
    file_data = {
        "name": file_name,
        "size": file_size,
        "description": description,
        "upload_time": datetime.now().isoformat(),
        "path": file_path
    }
    uploaded_files_data.append(file_data)
    
    logger.warning(f"File uploaded: {file_name} with description: {description[:30]}...")
    
    # VULNERABLE: Display file list with unsanitized descriptions
    files_html = "<h3>Uploaded Files:</h3>"
    for f in uploaded_files_data[-3:]:  # Show last 3 files
        files_html += f"""
        <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0;">
            <strong>File:</strong> {f['name']} ({f['size']} bytes)<br>
            <strong>Description:</strong> {f['description']}<br>
            <em>Uploaded: {f['upload_time'][:19]}</em>
        </div>
        """
    
    return f"File '{file_name}' uploaded successfully!", files_html

def vulnerable_search_function(search_query: str, search_type: str) -> str:
    """
    VULNERABILITY 5: XSS in search results
    Search query is reflected in results without escaping
    """
    if not search_query:
        return "Please enter a search query"
    
    logger.warning(f"Search performed: {search_query} (type: {search_type})")
    
    # Simulate search results
    mock_results = [
        f"Result 1 for '{search_query}' in {search_type}",
        f"Result 2 matching '{search_query}'",
        f"Advanced result for '{search_query}' with special handling"
    ]
    
    # VULNERABLE: Embed search query directly in HTML
    results_html = f"""
    <div style="border: 1px solid #2196F3; padding: 15px;">
        <h3>Search Results for: {search_query}</h3>
        <p><em>Search type: {search_type}</em></p>
        <ul>
    """
    
    for result in mock_results:
        # VULNERABLE: No escaping of search terms in results
        highlighted_result = result.replace(search_query, f"<mark>{search_query}</mark>")
        results_html += f"<li>{highlighted_result}</li>"
    
    results_html += """
        </ul>
        <p><small>Search completed successfully</small></p>
    </div>
    """
    
    return results_html

def vulnerable_chat_interface(message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
    """
    VULNERABILITY 6: XSS in chat interface
    Chat messages are stored and displayed without sanitization
    """
    if not message:
        return history, ""
    
    logger.warning(f"Chat message: {message[:50]}...")
    
    # Simulate bot response
    bot_responses = [
        f"I see you said: {message}",
        f"That's interesting! You mentioned: {message}",
        f"Thanks for your input: {message}. How can I help?",
        f"Processing your request: {message}..."
    ]
    
    import random
    bot_response = random.choice(bot_responses)
    
    # VULNERABLE: Add to history without sanitization
    history.append((message, bot_response))
    
    return history, ""

def vulnerable_dynamic_content(content_type: str, user_data: str) -> str:
    """
    VULNERABILITY 7: DOM-based XSS simulation
    Generates dynamic content based on user input
    """
    if not user_data:
        return "Please provide user data"
    
    logger.warning(f"Generating {content_type} content with data: {user_data[:50]}...")
    
    if content_type == "Profile Card":
        # VULNERABLE: Direct embedding in HTML template
        return f"""
        <div style="border: 2px solid #FF9800; padding: 20px; background: linear-gradient(45deg, #FFF3E0, #FFE0B2);">
            <h2>User Profile</h2>
            <p><strong>Name:</strong> {user_data}</p>
            <p><strong>Status:</strong> Active User</p>
            <script>
                // Secure: User data is sanitized before embedding in JavaScript context
                var userData = "{escape_js(user_data)}";
                console.log("Profile loaded for: " + userData);
            </script>
        </div>
        """
    
    elif content_type == "Alert Message":
        # VULNERABLE: User data in JavaScript alert
        return f"""
        <div style="border: 2px solid #F44336; padding: 15px; background: #FFEBEE;">
            <h3>System Alert</h3>
            <p>Alert message: {user_data}</p>
            <button onclick="alert('Alert for: {user_data}')">Show Alert</button>
        </div>
        """
    
    elif content_type == "Dynamic List":
        # VULNERABLE: User data in multiple contexts
        items = user_data.split(',')
        list_html = f"""
        <div style="border: 2px solid #9C27B0; padding: 15px; background: #F3E5F5;">
            <h3>Dynamic List</h3>
            <ul>
        """
        for item in items:
            list_html += f"<li onclick='console.log(\"{item}\");'>{item.strip()}</li>"
        
        list_html += """
            </ul>
            <script>
                // More vulnerable JavaScript
                function processItems() {
        """
        list_html += f'        document.title = "Processing: {user_data}";'
        list_html += """
                }
                processItems();
            </script>
        </div>
        """
        return list_html
    
    else:
        return f"""
        <div style="border: 1px solid #ccc; padding: 10px;">
            <p>Unknown content type: {content_type}</p>
            <p>Data: {user_data}</p>
        </div>
        """

def create_demo_interface():
    """Create the Gradio interface with vulnerable components"""
    
    with gr.Blocks(title="Gradio XSS Demo - VULNERABLE", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🚨 Gradio XSS Vulnerability Demo 🚨
        
        **⚠️ WARNING: This application contains intentional security vulnerabilities for educational purposes only!**
        
        This demo showcases various Cross-Site Scripting (XSS) vulnerabilities in Gradio applications.
        
        ## Test Payloads:
        
        ### Basic XSS:
        - `<script>alert('XSS')</script>`
        - `<img src=x onerror=alert('XSS')>`
        - `<svg onload=alert('XSS')>`
        
        ### Event Handler XSS:
        - `<div onclick="alert('XSS')">Click me</div>`
        - `<input onfocus="alert('XSS')" autofocus>`
        
        ### JavaScript Context:
        - `"; alert('XSS'); //`
        - `'); alert('XSS'); //`
        
        ### Data URL XSS:
        - `<iframe src="data:text/html,<script>alert('XSS')</script>"></iframe>`
        """)
        
        with gr.Tab("Text Processor"):
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="Enter text to process",
                        placeholder="Try: <script>alert('XSS')</script>",
                        lines=3
                    )
                    process_btn = gr.Button("Process Text")
                
                with gr.Column():
                    text_output = gr.HTML(label="Processed Output")
            
            process_btn.click(vulnerable_text_processor, inputs=[text_input], outputs=[text_output])
        
        with gr.Tab("Comment System"):
            with gr.Row():
                with gr.Column():
                    name_input = gr.Textbox(label="Your Name", placeholder="John Doe")
                    comment_input = gr.Textbox(
                        label="Comment", 
                        placeholder="Try: <img src=x onerror=alert('Stored XSS')>",
                        lines=3
                    )
                    comment_btn = gr.Button("Add Comment")
                
                with gr.Column():
                    comment_status = gr.Textbox(label="Status")
                    comments_display = gr.HTML(label="Recent Comments")
            
            comment_btn.click(
                vulnerable_comment_system, 
                inputs=[name_input, comment_input], 
                outputs=[comment_status, comments_display]
            )
        
        with gr.Tab("Markdown Renderer"):
            with gr.Row():
                with gr.Column():
                    markdown_input = gr.Textbox(
                        label="Markdown Content",
                        placeholder="Try: [Click me](<javascript:alert('XSS')>)",
                        lines=5
                    )
                    render_btn = gr.Button("Render Markdown")
                
                with gr.Column():
                    markdown_output = gr.HTML(label="Rendered HTML")
            
            render_btn.click(vulnerable_markdown_renderer, inputs=[markdown_input], outputs=[markdown_output])
        
        with gr.Tab("File Upload"):
            with gr.Row():
                with gr.Column():
                    file_input = gr.File(label="Upload File")
                    description_input = gr.Textbox(
                        label="File Description",
                        placeholder="Try: <script>alert('File XSS')</script>",
                        lines=2
                    )
                    upload_btn = gr.Button("Process File")
                
                with gr.Column():
                    upload_status = gr.Textbox(label="Upload Status")
                    files_display = gr.HTML(label="Uploaded Files")
            
            upload_btn.click(
                vulnerable_file_processor,
                inputs=[file_input, description_input],
                outputs=[upload_status, files_display]
            )
        
        with gr.Tab("Search"):
            with gr.Row():
                with gr.Column():
                    search_input = gr.Textbox(
                        label="Search Query",
                        placeholder="Try: <svg onload=alert('Search XSS')>",
                    )
                    search_type = gr.Dropdown(
                        choices=["Web", "Images", "Videos", "News"],
                        value="Web",
                        label="Search Type"
                    )
                    search_btn = gr.Button("Search")
                
                with gr.Column():
                    search_results = gr.HTML(label="Search Results")
            
            search_btn.click(
                vulnerable_search_function,
                inputs=[search_input, search_type],
                outputs=[search_results]
            )
        
        with gr.Tab("Chat Interface"):
            chatbot = gr.Chatbot(label="Vulnerable Chat Bot")
            msg = gr.Textbox(
                label="Message", 
                placeholder="Try: <img src=x onerror=alert('Chat XSS')>",
            )
            clear = gr.Button("Clear Chat")
            
            msg.submit(vulnerable_chat_interface, [msg, chatbot], [chatbot, msg])
            clear.click(lambda: ([], ""), outputs=[chatbot, msg])
        
        with gr.Tab("Dynamic Content"):
            with gr.Row():
                with gr.Column():
                    content_type = gr.Dropdown(
                        choices=["Profile Card", "Alert Message", "Dynamic List"],
                        value="Profile Card",
                        label="Content Type"
                    )
                    user_data_input = gr.Textbox(
                        label="User Data",
                        placeholder="Try: \"; alert('Dynamic XSS'); //",
                        lines=2
                    )
                    generate_btn = gr.Button("Generate Content")
                
                with gr.Column():
                    dynamic_output = gr.HTML(label="Generated Content")
            
            generate_btn.click(
                vulnerable_dynamic_content,
                inputs=[content_type, user_data_input],
                outputs=[dynamic_output]
            )
    
    return demo

if __name__ == "__main__":
    demo = create_demo_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Don't share publicly for security
        debug=True
    )