"""Arena Shooter - run with:  python main.py"""
from ursina import *

import config
from game import Game

app = Ursina(title=config.TITLE, borderless=False)
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

game = Game(app)

app.run()
