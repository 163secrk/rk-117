import requests
from PySide6.QtCore import QObject, Signal, QThread

BASE_URL = "http://localhost:8117"


class ApiWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ApiClient(QObject):
    def __init__(self):
        super().__init__()
        self.base_url = BASE_URL
        self._threads = []
        self._workers = []

    def _run_async(self, func, callback, error_callback=None, *args, **kwargs):
        thread = QThread()
        worker = ApiWorker(func, *args, **kwargs)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)

        worker.finished.connect(callback)
        if error_callback:
            worker.error.connect(error_callback)

        def _cleanup():
            thread.wait()
            if thread in self._threads:
                self._threads.remove(thread)
            if worker in self._workers:
                self._workers.remove(worker)

        thread.finished.connect(_cleanup)

        self._threads.append(thread)
        self._workers.append(worker)

        thread.start()

    def get_player_sync(self):
        try:
            resp = requests.get(f"{self.base_url}/api/player", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_equipment_sync(self):
        try:
            resp = requests.get(f"{self.base_url}/api/equipment", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_upgrade_info_sync(self, equipment_id):
        try:
            resp = requests.get(f"{self.base_url}/api/upgrade/info/{equipment_id}", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def upgrade_equipment_sync(self, equipment_id, use_protect_scroll=False, use_lucky_charm=False):
        try:
            resp = requests.post(
                f"{self.base_url}/api/upgrade/{equipment_id}",
                json={"use_protect_scroll": use_protect_scroll, "use_lucky_charm": use_lucky_charm},
                timeout=5
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def buy_stones_sync(self, amount):
        try:
            resp = requests.post(f"{self.base_url}/api/shop/buy_stones/{amount}", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def buy_protect_scrolls_sync(self, amount):
        try:
            resp = requests.post(f"{self.base_url}/api/shop/buy_protect_scrolls/{amount}", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def buy_lucky_charms_sync(self, amount):
        try:
            resp = requests.post(f"{self.base_url}/api/shop/buy_lucky_charms/{amount}", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_player_power_sync(self):
        try:
            resp = requests.get(f"{self.base_url}/api/wild/player_power", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def hunt_monster_sync(self):
        try:
            resp = requests.post(f"{self.base_url}/api/wild/hunt", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_player(self, callback, error_callback=None):
        self._run_async(self.get_player_sync, callback, error_callback)

    def get_equipment(self, callback, error_callback=None):
        self._run_async(self.get_equipment_sync, callback, error_callback)

    def get_upgrade_info(self, equipment_id, callback, error_callback=None):
        self._run_async(self.get_upgrade_info_sync, callback, error_callback, equipment_id)

    def upgrade_equipment(self, equipment_id, callback, error_callback=None, use_protect_scroll=False, use_lucky_charm=False):
        self._run_async(
            self.upgrade_equipment_sync, callback, error_callback,
            equipment_id, use_protect_scroll, use_lucky_charm
        )

    def buy_stones(self, amount, callback, error_callback=None):
        self._run_async(self.buy_stones_sync, callback, error_callback, amount)

    def buy_protect_scrolls(self, amount, callback, error_callback=None):
        self._run_async(self.buy_protect_scrolls_sync, callback, error_callback, amount)

    def buy_lucky_charms(self, amount, callback, error_callback=None):
        self._run_async(self.buy_lucky_charms_sync, callback, error_callback, amount)

    def get_player_power(self, callback, error_callback=None):
        self._run_async(self.get_player_power_sync, callback, error_callback)

    def hunt_monster(self, callback, error_callback=None):
        self._run_async(self.hunt_monster_sync, callback, error_callback)
