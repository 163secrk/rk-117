import requests

BASE_URL = "http://localhost:8117"


class ApiClient:
    def __init__(self):
        self.base_url = BASE_URL

    def get_player(self):
        try:
            resp = requests.get(f"{self.base_url}/api/player")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_equipment(self):
        try:
            resp = requests.get(f"{self.base_url}/api/equipment")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_upgrade_info(self, equipment_id):
        try:
            resp = requests.get(f"{self.base_url}/api/upgrade/info/{equipment_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def upgrade_equipment(self, equipment_id):
        try:
            resp = requests.post(f"{self.base_url}/api/upgrade/{equipment_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
