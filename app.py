import os
import shutil
import gradio as gr
from ingestion import load_and_ingest_file, load_and_ingest_url, clear_database, delete_embeddings_by_source
from qa_pipeline import answer_question

INGESTED_URLS_FILE = "./ingested_urls.txt"
UPLOAD_DIR = "./uploads"


def handle_file_upload(file):
    filename = os.path.basename(file.name)
    file_path = f"./uploads/{filename}"
    upload_dir = "uploads"
    os.makedirs("./uploads", exist_ok=True)
    destination = os.path.join(upload_dir, filename)
    shutil.copy2(file.name, destination)
    load_and_ingest_file(file_path)
    return "File processed and embedded successfully."


def handle_url_ingestion(url):
    load_and_ingest_url(url)
    save_url(url)
    return "URL content processed and embedded successfully."


def handle_file_upload_with_progress(file):
    """File upload with progress indicator"""
    if not file:
        return "No file selected.", gr.update(visible=False)
    
    try:
        #  Copy file
        filename = os.path.basename(file.name)
        file_path = f"./uploads/{filename}"
        upload_dir = "uploads"
        os.makedirs("./uploads", exist_ok=True)
        destination = os.path.join(upload_dir, filename)
        shutil.copy2(file.name, destination)
        
        # Process and embed
        load_and_ingest_file(file_path)
        
        return f"File '{filename}' processed and embedded successfully!", gr.update(visible=True)
    except Exception as e:
        return f"Error processing file: {str(e)}", gr.update(visible=True)


def handle_url_ingestion_with_progress(url):
    """URL ingestion with progress indicator"""
    if not url or not url.strip():
        return "No URL provided.", gr.update(visible=False)
    
    try:
        # Ingest URL content
        load_and_ingest_url(url.strip())
        
        # Save URL to file
        save_url(url.strip())
        
        return f"URL '{url.strip()}' processed and embedded successfully!", gr.update(visible=True)
    except Exception as e:
        return f"Error processing URL: {str(e)}", gr.update(visible=True)


def handle_question(question):
    return answer_question(question)


def list_uploaded_files():
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        full_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(full_path):
            files.append(full_path)
    return files


def save_url(url: str):
    with open(INGESTED_URLS_FILE, "a") as f:
        f.write(url.strip() + "\n")


def get_saved_urls() -> str:
    if not os.path.exists(INGESTED_URLS_FILE):
        return "<i>No URLs ingested yet.</i>"

    links_html = ""
    with open(INGESTED_URLS_FILE, "r") as f:
        for i, line in enumerate(f):
            url = line.strip()
            links_html += f'<div style="margin: 2px 0; padding: 8px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;"><a href="{url}" target="_blank">{url}</a></div>'
    return links_html


def get_saved_urls_list():
    """Get list of ingested URLs for dropdown"""
    urls = []
    if os.path.exists(INGESTED_URLS_FILE):
        with open(INGESTED_URLS_FILE, "r") as f:
            for line in f:
                url = line.strip()
                if url:
                    urls.append(url)
    return urls


def delete_url_by_url(url_to_delete: str):
    """Delete URL by its actual URL string and its embeddings"""
    if not os.path.exists(INGESTED_URLS_FILE):
        return "No URLs to delete."
    
    try:
        with open(INGESTED_URLS_FILE, "r") as f:
            urls = f.readlines()
        
        # Find and remove the URL
        found = False
        for i, url in enumerate(urls):
            if url.strip() == url_to_delete:
                urls.pop(i)
                found = True
                break
        
        if found:
            with open(INGESTED_URLS_FILE, "w") as f:
                f.writelines(urls)
            
            # Delete embeddings for this URL
            embeddings_result = delete_embeddings_by_source(url_to_delete)
            
            return f"Deleted URL: {url_to_delete}\n{embeddings_result}"
        else:
            return f"URL not found: {url_to_delete}"
    except Exception as e:
        return f"Error deleting URL: {str(e)}"



