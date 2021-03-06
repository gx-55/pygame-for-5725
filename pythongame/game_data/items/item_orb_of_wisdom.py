from pythongame.core.common import ItemType, Sprite, UiIconSprite, HeroStat
from pythongame.core.game_data import register_ui_icon_sprite_path, register_item_data, ItemData, \
    register_entity_sprite_initializer, ITEM_ENTITY_SIZE
from pythongame.core.item_effects import register_item_effect, StatModifyingItemEffect
from pythongame.core.item_inventory import ItemEquipmentCategory
from pythongame.core.view.image_loading import SpriteInitializer


def register_orb_of_wisdom_item():
    item_types = [ItemType.ORB_OF_WISDOM_1, ItemType.ORB_OF_WISDOM_2, ItemType.ORB_OF_WISDOM_3]
    bonuses = [0.5, 0.75, 1]
    ui_icon_sprite = UiIconSprite.ITEM_ORB_OF_WISDOM
    sprite = Sprite.ITEM_ORB_OF_WISDOM
    image_file_path = "resources/graphics/item_orb_of_wisdom.png"
    register_ui_icon_sprite_path(ui_icon_sprite, image_file_path)
    register_entity_sprite_initializer(
        sprite, SpriteInitializer(image_file_path, ITEM_ENTITY_SIZE))
    for i in range(3):
        item_type = item_types[i]
        bonus = bonuses[i]
        effect = StatModifyingItemEffect(item_type, {HeroStat.MANA_REGEN: bonus})
        register_item_effect(item_type, effect)
        name = "Orb of Wisdom (" + str(i + 1) + ")"
        description = effect.get_description()
        item_data = ItemData(ui_icon_sprite, sprite, name, description, ItemEquipmentCategory.OFF_HAND)
        register_item_data(item_type, item_data)
