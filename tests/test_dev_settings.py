"""Host and Docker worker must share the local database, queue and notifications."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DevelopmentSettingsTests(unittest.TestCase):
    def test_worker_shares_local_overrides_without_disabling_tasks_or_telegram(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings").mkdir()
            for name in ("__init__.py", "base.py", "dev.py", "dev_worker.py"):
                shutil.copy(ROOT / "settings" / name, root / "settings" / name)
            (root / "settings/local.py").write_text(
                "from copy import deepcopy\nfrom .base import DATABASES as original\n"
                "DATABASES = deepcopy(original)\n"
                'DATABASES["default"].update(NAME="restored-local", HOST="127.0.0.1", PORT="5433")\n'
                'MEDIA_ROOT = "/tmp/restored-local-media"\n'
            )
            script = (
                "import importlib,json,sys; s=importlib.import_module(sys.argv[1]); "
                'print(json.dumps({"database": s.DATABASES["default"], "media": str(s.MEDIA_ROOT), '
                '"tasks": s.TASKS, "token": s.TELEGRAM_BOT_TOKEN, "chat": s.TELEGRAM_NOTIFICATIONS_CHAT_ID}))'
            )
            configurations = []
            for module, host, port in (("settings.dev", "127.0.0.1", "5433"), ("settings.dev_worker", "db", "5432")):
                env = {
                    "PATH": os.defpath,
                    "DJANGO_LOAD_DOTENV": "0",
                    "DB_HOST": host,
                    "DB_PORT": port,
                    "DB_NAME": "original-local",
                    "TELEGRAM_BOT_TOKEN": "synthetic-test-token",
                    "TELEGRAM_NOTIFICATIONS_CHAT_ID": "synthetic-test-chat",
                    "PYTHONDONTWRITEBYTECODE": "1",
                }
                result = subprocess.run(
                    [sys.executable, "-c", script, module],
                    cwd=root,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                config = json.loads(result.stdout)
                self.assertEqual(config["database"]["NAME"], "restored-local")
                self.assertEqual(config["database"]["HOST"], host)
                self.assertEqual(config["database"]["PORT"], port)
                self.assertEqual(config["tasks"]["default"]["BACKEND"], "django_tasks_db.DatabaseBackend")
                self.assertEqual(config["token"], "synthetic-test-token")
                self.assertEqual(config["chat"], "synthetic-test-chat")
                configurations.append(config)
            for field in ("media", "tasks", "token", "chat"):
                self.assertEqual(configurations[0][field], configurations[1][field])
