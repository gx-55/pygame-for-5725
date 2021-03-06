from pythongame.core.common import HeroId, PortraitIconSprite, PLAYER_ENTITY_SIZE, HeroUpgrade, UiIconSprite
from pythongame.core.game_data import Sprite, Direction, AbilityType, register_entity_sprite_map, \
    register_portrait_icon_sprite_path, register_hero_data, HeroData, \
    InitialPlayerStateData
from pythongame.core.game_state import PlayerLevelBonus
from pythongame.core.talents import TalentsConfig, TalentTierConfig, TalentTierOptionConfig
from pythongame.core.view.image_loading import SpriteSheet
from pythongame.game_data.heroes.generic_talents import TALENT_CHOICE_ARMOR_DAMAGE, TALENT_CHOICE_HEALTH_MANA, \
    TALENT_CHOICE_HEALTH_MANA_REGEN

HERO_ID = HeroId.WARRIOR


def register_hero_warrior():
    sprite = Sprite.HERO_WARRIOR
    portrait_icon_sprite = PortraitIconSprite.HERO_WARRIOR
    player_sprite_sheet = SpriteSheet("resources/graphics/enemy_sprite_sheet_3.png")
    original_sprite_size = (32, 32)
    scaled_sprite_size = (48, 48)
    x = 6
    indices_by_dir = {
        Direction.DOWN: [(x + i, 4) for i in range(3)],
        Direction.LEFT: [(x + i, 5) for i in range(3)],
        Direction.RIGHT: [(x + i, 6) for i in range(3)],
        Direction.UP: [(x + i, 7) for i in range(3)]
    }
    sprite_position_relative_to_entity = (-8, -16)
    register_entity_sprite_map(sprite, player_sprite_sheet, original_sprite_size,
                               scaled_sprite_size, indices_by_dir, sprite_position_relative_to_entity)
    register_portrait_icon_sprite_path(portrait_icon_sprite, 'resources/graphics/portrait_warrior_hero.png')
    entity_speed = 0.105
    description = "A sturdy melee fighter, the warrior can stand his ground against any foe, and thrives when there " \
                  "are enemies all around."
    hero_data = HeroData(sprite, portrait_icon_sprite, _get_initial_player_state_warrior(), entity_speed,
                         PLAYER_ENTITY_SIZE, description)
    register_hero_data(HERO_ID, hero_data)


def _get_initial_player_state_warrior() -> InitialPlayerStateData:
    health = 60
    mana = 30
    mana_regen = 2
    health_per_level = 15
    mana_per_level = 5
    armor_per_level = 1.5
    level_bonus = PlayerLevelBonus(health_per_level, mana_per_level, armor_per_level)
    armor = 3
    dodge_chance = 0.05
    consumable_slots = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: []
    }
    abilities = [AbilityType.SWORD_SLASH]
    new_level_abilities = {
        2: AbilityType.CHARGE,
        5: AbilityType.BLOOD_LUST,
        7: AbilityType.STOMP
    }

    talents_state = TalentsConfig({
        3: TALENT_CHOICE_ARMOR_DAMAGE,
        4: TalentTierConfig(
            TalentTierOptionConfig("Close combat",
                                   "Your charge ability deals full damage even when used at close range",
                                   HeroUpgrade.ABILITY_CHARGE_MELEE, UiIconSprite.ABILITY_CHARGE),
            TalentTierOptionConfig("Brawl",
                                   "The damage of your slash ability is increased if at least 2 enemies are hit",
                                   HeroUpgrade.ABILITY_SLASH_AOE_BONUS_DAMAGE, UiIconSprite.ABILITY_SWORD_SLASH)),
        5: TALENT_CHOICE_HEALTH_MANA,
        6: TalentTierConfig(
            TalentTierOptionConfig("Bloodthirst",
                                   "The duration of your bloodlust ability is increased additionally on kills",
                                   HeroUpgrade.ABILITY_BLOODLUST_DURATION, UiIconSprite.ABILITY_BLOODLUST),
            TalentTierOptionConfig("Berserker", "Reduces the cooldown of your slash ability",
                                   HeroUpgrade.ABILITY_SLASH_CD, UiIconSprite.ABILITY_SWORD_SLASH)),
        7: TALENT_CHOICE_HEALTH_MANA_REGEN
    })
    block_chance = 0.2
    return InitialPlayerStateData(
        health, mana, mana_regen, consumable_slots, abilities, new_level_abilities, HERO_ID, armor, dodge_chance,
        level_bonus, talents_state, block_chance)
