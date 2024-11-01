from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import logging
import os
import re
import requests
import smtplib
import subprocess
import unicodedata
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from bs4 import BeautifulSoup

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = os.getenv("SMTP_PORT", 587)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
KINDLE_EMAIL = os.getenv("KINDLE_EMAIL")
SENDS_FOLDER = "sends"

app = FastAPI()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
class ArticleRequest(BaseModel):
    url: HttpUrl

def sanitize_title(title: str) -> str:
    """
    Sanitizes a title string by normalizing special characters and replacing any non-alphanumeric
    characters with an underscore. This is useful for generating a filename from a title.

    Args:
        title (str): The title string to sanitize

    Returns:
        str: The sanitized title string
    """
    normalized = unicodedata.normalize("NFKD", title)
    # Replace any character that is not a letter, number, or whitespace with an underscore
    sanitized = re.sub(r'[^\w\s-]', '_', normalized)
    # Replace spaces with underscores and strip any leading/trailing whitespace
    sanitized = sanitized.replace(" ", "_").strip("_")
    return sanitized


def get_unique_filename(base_name: str, extension: str) -> str:
    """
    Generates a unique filename by appending a counter to the base name if the desired filename
    already exists.

    Args:
        base_name (str): The base name of the file
        extension (str): The file extension

    Returns:
        str: A unique filename
    """
    filename = f"{base_name}.{extension}"
    counter = 1
    while os.path.exists(os.path.join(SENDS_FOLDER, filename)):
        logging.info(f"File {filename} already exists. Renaming...")
        filename = f"{base_name}_{counter}.{extension}"
        counter += 1
    logging.info(f"Saving file as {filename}")
    return filename


def download_html(url:str) -> str | None:
    """
    Downloads the HTML content of a webpage at the given URL and saves it to a local file.

    Args:
        url (str): The URL of the webpage to download

    Returns:
        html_file (str): The filename of the saved HTML file
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")
        title = sanitize_title(soup.title.string if soup.title else "article")
        html_file = get_unique_filename(title, "html")

        with open(os.path.join(SENDS_FOLDER, html_file), "w", encoding="utf-8") as file:
            file.write(html_content)
        logging.info(f"HTML content downloaded with title: {title}")
        return html_file
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while downloading the HTML content: {e}")
        return None

def convert_html_to_epub(html_file: str) -> str | None:
    """
    Converts an HTML file to an EPUB file using Pandoc.

    Args:
        html_file (str): The filename of the HTML file to convert

    Returns:
        epub_file (str): The filename of the generated EPUB file
    """
    epub_file = html_file.replace(".html", ".epub")
    try:
        subprocess.run(["pandoc", "-f", "html", "-t", "epub3", "-o", os.path.join(SENDS_FOLDER, epub_file), os.path.join(SENDS_FOLDER, html_file)], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while converting the HTML file to EPUB: {e}")
        return None
    return epub_file

def send_to_kindle(epub_file: str) -> bool:
    """
    Sends an email to the Kindle email address with the given EPUB file attached.

    Args:
        epub_file (str): The path to the EPUB file to send
    """
    msg = MIMEMultipart()
    msg["From"] = formataddr(("Sender Name", EMAIL_ADDRESS))
    msg["To"] = KINDLE_EMAIL
    msg["Subject"] = "convert"

    with open(os.path.join(SENDS_FOLDER, epub_file), "rb") as file:
        part = MIMEApplication(file.read(), Name=os.path.basename(epub_file))
    part["Content-Disposition"] = f'attachment; filename="{os.path.basename(epub_file)}"'
    msg.attach(part)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        try:
            server.sendmail(EMAIL_ADDRESS, KINDLE_EMAIL, msg.as_string())
            return True
        except smtplib.SMTPException as e:
            logging.error(f"An error occurred while sending the email: {e}")
            return False


@app.post("/send-article")
async def send_article(request: ArticleRequest) -> dict:
    url = request.url
    html_file = download_html(url)
    if not html_file:
        logging.error("Failed to download HTML content.")
        raise HTTPException(status_code=400, detail="Failed to download HTML content.")  
    epub_file = convert_html_to_epub(html_file)
    if not epub_file:
        raise HTTPException(status_code=500, detail="Failed to convert HTML to EPUB.")
    if not send_to_kindle(epub_file):
        raise HTTPException(status_code=500, detail="Failed to send EPUB file to Kindle.") 
    return {"status": "success", "message": f"Article '{epub_file[:-5]}' sent to Kindle."}


@app.post("/cleanup")
async def cleanup():
    try:
        for filename in os.listdir(SENDS_FOLDER):
            file_path = os.path.join(SENDS_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Deleted file: {file_path}")
        return {"status": "success", "message": "All files deleted from SENDS_FOLDER."}
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean up files.")