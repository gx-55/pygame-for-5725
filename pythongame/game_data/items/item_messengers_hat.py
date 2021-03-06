from pythongame.core.common import ItemType, Sprite, HeroStat
from pythongame.core.game_data import UiIconSprite
from pythongame.core.item_inventory import ItemEquipmentCategory
from pythongame.game_data.items.register_items_util import register_stat_modifying_item


def register_messengers_hat_item():
    register_stat_modifying_item(
        item_type=ItemType.MESSENGERS_HAT,
        ui_icon_sprite=UiIconSprite.ITEM_MESSENGERS_HAT,
        sprite=Sprite.ITEM_MESSENGERS_HAT,
        image_file_path="resources/graphics/item_messengers_hat.png",
        item_equipment_category=ItemEquipmentCategory.HEAD,
        name="Messenger's hat",
        stat_modifiers={HeroStat.MOVEMENT_SPEED: 0.2}
    )
