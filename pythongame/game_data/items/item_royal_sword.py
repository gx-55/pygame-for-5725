from pythongame.core.common import ItemType, Sprite, UiIconSprite, HeroStat
from pythongame.core.game_data import register_ui_icon_sprite_path, register_item_data, ItemData, \
    register_entity_sprite_initializer, ITEM_ENTITY_SIZE
from pythongame.core.item_effects import register_item_effect, StatModifyingItemEffect
from pythongame.core.item_inventory import ItemEquipmentCategory
from pythongame.core.view.image_loading import SpriteInitializer


def register_royal_sword_item():
    item_type = ItemType.ROYAL_SWORD
    damage_bonus = 0.15
    armor_bonus = 1
    ui_icon_sprite = UiIconSprite.ITEM_ROYAL_SWORD
    sprite = Sprite.ITEM_ROYAL_SWORD
    effect = StatModifyingItemEffect(item_type, {HeroStat.DAMAGE: damage_bonus, HeroStat.ARMOR: armor_bonus})
    register_item_effect(item_type, effect)
    image_file_path = "resources/graphics/item_royal_sword.png"
    register_ui_icon_sprite_path(ui_icon_sprite, image_file_path)
    register_entity_sprite_initializer(sprite, SpriteInitializer(image_file_path, ITEM_ENTITY_SIZE))
    description = effect.get_description()
    item_data = ItemData(ui_icon_sprite, sprite, "Royal Sword", description, ItemEquipmentCategory.MAIN_HAND)
    register_item_data(item_type, item_data)
