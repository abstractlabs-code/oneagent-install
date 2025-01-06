import os
import logging
import tempfile
import requests
import zipfile
from pathlib import Path
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def label_pod_on_failure(label_key="observable", label_value="false"):
    """
    Labels the current pod in case of failure using the Kubernetes Python client.
    """
    try:
        pod_name = os.getenv("POD_NAME")
        namespace = os.getenv("POD_NAMESPACE")
        if not pod_name or not namespace:
            raise ValueError("POD_NAME or POD_NAMESPACE environment variables are not set.")

        config.load_incluster_config()

        patch = {
            "metadata": {
                "labels": {
                    label_key: label_value
                }
            }
        }

        v1 = client.CoreV1Api()

        v1.patch_namespaced_pod(name=pod_name, namespace=namespace, body=patch)
        logger.info(f"Pod '{pod_name}' in namespace '{namespace}' labeled with '{label_key}={label_value}'")
    except ApiException as e:
        logger.error(f"Exception when calling CoreV1Api->patch_namespaced_pod: {e}")
    except Exception as e:
        logger.error(f"Failed to label pod: {e}")

def download_and_extract_oneagent(api_url, token, options, install_dir):
    """
    Downloads and extracts the OneAgent installer.
    """
    try:
        logger.info("Starting OneAgent installation process.")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            archive_path = temp_file.name
        logger.info(f"Temporary archive file created: {archive_path}")

        download_url = f"{api_url}/v1/deployment/installer/agent/unix/paas/latest?Api-Token={token}&{options}"
        logger.info(f"Downloading OneAgent from URL: {download_url}")

        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(archive_path, "wb") as archive_file:
            for chunk in response.iter_content(chunk_size=8192):
                archive_file.write(chunk)
        logger.info("Download completed successfully.")

        logger.info(f"Extracting installer to directory: {install_dir}")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(install_dir)
        logger.info("Extraction completed successfully.")

        Path(archive_path).unlink()
        logger.info("Temporary file deleted.")
    except Exception as e:
        logger.error(f"An error occurred during installation: {e}")
        label_pod_on_failure()
    finally:
        logger.info("Init container will exit successfully, regardless of the failure.")
        sys.exit(0)

def main():
    api_url = os.getenv("DT_API_URL")
    token = os.getenv("DT_PAAS_TOKEN")
    options = os.getenv("DT_ONEAGENT_OPTIONS")
    install_dir = "/opt/dynatrace/oneagent"

    if not api_url or not token or not options:
        logger.error("Required environment variables (DT_API_URL, DT_PAAS_TOKEN, DT_ONEAGENT_OPTIONS) are not set.")
        label_pod_on_failure()
        sys.exit(0)

    download_and_extract_oneagent(api_url, token, options, install_dir)
    logger.info("OneAgent installation completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        label_pod_on_failure()
        sys.exit(0)
