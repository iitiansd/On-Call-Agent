import re
import requests
from datetime import datetime
from typing import Dict, List
from app.core.config import settings


class ObserveLogsFetcher:
    def __init__(self):
        # Initialize with the Observe API key from settings
        self.observe_api_key = settings.OBSERVE_API_KEY

    def fetch_logs(self, observe_logs_url: str) -> List[Dict]:
        """Fetch logs from the Observe API using the extracted URL"""
        try:
            # Parse the Observe Logs URL to extract parameters
            parsed_url = self._parse_observe_logs_url(observe_logs_url)
            if not parsed_url:
                return []

            dataset_id = parsed_url["datasetId"]
            resource_id = parsed_url["resourceId"]
            env = parsed_url["env"]
            start_time = parsed_url["start_time"]
            end_time = parsed_url["end_time"]

            # Convert timestamps to ISO 8601 format
            start_time_iso = self._convert_timestamp_to_iso(start_time)
            end_time_iso = self._convert_timestamp_to_iso(end_time)

            # Construct the Observe API request payload
            payload = {
                "query": {
                    "stages": [
                        {
                            "input": [
                                {
                                    "inputName": "system",
                                    "datasetId": dataset_id
                                }
                            ],
                            "stageID": "main",
                            "pipeline": f'filter env = "{env}"\nfilter resourceId = "{resource_id}"\nfilter not message ~ /Audit Request (Finished|Initiated) Event/\npick_col message, timestamp,dims\nsort desc(timestamp)\nlimit 10'
                        }
                    ]
                }
            }

            import pdb; pdb.set_trace()
            # Make the Observe API request
            observe_url = f"https://{parsed_url['domain']}/v1/meta/export/query?startTime={start_time_iso}&endTime={end_time_iso}"
            headers = {
                "Authorization": f"Bearer {self.observe_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/x-ndjson"
            }

            response = requests.post(observe_url, headers=headers, json=payload)

            if response.status_code == 200:
                # Parse the response (assuming it's in NDJSON format)
                logs = response.text.strip().split("\n")
                return [self._parse_log_entry(log) for log in logs]
            else:
                print(f"Failed to fetch logs from Observe API: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching logs from Observe API: {e}")
            return []

    def _parse_observe_logs_url(self, url: str) -> Dict:
        """Parse the Observe Logs URL to extract parameters safely"""
        try:
            url = url.strip('"')
            print(f"Parsing Observe Logs URL: {url}")  # Debugging line


            print(f"URL received: {url}")
            # Extract values using regex (handle None cases properly)
            domain_match = re.search(r"https://([\w.-]+\.observeinc\.com)", url)
            dataset_match = re.search(r"[?&]datasetId=(\d+)", url)
            resource_match = re.search(r"[?&]filter-resourceId=([^&]+)", url)
            env_match = re.search(r"[?&]filter-env=([^&]+)", url)
            start_time_match = re.search(r"[?&]time-start=(\d+)", url)
            end_time_match = re.search(r"[?&]time-end=(\d+)", url)


            import pdb; pdb.set_trace()
            if not domain_match:
                print("Error: Domain is missing in the URL.")
            if not dataset_match:
                print("Error: Dataset ID is missing in the URL.")
            if not resource_match:
                print("Error: Resource ID is missing in the URL.")
            if not env_match:
                print("Error: Environment is missing in the URL.")
            if not start_time_match:
                print("Error: Start time is missing in the URL.")
            if not end_time_match:
                print("Error: End time is missing in the URL.")
            if not all([domain_match, dataset_match, resource_match, start_time_match, end_time_match]):
                print("Error: One or more required parameters are missing in the URL.")
                return {}

            import pdb; pdb.set_trace()
            env = env_match.group(1) if env_match else "prod1-default"
            return {
                "domain": domain_match.group(1),
                "datasetId": dataset_match.group(1),
                "resourceId": resource_match.group(1),
                "env": env,
                "start_time": int(start_time_match.group(1)),
                "end_time": int(end_time_match.group(1))
            }
        except Exception as e:
            print(f"Error parsing Observe Logs URL: {e}")
            return {}


    def _convert_timestamp_to_iso(self, timestamp_ms: int) -> str:
        """Convert a timestamp in milliseconds to ISO 8601 format in UTC"""
        timestamp_seconds = timestamp_ms / 1000
        return datetime.utcfromtimestamp(timestamp_seconds).isoformat() + "Z"

    def _parse_log_entry(self, log_entry: str) -> Dict:
        """Parse a single log entry from the Observe API response"""
        try:
            return eval(log_entry)  # Convert NDJSON string to dictionary
        except Exception as e:
            print(f"Error parsing log entry: {e}")
            return {}