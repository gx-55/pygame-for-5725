from typing import Tuple

import pygame

from pythongame.core.common import *
from pythongame.core.game_data import KEYS_BY_ABILITY_TYPE

EXIT_ON_ESCAPE = False


class ActionExitGame:
    pass


class ActionTryUseAbility:
    def __init__(self, ability_type):
        self.ability_type = ability_type


class ActionTryUsePotion:
    def __init__(self, slot_number):
        self.slot_number = slot_number


class ActionMoveInDirection:
    def __init__(self, direction):
        self.direction = direction


class ActionStopMoving:
    pass


class ActionPauseGame:
    pass


class ActionPressSpaceKey:
    pass


class ActionPressShiftKey:
    pass


class ActionReleaseShiftKey:
    pass


class ActionSaveGameState:
    pass


class ActionToggleRenderDebugging:
    pass


class ActionToggleUiTalents:
    pass


class ActionToggleUiStats:
    pass


class ActionToggleUiHelp:
    pass


# Used for determining when user hovers over something in UI.
# TODO: Handle the dependency between user input and the visual interface in a better way
class ActionMouseMovement:
    def __init__(self, mouse_screen_position: Tuple[int, int]):
        self.mouse_screen_position = mouse_screen_position


# Used for dragging items in UI
class ActionMouseClicked:
    pass


# Used for dragging items in UI
class ActionMouseReleased:
    pass


class ActionRightMouseClicked:
    pass


class ActionChangeDialogOption:
    def __init__(self, index_delta: int):
        self.index_delta = index_delta


PYGAME_MOVEMENT_KEYS = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]
DIRECTION_BY_PYGAME_MOVEMENT_KEY = {
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT,
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN
}

PYGAME_MOUSE_LEFT_BUTTON = 1
PYGAME_MOUSE_RIGHT_BUTTON = 3


def get_dialog_user_inputs() -> List[Any]:
    actions = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(ActionExitGame())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and EXIT_ON_ESCAPE:
                actions.append(ActionExitGame())
            elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                actions.append(ActionChangeDialogOption(-1))
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                actions.append(ActionChangeDialogOption(1))
            elif event.key == pygame.K_SPACE:
                actions.append(ActionPressSpaceKey())
            elif event.key == pygame.K_s:
                actions.append(ActionSaveGameState())
    return actions


def get_paused_user_inputs() -> List[Any]:
    actions = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(ActionExitGame())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and EXIT_ON_ESCAPE:
                actions.append(ActionExitGame())
            elif event.key == pygame.K_RETURN:
                actions.append(ActionPauseGame())
    return actions


class PlayingUserInputHandler:
    def __init__(self):
        self._movement_keys_down = []
        self._ability_keys_down: List[AbilityType] = []

    def get_main_user_inputs(self) -> List[Any]:
        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                actions.append(ActionExitGame())
            if event.type == pygame.KEYDOWN:
                if event.key in PYGAME_MOVEMENT_KEYS:
                    if event.key in self._movement_keys_down:
                        self._movement_keys_down.remove(event.key)
                    self._movement_keys_down.append(event.key)
                elif event.key == pygame.K_1:
                    actions.append(ActionTryUsePotion(1))
                elif event.key == pygame.K_2:
                    actions.append(ActionTryUsePotion(2))
                elif event.key == pygame.K_3:
                    actions.append(ActionTryUsePotion(3))
                elif event.key == pygame.K_4:
                    actions.append(ActionTryUsePotion(4))
                elif event.key == pygame.K_5:
                    actions.append(ActionTryUsePotion(5))
                elif event.key == pygame.K_0:
                    actions.append(ActionToggleRenderDebugging())
                elif event.key == pygame.K_ESCAPE and EXIT_ON_ESCAPE:
                    actions.append(ActionExitGame())
                elif event.key == pygame.K_RETURN:
                    actions.append(ActionPauseGame())
                elif event.key == pygame.K_SPACE:
                    actions.append(ActionPressSpaceKey())
                elif event.key == pygame.K_LSHIFT:
                    actions.append(ActionPressShiftKey())
                elif event.key == pygame.K_s:
                    actions.append(ActionSaveGameState())
                elif event.key == pygame.K_n:
                    actions.append(ActionToggleUiTalents())
                elif event.key == pygame.K_a:
                    actions.append(ActionToggleUiStats())
                elif event.key == pygame.K_h:
                    actions.append(ActionToggleUiHelp())
                else:
                    for ability_type in KEYS_BY_ABILITY_TYPE:
                        if event.key == KEYS_BY_ABILITY_TYPE[ability_type].pygame_key:
                            if ability_type in self._ability_keys_down:
                                self._ability_keys_down.remove(ability_type)
                            self._ability_keys_down.append(ability_type)

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    actions.append(ActionReleaseShiftKey())
                elif event.key in PYGAME_MOVEMENT_KEYS:
                    if event.key in self._movement_keys_down:
                        self._movement_keys_down.remove(event.key)
                else:
                    for ability_type in KEYS_BY_ABILITY_TYPE:
                        if event.key == KEYS_BY_ABILITY_TYPE[ability_type].pygame_key:
                            if ability_type in self._ability_keys_down:
                                self._ability_keys_down.remove(ability_type)

            if event.type == pygame.MOUSEMOTION:
                actions.append(ActionMouseMovement(event.pos))

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == PYGAME_MOUSE_LEFT_BUTTON:
                    actions.append(ActionMouseClicked())
                elif event.button == PYGAME_MOUSE_RIGHT_BUTTON:
                    actions.append(ActionRightMouseClicked())

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == PYGAME_MOUSE_LEFT_BUTTON:
                    actions.append(ActionMouseReleased())

        if self._movement_keys_down:
            last_pressed_movement_key = self._movement_keys_down[-1]
            direction = DIRECTION_BY_PYGAME_MOVEMENT_KEY[last_pressed_movement_key]
            actions.append(ActionMoveInDirection(direction))
        else:
            actions.append(ActionStopMoving())

        for ability_type in self._ability_keys_down:
            actions.append(ActionTryUseAbility(ability_type))

        return actions
