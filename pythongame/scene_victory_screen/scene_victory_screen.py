import sys
from typing import Optional

import pygame

from pythongame.core.common import Millis, AbstractScene, SceneTransition
from pythongame.core.view.render_util import DrawableArea

COLOR_BLACK = (0, 0, 0)
DIR_FONTS = './resources/fonts/'


def handle_user_input():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


class VictoryScreenScene(AbstractScene):
    def __init__(self, pygame_screen):
        self.screen_render = DrawableArea(pygame_screen)
        self.font = pygame.font.Font(DIR_FONTS + 'Merchant Copy.ttf', 24)
        self.time_since_start = Millis(0)

    def run_one_frame(self, time_passed: Millis) -> Optional[SceneTransition]:
        handle_user_input()
        self.time_since_start += time_passed
        self.render()
        return None

    def render(self):
        self.screen_render.fill(COLOR_BLACK)
        x = 70
        lines_y = [200,
                   325, 350,
                   500, 525, 550]
        text_lines = [
            " Well done! You have finished the demo version of this game!",

            "           Don't hesitate to drop any feedback at",
            "   https://github.com/JonathanMurray/python-2d-game/issues  ",

            "                      /",
            "                  O===[====================-",
            "                      \\"
        ]

        num_chars_to_show = self.time_since_start // 30
        accumulated = 0
        for i in range(len(text_lines)):
            if num_chars_to_show > accumulated:
                line = text_lines[i]
                self.screen_render.text(self.font, line[:num_chars_to_show - accumulated], (x, lines_y[i]))
                accumulated += len(line)

        pygame.display.update()
