from typing import Dict, Type

from pythongame.common import *
from pythongame.game_state import GameState, Enemy, WorldEntity


class AbstractEnemyMind:
    def control_enemy(self,
                      game_state: GameState,
                      enemy: Enemy,
                      player_entity: WorldEntity,
                      is_player_invisible: bool,
                      time_passed: Millis):
        pass


_enemy_mind_constructors: Dict[EnemyBehavior, Type[AbstractEnemyMind]] = {}


def register_enemy_behavior(enemy_behavior: EnemyBehavior, mind_constructor: Type[AbstractEnemyMind]):
    _enemy_mind_constructors[enemy_behavior] = mind_constructor


def create_enemy_mind(enemy_behavior: EnemyBehavior):
    return _enemy_mind_constructors[enemy_behavior]()
