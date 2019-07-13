from typing import Optional, Tuple

from pythongame.core.common import Sprite, WallType, NpcType, ConsumableType, ItemType, PortalId, HeroId
from pythongame.core.entity_creation import create_portal, create_hero_world_entity, create_npc, create_wall, \
    create_consumable_on_ground, create_item_on_ground, create_decoration_entity, create_money_pile_on_ground


class MapEditorWorldEntity:
    def __init__(self, sprite: Sprite, entity_size: Tuple[int, int]):
        self.sprite = sprite
        self.entity_size = entity_size
        self.npc_type: NpcType = None
        self.is_player: bool = False
        self.wall_type: Optional[WallType] = None
        self.consumable_type: Optional[ConsumableType] = None
        self.item_type: Optional[ItemType] = None
        self.decoration_sprite: Optional[Sprite] = None
        self.money_amount: Optional[int] = None
        self.portal_id: Optional[PortalId] = None

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        # No need for efficiency in this class
        return 0

    @staticmethod
    def player():
        # The choice of hero shouldn't matter in the map editor, as we only store its position in the map file
        entity = create_hero_world_entity(HeroId.MAGE, (0, 0))
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.is_player = True
        return e

    @staticmethod
    def npc(npc_type: NpcType):
        entity = create_npc(npc_type, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.npc_type = npc_type
        return e

    @staticmethod
    def wall(wall_type: WallType):
        entity = create_wall(wall_type, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.wall_type = wall_type
        return e

    @staticmethod
    def consumable(consumable_type: ConsumableType):
        entity = create_consumable_on_ground(consumable_type, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.consumable_type = consumable_type
        return e

    @staticmethod
    def item(item_type: ItemType):
        entity = create_item_on_ground(item_type, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.item_type = item_type
        return e

    @staticmethod
    def decoration(sprite: Sprite):
        decoration_entity = create_decoration_entity((0, 0), sprite)
        e = MapEditorWorldEntity(decoration_entity.sprite, (0, 0))
        e.decoration_sprite = sprite
        return e

    @staticmethod
    def money(amount: int):
        entity = create_money_pile_on_ground(amount, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.money_amount = amount
        return e

    @staticmethod
    def portal(portal_id: PortalId):
        entity = create_portal(portal_id, (0, 0)).world_entity
        e = MapEditorWorldEntity(entity.sprite, (entity.w, entity.h))
        e.portal_id = portal_id
        return e
