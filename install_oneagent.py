import os
import tempfile
import logging
import requests
import zipfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        dt_api_url = os.getenv("DT_API_URL")
        dt_paas_token = os.getenv("DT_PAAS_TOKEN")
        dt_oneagent_options = os.getenv("DT_ONEAGENT_OPTIONS")
        output_dir = "/opt/dynatrace/oneagent"

        if not all([dt_api_url, dt_paas_token, dt_oneagent_options]):
            logger.error("One or more required environment variables are missing: "
                         "DT_API_URL, DT_PAAS_TOKEN, DT_ONEAGENT_OPTIONS")
            raise ValueError("Missing required environment variables")

        url = f"{dt_api_url}/v1/deployment/installer/agent/unix/paas/latest"
        params = {
            "Api-Token": dt_paas_token,
            **dict(item.split("=") for item in dt_oneagent_options.split("&") if "=" in item)
        }
        logger.info(f"Constructed URL: {url}")

        archive_path = tempfile.NamedTemporaryFile(delete=False).name
        logger.info(f"Temporary archive file created at {archive_path}")

        logger.info("Downloading the installer...")
        response = requests.get(url, params=params, stream=True)
        response.raise_for_status()

        with open(archive_path, "wb") as archive_file:
            for chunk in response.iter_content(chunk_size=8192):
                archive_file.write(chunk)
        logger.info("Download completed successfully.")

        logger.info(f"Extracting the archive to {output_dir}...")
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as archive:
            archive.extractall(output_dir)
        logger.info("Extraction completed successfully.")

        logger.info("Cleaning up temporary files...")
        Path(archive_path).unlink()
        logger.info("Temporary files cleaned up successfully.")

    except requests.RequestException as req_err:
        logger.error(f"Request failed: {req_err}")
        raise
    except zipfile.BadZipFile as zip_err:
        logger.error(f"Failed to extract the archive: {zip_err}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
