import json
import subprocess
import os
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DockerContainerManager:
    def __init__(self, base_port: int = 8000):
        self.base_port = base_port
        self.containers: List[str] = []
        self.load_apis()

    def load_apis(self) -> None:
        with open('db.json', 'r') as f:
            self.apis = json.load(f)['apis']
        
        # Assign ports to APIs
        for i, api in enumerate(self.apis):
            api['port'] = self.base_port + i

    def build_image(self) -> str:
        image_name = "api-runner:latest"
        subprocess.run(["docker", "build", "-t", image_name, "."], check=True)
        return image_name

    def start_container(self, api: Dict) -> None:
        container_name = f"api-runner-{api['id']}"
        
        # Stop and remove if container exists
        subprocess.run(["docker", "rm", "-f", container_name], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)

        # Start new container
        cmd = [
            "docker", "run",
            "-d",  # detached mode
            "--name", container_name,
            "-e", f"API_ID={api['id']}",
            "-p", f"{api['port']}:{api['port']}",
            "-v", f"{os.path.abspath('responses')}:/app/responses",
            "-v", f"{os.path.abspath('db.json')}:/app/db.json",
            "api-runner:latest"
        ]
        
        subprocess.run(cmd, check=True)
        logger.info(f"Started container {container_name} for API {api['name']} on port {api['port']}")
        self.containers.append(container_name)

    def start_all(self) -> None:
        try:
            # Create responses directory if it doesn't exist
            os.makedirs('responses', exist_ok=True)
            
            # Build the Docker image
            self.build_image()
            
            # Start containers for each API
            for api in self.apis:
                self.start_container(api)
                
            logger.info(f"Successfully started {len(self.apis)} containers")
            
        except Exception as e:
            logger.error(f"Error starting containers: {str(e)}")
            self.stop_all()
            raise

    def stop_all(self) -> None:
        for container in self.containers:
            subprocess.run(["docker", "stop", container], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            subprocess.run(["docker", "rm", container], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        logger.info("All containers stopped and removed")

def main():
    manager = DockerContainerManager()
    try:
        manager.start_all()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        manager.stop_all()

if __name__ == "__main__":
    main()