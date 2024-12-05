import json
import requests
import logging
import os
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIRunner:
    def __init__(self, api_config: Dict[str, Any]):
        self.api_config = api_config
        self.name = api_config['name']
        self.url = api_config['url']
        self.method = api_config['method']
        self.headers = api_config.get('headers', {})
        self.port = api_config.get('port', 8000)
    
    def call_api(self) -> Dict[str, Any]:
        try:
            logger.info(f"Calling {self.name} on port {self.port}")
            request_func = getattr(requests, self.method.lower())
            response = request_func(self.url, headers=self.headers)
            
            result = {
                'api_name': self.name,
                'port': self.port,
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat(),
                'response': response.json()
            }
            
            logger.info(f"{self.name} response status: {response.status_code}")
            return result
            
        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
            return {
                'api_name': self.name,
                'port': self.port,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

def load_api_config() -> Dict[str, Any]:
    api_id = int(os.environ.get('API_ID', 1))
    with open('db.json', 'r') as f:
        apis = json.load(f)['apis']
        return next(api for api in apis if api['id'] == api_id)

def save_response(response: Dict[str, Any]) -> None:
    filename = f"responses/{response['api_name']}.json"
    
    os.makedirs('responses', exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(response, f, indent=2)
    logger.info(f"Saved response to {filename}")

def main():
    try:
        api_config = load_api_config()
        runner = APIRunner(api_config)
        response = runner.call_api()
        save_response(response)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()