def delete_uploaded_file(filename: str):
    """Delete an uploaded file and its embeddings"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)
            
            # Delete embeddings for this file
            embeddings_result = delete_embeddings_by_source(file_path)
            
            return f"Deleted file: {filename}\n{embeddings_result}"
        else:
            return f"File not found: {filename}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def get_uploaded_files_list():
    """Get list of uploaded files with delete buttons"""
    files = []
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            full_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(full_path):
                files.append(filename)
    return files


with gr.Blocks() as demo:
    gr.Markdown("# 📘 Developer Docs Assistant")

    with gr.Tab("Upload Document"):
        with gr.Row():
            with gr.Column(scale=2):
                file = gr.File(label="Upload Document", file_types=[".pdf", ".txt", ".md", ".markdown"])
                upload_btn = gr.Button("📤 Ingest File", variant="primary")
                upload_output = gr.Textbox(label="Upload Result", visible=False)
                
                # Progress indicator
                upload_progress = gr.HTML(
                    value="<div style='text-align: center; color: #666;'>Ready to upload</div>",
                    label="Status"
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 📋 Upload Instructions")
                gr.Markdown("""
                1. **Select File**: Choose a PDF, TXT, or Markdown file
                2. **Click Upload**: The file will be processed and embedded
                3. **Wait**: Processing may take a few moments
                4. **Check Status**: Monitor the progress indicator
                """)

        def handle_upload_with_progress(file):
            if not file:
                return (
                    "⚠️ Please select a file first.", 
                    gr.update(visible=True),
                    gr.update(value="<div style='text-align: center; color: #ff6b6b;'>❌ No file selected</div>")
                )
            
            # Show processing status
            progress_html = """
            <div style='text-align: center; color: #4CAF50;'>
                <div style='margin-bottom: 10px;'>🔄 Processing file...</div>
                <div style='display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite;'></div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </div>
            """
            
            try:
                result = handle_file_upload_with_progress(file)
                success_html = f"""
                <div style='text-align: center; color: #4CAF50;'>
                    ✅ {result[0]}
                </div>
                """
                return result[0], gr.update(visible=True), gr.update(value=success_html)
            except Exception as e:
                error_html = f"""
                <div style='text-align: center; color: #ff6b6b;'>
                    ❌ Error: {str(e)}
                </div>
                """
                return f"❌ Error: {str(e)}", gr.update(visible=True), gr.update(value=error_html)

        upload_btn.click(
            handle_upload_with_progress,
            inputs=file,
            outputs=[upload_output, upload_output, upload_progress]
        )

    with gr.Tab("Ingest from URL"):
        with gr.Row():
            with gr.Column(scale=2):
                url_input = gr.Textbox(label="Document URL", placeholder="https://example.com/document")
                url_btn = gr.Button("🌐 Ingest URL", variant="primary")
                url_output = gr.Textbox(label="URL Processing Result", visible=False)
                
                # Progress indicator
                url_progress = gr.HTML(
                    value="<div style='text-align: center; color: #666;'>Ready to ingest URL</div>",
                    label="Status"
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 📋 URL Ingestion Instructions")
                gr.Markdown("""
                1. **Enter URL**: Paste a valid document URL
                2. **Click Ingest**: Content will be fetched and processed
                3. **Wait**: Processing may take a few moments
                4. **Check Status**: Monitor the progress indicator
                """)

        def handle_url_ingestion_with_progress_ui(url):
            if not url or not url.strip():
                return (
                    "⚠️ Please enter a valid URL.", 
                    gr.update(visible=True),
                    gr.update(value="<div style='text-align: center; color: #ff6b6b;'>❌ No URL provided</div>")
                )
            
            # Show processing status
            progress_html = """
            <div style='text-align: center; color: #4CAF50;'>
                <div style='margin-bottom: 10px;'>🔄 Fetching and processing URL...</div>
                <div style='display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #4CAF50; border-radius: 50%; animation: spin 1s linear infinite;'></div>
                <style>
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </div>
            """
            
            try:
                result = handle_url_ingestion_with_progress(url.strip())
                success_html = f"""
                <div style='text-align: center; color: #4CAF50;'>
                    ✅ {result[0]}
                </div>
                """
                return result[0], gr.update(visible=True), gr.update(value=success_html)
            except Exception as e:
                error_html = f"""
                <div style='text-align: center; color: #ff6b6b;'>
                    ❌ Error: {str(e)}
                </div>
                """
                return f"❌ Error: {str(e)}", gr.update(visible=True), gr.update(value=error_html)

        url_btn.click(
            handle_url_ingestion_with_progress_ui,
            inputs=url_input,
            outputs=[url_output, url_output, url_progress]
        )

    with gr.Tab("Manage Data"):
        gr.Markdown("# 🗂️ Data Management")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Uploaded Files")
                file_dropdown = gr.Dropdown(
                    label="Select File to Delete",
                    choices=get_uploaded_files_list(),
                    interactive=True
                )
                delete_file_btn = gr.Button("🗑️ Delete Selected File", variant="stop")
                file_delete_output = gr.Textbox(label="File Delete Result", visible=False)
                
                def delete_selected_file(filename):
                    if filename:
                        result = delete_uploaded_file(filename)
                        # Refresh the dropdown
                        new_choices = get_uploaded_files_list()
                        return gr.update(value=result, visible=True), gr.update(choices=new_choices)
                    return gr.update(value="No file selected", visible=True), gr.update()
                
                delete_file_btn.click(
                    delete_selected_file,
                    inputs=file_dropdown,
                    outputs=[file_delete_output, file_dropdown]
                )
                
                refresh_files_btn = gr.Button("🔄 Refresh File List")
                refresh_files_btn.click(
                    lambda: gr.update(choices=get_uploaded_files_list()),
                    outputs=file_dropdown
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### 🌐 Ingested URLs")
                # url_links_display = gr.HTML(value=get_saved_urls())
                url_dropdown = gr.Dropdown(
                    label="Select URL to Delete",
                    choices=get_saved_urls_list(),
                    interactive=True
                )
                delete_url_btn = gr.Button("🗑️ Delete Selected URL", variant="stop")
                url_delete_output = gr.Textbox(label="URL Delete Result", visible=False)
                
                def delete_selected_url(url):
                    if url:
                        result = delete_url_by_url(url)
                        # Refresh the dropdown and display
                        new_choices = get_saved_urls_list()
                        new_display = get_saved_urls()
                        return gr.update(value=result, visible=True), gr.update(choices=new_choices), gr.update(value=new_display)
                    return gr.update(value="No URL selected", visible=True), gr.update(), gr.update()
                
                delete_url_btn.click(
                    delete_selected_url,
                    inputs=url_dropdown,
                    outputs=[url_delete_output, url_dropdown]
                )
                
                refresh_urls_btn = gr.Button("🔄 Refresh URL List")
                refresh_urls_btn.click(
                    lambda: (gr.update(choices=get_saved_urls_list()), gr.update(value=get_saved_urls())),
                    outputs=[url_dropdown]
                )
        
        gr.Markdown("---")
        gr.Markdown("### ⚠️ Nuclear Option - Clear All Data")
        gr.Markdown("**Warning**: This will delete ALL uploaded files, ingested URLs, and clear the entire vector database. This action cannot be undone.")
        
        with gr.Row():
            clear_all_btn = gr.Button("💥 Clear All Data", variant="stop", size="lg")
            clear_output = gr.Textbox(label="Clear All Result", visible=False)
        
        def clear_all_data():
            # Clear database
            db_result = clear_database()
            
            # Clear uploaded files
            file_result = ""
            if os.path.exists(UPLOAD_DIR):
                for filename in os.listdir(UPLOAD_DIR):
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            file_result += f"Deleted file: {filename}\n"
                        except Exception as e:
                            file_result += f"Error deleting {filename}: {str(e)}\n"
            
            # Clear ingested URLs
            url_result = ""
            if os.path.exists(INGESTED_URLS_FILE):
                try:
                    os.remove(INGESTED_URLS_FILE)
                    url_result = "Deleted ingested URLs file\n"
                except Exception as e:
                    url_result = f"Error deleting URLs file: {str(e)}\n"
            
            return f"Database: {db_result}\nFiles: {file_result}URLs: {url_result}"
        
        clear_all_btn.click(
            clear_all_data,
            outputs=clear_output
        )
        
        # Load initial data
        demo.load(fn=lambda: gr.update(choices=get_uploaded_files_list()), outputs=file_dropdown)
        demo.load(fn=lambda: gr.update(choices=get_saved_urls_list()), outputs=url_dropdown)
        # demo.load(fn=get_saved_urls, outputs=url_links_display)

    with gr.Tab("Ask a Question"):
        with gr.Row():
            with gr.Column(scale=2):
                question_input = gr.Textbox(label="Your Question", placeholder="Ask a question about your documents...")
                ask_btn = gr.Button("🤖 Get Answer", variant="primary")
                answer_output = gr.Markdown(label="Answer", value="Answer will appear here...")
            
        
        def handle_question_with_sources(question):
            return answer_question(question)
        
        ask_btn.click(handle_question_with_sources, inputs=question_input, outputs=answer_output)


demo.launch()
