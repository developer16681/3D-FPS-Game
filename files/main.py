"""Arena Shooter - run with:  python main.py"""
import os
import sys
from pathlib import Path

# Ensure nested game directory is on path and cwd
game_dir = Path(__file__).resolve().parent / "ursina_fps" / "ursina_fps"
if game_dir.is_dir() and str(game_dir) not in sys.path:
    sys.path.insert(0, str(game_dir))
    os.chdir(str(game_dir))

from ursina import *

import config
from game import Game

app = Ursina(title=config.TITLE, borderless=False)
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

game = Game(app)

app.run()
