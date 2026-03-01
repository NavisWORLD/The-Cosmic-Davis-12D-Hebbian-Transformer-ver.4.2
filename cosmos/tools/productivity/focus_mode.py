"""
<<<<<<< HEAD:cosmos/tools/productivity/focus_mode.py
cosmos Focus Mode (Cone of Silence)
=======
Farnsworth Focus Mode (Cone of Silence)
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/focus_mode.py
---------------------------------------

"Quiet, you!"

Edits the HOSTS file to temporarily block distraction sites.
"""

import sys
import os
from loguru import logger

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if sys.platform == "win32" else "/etc/hosts"
DISTRACTIONS = [
    "twitter.com", "x.com", "facebook.com", "instagram.com", "reddit.com", "news.ycombinator.com"
]

class ConeOfSilence:
    def enable(self):
        """Block sites."""
        try:
            with open(HOSTS_PATH, "r") as f:
                content = f.read()
            
            with open(HOSTS_PATH, "a") as f:
<<<<<<< HEAD:cosmos/tools/productivity/focus_mode.py
                f.write("\n# cosmos CONE OF SILENCE START\n")
=======
                f.write("\n# FARNSWORTH CONE OF SILENCE START\n")
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/focus_mode.py
                for site in DISTRACTIONS:
                    if site not in content:
                        f.write(f"127.0.0.1 {site}\n")
                        f.write(f"127.0.0.1 www.{site}\n")
<<<<<<< HEAD:cosmos/tools/productivity/focus_mode.py
                f.write("# cosmos CONE OF SILENCE END\n")
=======
                f.write("# FARNSWORTH CONE OF SILENCE END\n")
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/focus_mode.py
            
            logger.info("🤫 Cone of Silence ENABLED. Distractions blocked.")
        except PermissionError:
            logger.error("❌ Need Admin/Root privileges to modify HOSTS file.")

    def disable(self):
        """Unblock sites."""
        try:
            with open(HOSTS_PATH, "r") as f:
                lines = f.readlines()
            
            with open(HOSTS_PATH, "w") as f:
                in_block = False
                for line in lines:
<<<<<<< HEAD:cosmos/tools/productivity/focus_mode.py
                    if "# cosmos CONE OF SILENCE START" in line:
                        in_block = True
                        continue
                    if "# cosmos CONE OF SILENCE END" in line:
=======
                    if "# FARNSWORTH CONE OF SILENCE START" in line:
                        in_block = True
                        continue
                    if "# FARNSWORTH CONE OF SILENCE END" in line:
>>>>>>> dd5db7d5307d56ce54f13e61b92f95333530d4d1:farnsworth/tools/productivity/focus_mode.py
                        in_block = False
                        continue
                    
                    if not in_block:
                        f.write(line)
                        
            logger.info("🔊 Cone of Silence DISABLED.")
        except PermissionError:
            logger.error("❌ Need Admin/Root privileges.")

focus_mode = ConeOfSilence()
