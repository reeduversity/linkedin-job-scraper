import modal

# Define the Modal App
app = modal.App("linkedin-job-scraper")

# Define the image: standard Python, install requirements,
# and copy ONLY the backend source code (not .git, .venv, frontend, etc.)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .add_local_dir("app", remote_path="/root/linkedin-job-scraper/app")
    .add_local_file("main.py", remote_path="/root/linkedin-job-scraper/main.py")
    .add_local_file("requirements.txt", remote_path="/root/linkedin-job-scraper/requirements.txt")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=300,
    scaledown_window=120,
)
@modal.asgi_app()
def fastapi_app():
    import os
    import sys

    project_root = "/root/linkedin-job-scraper"
    os.chdir(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Import the FastAPI instance from our existing code
    from app.main_api import app as web_app
    return web_app
