from pythongame.core.common import ItemType, Sprite, UiIconSprite, HeroStat
from pythongame.core.item_inventory import ItemEquipmentCategory
from pythongame.game_data.items.register_items_util import register_stat_modifying_item


def register_wooden_shield():
    register_stat_modifying_item(
        item_type=ItemType.WOODEN_SHIELD,
        ui_icon_sprite=UiIconSprite.ITEM_WOODEN_SHIELD,
        sprite=Sprite.ITEM_WOODEN_SHIELD,
        image_file_path="resources/graphics/item_wooden_shield.png",
        item_equipment_category=ItemEquipmentCategory.OFF_HAND,
        name="Wooden Shield",
        stat_modifiers={HeroStat.ARMOR: 1, HeroStat.BLOCK_AMOUNT: 3}
    )
