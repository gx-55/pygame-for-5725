import math
from typing import Dict, Tuple, Union

from pygame.rect import Rect

from pythongame.core.common import *
from pythongame.core.consumable_inventory import ConsumableInventory
from pythongame.core.game_data import NpcCategory, PlayerLevelBonus
from pythongame.core.item_inventory import ItemInventory
from pythongame.core.loot import LootTable
from pythongame.core.math import boxes_intersect, rects_intersect, get_position_from_center_position, \
    translate_in_direction, is_x_and_y_within_distance
from pythongame.core.talents import TalentsConfig, TalentsState

GRID_CELL_WIDTH = 25


class WorldEntity:
    def __init__(self, pos: Tuple[int, int], size: Tuple[int, int], sprite: Sprite, direction=Direction.LEFT, speed=0):
        self.x: int = pos[0]
        self.y: int = pos[1]
        self.w: int = size[0]
        self.h: int = size[1]
        self.sprite: Sprite = sprite
        self.direction: Direction = direction
        self._speed = speed
        self._speed_multiplier = 1  # update and get using methods
        self._effective_speed = speed
        self._is_moving = True
        self.pygame_collision_rect: Rect = Rect(self.x, self.y, self.w, self.h)
        self.movement_animation_progress: float = 0  # goes from 0 to 1 repeatedly
        self.visible = True  # Should only be used to control rendering
        self.view_z = 0  # increasing Z values = moving into the screen

    def set_moving_in_dir(self, direction: Direction):
        if direction is None:
            raise Exception("Need to provide a valid direciton to move in")
        self.direction = direction
        self._is_moving = True

    def set_not_moving(self):
        self._is_moving = False

    def get_new_position_according_to_dir_and_speed(self, time_passed: Millis) -> Optional[Tuple[int, int]]:
        distance = self._effective_speed * time_passed
        if self._is_moving:
            return translate_in_direction((self.x, self.y), self.direction, distance)
        return None

    def update_movement_animation(self, time_passed: Millis):
        if self._is_moving:
            self.update_animation(time_passed)

    def update_animation(self, time_passed):
        self.movement_animation_progress = (self.movement_animation_progress + float(time_passed) / 1000) % 1

    def get_new_position_according_to_other_dir_and_speed(self, direction: Direction, time_passed: Millis) \
            -> Optional[Tuple[int, int]]:
        distance = self._effective_speed * time_passed
        return translate_in_direction((self.x, self.y), direction, distance)

    def get_center_position(self) -> Tuple[int, int]:
        return self.pygame_collision_rect.center

    def get_position(self) -> Tuple[int, int]:
        return int(self.x), int(self.y)

    def add_to_speed_multiplier(self, amount):
        self._speed_multiplier += amount
        self._effective_speed = self._speed_multiplier * self._speed

    def get_speed_multiplier(self):
        return self._speed_multiplier

    # TODO use more
    def rect(self) -> Rect:
        return self.pygame_collision_rect

    def translate_x(self, amount):
        self.set_position((self.x + amount, self.y))

    def translate_y(self, amount):
        self.set_position((self.x, self.y + amount))

    def set_position(self, new_position: Tuple[int, int]):
        self.x = new_position[0]
        self.y = new_position[1]
        self.pygame_collision_rect = Rect(self.x, self.y, self.w, self.h)

    def rotate_right(self):
        dirs = {
            Direction.DOWN: Direction.LEFT,
            Direction.LEFT: Direction.UP,
            Direction.UP: Direction.RIGHT,
            Direction.RIGHT: Direction.DOWN
        }
        self.direction = dirs[self.direction]

    def rotate_left(self):
        dirs = {
            Direction.DOWN: Direction.RIGHT,
            Direction.RIGHT: Direction.UP,
            Direction.UP: Direction.LEFT,
            Direction.LEFT: Direction.DOWN
        }
        self.direction = dirs[self.direction]


class LootableOnGround:
    def __init__(self, world_entity: WorldEntity):
        self.world_entity: WorldEntity = world_entity


class ConsumableOnGround(LootableOnGround):
    def __init__(self, world_entity: WorldEntity, consumable_type: ConsumableType):
        super().__init__(world_entity)
        self.consumable_type = consumable_type


class ItemOnGround(LootableOnGround):
    def __init__(self, world_entity: WorldEntity, item_type: ItemType):
        super().__init__(world_entity)
        self.item_type = item_type


class MoneyPileOnGround:
    def __init__(self, world_entity: WorldEntity, amount: int):
        self.world_entity = world_entity
        self.amount = amount
        self.has_been_picked_up_and_should_be_removed = False


# TODO There is a cyclic dependency here between game_state and projectile_controllers
class Projectile:
    def __init__(self, world_entity: WorldEntity, projectile_controller):
        self.world_entity = world_entity
        self.has_expired = False
        self.projectile_controller = projectile_controller
        self.has_collided_and_should_be_removed = False


class HealthOrManaResource:
    def __init__(self, max_value: int, regen: float):
        self._value_float = max_value
        self.value = max_value
        self.max_value = max_value
        self.base_regen = regen
        self.regen_bonus = 0
        self.value_was_updated = Observable()

    def gain(self, amount: float) -> int:
        value_before = self.value
        self._value_float = min(self._value_float + amount, self.max_value)
        self.value = int(math.floor(self._value_float))
        amount_gained = self.value - value_before
        self._notify_observers()
        return amount_gained

    def lose(self, amount: float) -> int:
        value_before = self.value
        self._value_float = min(self._value_float - amount, self.max_value)
        self.value = int(math.floor(self._value_float))
        amount_lost = value_before - self.value
        self._notify_observers()
        return amount_lost

    def set_zero(self):
        self._value_float = 0
        self.value = 0
        self._notify_observers()

    def gain_to_max(self) -> int:
        value_before = self.value
        self._value_float = self.max_value
        self.value = self.max_value
        amount_gained = self.value - value_before
        self._notify_observers()
        return amount_gained

    def set_to_partial_of_max(self, partial: float):
        self._value_float = partial * self.max_value
        self.value = int(math.floor(self._value_float))
        self._notify_observers()

    def regenerate(self, time_passed: Millis):
        self.gain(self.get_effective_regen() / 1000.0 * float(time_passed))

    def is_at_max(self):
        return self.value == self.max_value

    def is_at_or_below_zero(self):
        return self.value <= 0

    def increase_max(self, amount: int):
        self.max_value += amount

    def decrease_max(self, amount: int):
        self.max_value -= amount
        if self.value > self.max_value:
            self._value_float = self.max_value
            self.value = int(math.floor(self._value_float))
            self._notify_observers()

    def get_partial(self) -> float:
        return self.value / self.max_value

    def get_effective_regen(self) -> float:
        return self.base_regen + self.regen_bonus

    def _notify_observers(self):
        self.value_was_updated.notify((self.value, self.max_value))


class StunStatus:
    def __init__(self):
        self._number_of_active_stuns = 0

    def add_one(self):
        self._number_of_active_stuns += 1

    def remove_one(self):
        self._number_of_active_stuns -= 1
        if self._number_of_active_stuns < 0:
            raise Exception("Number of active stuns went below 0 down to " + str(self._number_of_active_stuns))

    def is_stunned(self):
        return self._number_of_active_stuns > 0


class NonPlayerCharacter:
    def __init__(self, npc_type: NpcType, world_entity: WorldEntity, health_resource: HealthOrManaResource,
                 npc_mind, npc_category: NpcCategory,
                 enemy_loot_table: Optional[LootTable], death_sound_id: Optional[SoundId],
                 max_distance_allowed_from_start_position: Optional[int]):
        self.npc_type = npc_type
        self.world_entity = world_entity
        self.health_resource = health_resource
        self.npc_mind = npc_mind
        self.active_buffs: List[BuffWithDuration] = []
        self.invulnerable: bool = False
        self.stun_status = StunStatus()
        self.npc_category = npc_category
        self.is_enemy = npc_category == NpcCategory.ENEMY
        self.is_neutral = npc_category == NpcCategory.NEUTRAL
        self.enemy_loot_table = enemy_loot_table
        self.death_sound_id = death_sound_id
        self.start_position = world_entity.get_position()  # Should never be updated
        self.max_distance_allowed_from_start_position = max_distance_allowed_from_start_position

    # TODO There is a cyclic dependancy here between game_state and buff_effects
    def gain_buff_effect(self, buff: Any, duration: Millis):
        existing_buffs_with_this_type = [b for b in self.active_buffs
                                         if b.buff_effect.get_buff_type() == buff.get_buff_type()]
        if existing_buffs_with_this_type:
            existing_buffs_with_this_type[0].set_remaining_duration(duration)
        else:
            self.active_buffs.append(BuffWithDuration(buff, duration))


class Wall:
    def __init__(self, wall_type: WallType, world_entity: WorldEntity):
        self.wall_type = wall_type
        self.world_entity = world_entity


# TODO There is a cyclic dependancy here between game_state and buff_effects
class BuffWithDuration:
    def __init__(self, buff_effect: Any, duration: Optional[Millis]):
        self.buff_effect = buff_effect
        self._time_until_expiration: Optional[Millis] = duration
        self.has_been_force_cancelled: bool = False
        self._total_duration: Optional[Millis] = duration
        self.has_applied_start_effect: bool = False

    def force_cancel(self):
        self.has_been_force_cancelled = True
        self._time_until_expiration = 0

    def notify_time_passed(self, time: Millis):
        self._time_until_expiration -= time

    def has_expired(self) -> bool:
        return self._time_until_expiration <= 0

    def get_ratio_duration_remaining(self) -> float:
        return self._time_until_expiration / self._total_duration

    def change_remaining_duration(self, delta: Millis):
        self._time_until_expiration = min(self._time_until_expiration + delta, self._total_duration)

    def set_remaining_duration(self, time: Millis):
        self._time_until_expiration = time

    def should_duration_be_visualized_on_enemies(self) -> bool:
        return self._total_duration > 1000


# These are sent as messages to player. They let buffs and items react to events. One buff might have its
# duration prolonged if an enemy dies for example, and an item might give mana on enemy kills.
class Event:
    pass


class EnemyDiedEvent(Event):
    pass


class PlayerUsedAbilityEvent(Event):
    def __init__(self, ability: AbilityType):
        self.ability = ability


class PlayerLostHealthEvent(Event):
    def __init__(self, amount: int, npc_attacker: Optional[NonPlayerCharacter]):
        self.amount = amount
        self.npc_attacker = npc_attacker


class PlayerBlockedEvent(Event):
    def __init__(self, npc_attacker: NonPlayerCharacter):
        self.npc_attacker = npc_attacker


class PlayerWasAttackedEvent(Event):
    def __init__(self, npc_attacker: NonPlayerCharacter):
        self.npc_attacker = npc_attacker


class PlayerDamagedEnemy(Event):
    def __init__(self, enemy_npc: NonPlayerCharacter, damage_source: Optional[str]):
        self.enemy_npc = enemy_npc
        self.damage_source = damage_source


class BuffEventOutcome:
    def __init__(self, change_remaining_duration: Optional[Millis], cancel_effect: bool):
        self.change_remaining_duration = change_remaining_duration
        self.cancel_effect = cancel_effect

    @staticmethod
    def change_remaining_duration(delta: Millis):
        return BuffEventOutcome(delta, False)

    @staticmethod
    def cancel_effect():
        return BuffEventOutcome(None, True)


class GainExpEvent:
    pass


class PlayerLeveledUp(GainExpEvent):
    pass


class PlayerLearnedNewAbility(GainExpEvent):
    def __init__(self, ability_type: AbilityType):
        self.ability_type = ability_type


class PlayerUnlockedNewTalent(GainExpEvent):
    pass


class AgentBuffsUpdate:
    def __init__(self, buffs_that_started: List[BuffWithDuration], buffs_that_were_active: List[BuffWithDuration],
                 buffs_that_ended: List[BuffWithDuration]):
        self.buffs_that_started = buffs_that_started
        self.buffs_that_were_active = buffs_that_were_active
        self.buffs_that_ended = buffs_that_ended


class PlayerState:
    def __init__(self, health_resource: HealthOrManaResource, mana_resource: HealthOrManaResource,
                 consumable_inventory: ConsumableInventory, abilities: List[AbilityType],
                 item_inventory: ItemInventory, new_level_abilities: Dict[int, AbilityType], hero_id: HeroId,
                 armor: int, base_dodge_chance: float, level_bonus: PlayerLevelBonus, talents_config: TalentsConfig,
                 block_chance: float):
        self.health_resource: HealthOrManaResource = health_resource
        self.mana_resource: HealthOrManaResource = mana_resource
        self.consumable_inventory = consumable_inventory
        self.abilities: List[AbilityType] = abilities
        self.ability_cooldowns_remaining: Dict[AbilityType, int] = {ability_type: 0 for ability_type in abilities}
        self.active_buffs: List[BuffWithDuration] = []
        self.is_invisible = False
        self.stun_status = StunStatus()
        self.item_inventory = item_inventory
        self.life_steal_ratio: float = 0
        self.exp = 0
        self.level = 1
        self.max_exp_in_this_level = 50
        self.new_level_abilities: Dict[int, AbilityType] = new_level_abilities
        self.money = 0
        self.base_physical_damage_modifier: float = 1  # only affected by level. [Changes multiplicatively]
        self.physical_damage_modifier_bonus: float = 0  # affected by items. [Change it additively]
        self.base_magic_damage_modifier: float = 1  # only affected by level. [Changes multiplicatively]
        self.magic_damage_modifier_bonus: float = 0  # affected by items. [Change it additively]
        self.hero_id: HeroId = hero_id
        self.base_armor: float = armor  # depends on which hero is being played
        # TODO add method for getting effective value
        self.armor_bonus: int = 0  # affected by items/buffs. [Change it additively]
        self.base_dodge_chance: float = base_dodge_chance  # depends on which hero is being used
        self.dodge_chance_bonus: float = 0  # affected by items/buffs. [Change it additively]
        self.level_bonus = level_bonus
        self._talents_state: TalentsState = TalentsState(talents_config)
        self._upgrades: List[HeroUpgrade] = []
        self.block_chance: float = block_chance
        self.block_damage_reduction: int = 0
        self.talents_were_updated = Observable()
        self.stats_were_updated = Observable()
        self.exp_was_updated = Observable()
        self.money_was_updated = Observable()
        self.cooldowns_were_updated = Observable()
        self.buffs_were_updated = Observable()

    def modify_money(self, delta: int):
        self.money += delta
        self.notify_money_observers()

    def notify_money_observers(self):
        self.money_was_updated.notify(self.money)

    def get_effective_physical_damage_modifier(self) -> float:
        return self.base_physical_damage_modifier + self.physical_damage_modifier_bonus

    def get_effective_magic_damage_modifier(self) -> float:
        return self.base_magic_damage_modifier + self.magic_damage_modifier_bonus

    def get_effective_dodge_change(self) -> float:
        return self.base_dodge_chance + self.dodge_chance_bonus

    def modify_stat(self, hero_stat: HeroStat, stat_delta: Union[int, float]):
        if hero_stat == HeroStat.MAX_HEALTH:
            if stat_delta >= 0:
                self.health_resource.increase_max(stat_delta)
            elif stat_delta < 0:
                self.health_resource.decrease_max(-stat_delta)
        elif hero_stat == HeroStat.HEALTH_REGEN:
            self.health_resource.regen_bonus += stat_delta
        elif hero_stat == HeroStat.MAX_MANA:
            if stat_delta >= 0:
                self.mana_resource.increase_max(stat_delta)
            elif stat_delta < 0:
                self.mana_resource.decrease_max(-stat_delta)
        elif hero_stat == HeroStat.MANA_REGEN:
            self.mana_resource.regen_bonus += stat_delta
        elif hero_stat == HeroStat.ARMOR:
            self.armor_bonus += stat_delta
        elif hero_stat == HeroStat.DAMAGE:
            self.physical_damage_modifier_bonus += stat_delta
            self.magic_damage_modifier_bonus += stat_delta
        elif hero_stat == HeroStat.PHYSICAL_DAMAGE:
            self.physical_damage_modifier_bonus += stat_delta
        elif hero_stat == HeroStat.MAGIC_DAMAGE:
            self.magic_damage_modifier_bonus += stat_delta
        elif hero_stat == HeroStat.LIFE_STEAL:
            self.life_steal_ratio += stat_delta
        elif hero_stat == HeroStat.BLOCK_AMOUNT:
            self.block_damage_reduction += stat_delta
        elif hero_stat == HeroStat.DODGE_CHANCE:
            self.dodge_chance_bonus += stat_delta
        else:
            raise Exception("Unhandled stat: " + str(hero_stat))
        self.notify_stats_observers()

    def notify_stats_observers(self):
        self.stats_were_updated.notify(self)

    # TODO There is a cyclic dependancy here between game_state and buff_effects
    def gain_buff_effect(self, buff: Any, duration: Millis):
        existing_buffs_with_this_type = [b for b in self.active_buffs
                                         if b.buff_effect.get_buff_type() == buff.get_buff_type()]
        if existing_buffs_with_this_type:
            existing_buffs_with_this_type[0].set_remaining_duration(duration)
        else:
            self.active_buffs.append(BuffWithDuration(buff, duration))
        self.notify_buff_observers()

    def notify_buff_observers(self):
        self.buffs_were_updated.notify(self.active_buffs)

    def has_active_buff(self, buff_type: BuffType):
        return len([b for b in self.active_buffs if b.buff_effect.get_buff_type() == buff_type]) > 0

    def force_cancel_all_buffs(self):
        for b in self.active_buffs:
            b.force_cancel()
        self.notify_buff_observers()

    def handle_buffs(self, time_passed: Millis):
        # NOTE: duplication between NPC's and player's buff handling
        copied_buffs_list = list(self.active_buffs)
        buffs_that_started = []
        buffs_that_ended = []
        buffs_that_were_active = []
        for buff in copied_buffs_list:
            buff.notify_time_passed(time_passed)
            if not buff.has_been_force_cancelled:
                buffs_that_were_active.append(buff)
            if not buff.has_applied_start_effect:
                buffs_that_started.append(buff)
                buff.has_applied_start_effect = True
            elif buff.has_expired():
                self.active_buffs.remove(buff)
                buffs_that_ended.append(buff)
        self.notify_buff_observers()
        return AgentBuffsUpdate(buffs_that_started, buffs_that_were_active, buffs_that_ended)

    def recharge_ability_cooldowns(self, time_passed: Millis):
        did_update = False
        for ability_type in self.ability_cooldowns_remaining:
            if self.ability_cooldowns_remaining[ability_type] > 0:
                self.ability_cooldowns_remaining[ability_type] -= time_passed
                did_update = True
        if did_update:
            self.notify_cooldown_observers()

    def add_to_ability_cooldown(self, ability_type: AbilityType, amount: Millis):
        self.ability_cooldowns_remaining[ability_type] += amount
        self.notify_cooldown_observers()

    def notify_cooldown_observers(self):
        self.cooldowns_were_updated.notify(self.ability_cooldowns_remaining)

    def gain_exp(self, amount: int) -> List[GainExpEvent]:
        events = []
        self.exp += amount
        if self.exp >= self.max_exp_in_this_level:
            events.append(PlayerLeveledUp())
        while self.exp >= self.max_exp_in_this_level:
            self.exp -= self.max_exp_in_this_level
            self.level += 1
            self._update_stats_for_new_level()
            if self.level in self.new_level_abilities:
                new_ability = self.new_level_abilities[self.level]
                self.gain_ability(new_ability)
                events.append(PlayerLearnedNewAbility(new_ability))
            if self._talents_state.has_tier_for_level(self.level):
                self._talents_state.unlock_tier(self.level)
                events.append(PlayerUnlockedNewTalent())
                self.notify_talent_observers()
        self.notify_exp_observers()
        return events

    def lose_exp_from_death(self):
        partial_exp_loss = 0.5
        self.exp = max(0, self.exp - int(self.max_exp_in_this_level * partial_exp_loss))
        self.notify_exp_observers()

    def notify_exp_observers(self):
        self.exp_was_updated.notify((self.level, self.exp / self.max_exp_in_this_level))

    def gain_exp_worth_n_levels(self, num_levels: int) -> List[GainExpEvent]:
        events = []
        for i in range(num_levels):
            amount = self.max_exp_in_this_level - self.exp
            events += self.gain_exp(amount)
        return events

    def _update_stats_for_new_level(self):
        self.health_resource.increase_max(self.level_bonus.health)
        self.health_resource.gain_to_max()
        self.mana_resource.increase_max(self.level_bonus.mana)
        self.mana_resource.gain_to_max()
        self.max_exp_in_this_level = int(self.max_exp_in_this_level * 1.6)
        self.base_physical_damage_modifier *= 1.1
        self.base_magic_damage_modifier *= 1.1
        self.base_armor += self.level_bonus.armor
        self.notify_stats_observers()

    def gain_ability(self, ability_type: AbilityType):
        self.ability_cooldowns_remaining[ability_type] = 0
        self.abilities.append(ability_type)
        self.notify_cooldown_observers()

    def notify_about_event(self, event: Event, game_state):
        for buff in self.active_buffs:
            outcome: Optional[BuffEventOutcome] = buff.buff_effect.buff_handle_event(event)
            if outcome:
                if outcome.change_remaining_duration:
                    buff.change_remaining_duration(outcome.change_remaining_duration)
                if outcome.cancel_effect:
                    buff.force_cancel()
                self.notify_buff_observers()
        for item_effect in self.item_inventory.get_all_active_item_effects():
            item_effect.item_handle_event(event, game_state)

    def choose_talent(self, tier_index: int, option_index: int) -> Tuple[str, HeroUpgrade]:
        option = self._talents_state.pick(tier_index, option_index)
        self._upgrades.append(option.upgrade)
        self.notify_talent_observers()
        return option.name, option.upgrade

    def notify_talent_observers(self):
        self.talents_were_updated.notify(self._talents_state)

    def has_unpicked_talents(self):
        return self._talents_state.has_unpicked_talents()

    def get_serilized_talent_tier_choices(self):
        return [tier.picked_index for tier in self._talents_state.tiers]

    def gain_upgrade(self, upgrade: HeroUpgrade):
        self._upgrades.append(upgrade)

    def has_upgrade(self, upgrade: HeroUpgrade) -> bool:
        return upgrade in self._upgrades


# TODO Is there a way to handle this better in the view module? This class shouldn't need to masquerade as a WorldEntity
class DecorationEntity:
    def __init__(self, pos: Tuple[int, int], sprite: Sprite):
        self.x = pos[0]
        self.y = pos[1]
        self.sprite = sprite
        # The fields below are needed for the view module to be able to handle this class the same as WorldEntity
        self.direction = Direction.DOWN  # The view module uses direction to determine which image to render
        self.movement_animation_progress: float = 0  # The view module uses this to determine which frame to render
        self.visible = True  # Should only be used to control rendering

    def rect(self):
        # Used by view module in map_editor
        return self.x, self.y, 0, 0

    def get_position(self):
        return self.x, self.y


class Portal:
    def __init__(self, world_entity: WorldEntity, portal_id: PortalId, is_enabled: bool, leads_to: Optional[PortalId]):
        self.world_entity = world_entity
        self.portal_id = portal_id
        self.is_enabled = is_enabled
        self.leads_to = leads_to

    def activate(self, sprite: Sprite):
        self.is_enabled = True
        self.world_entity.sprite = sprite


class Chest:
    def __init__(self, world_entity: WorldEntity, loot_table: LootTable):
        self.world_entity = world_entity
        self.loot_table = loot_table
        self.has_been_opened = False


class WarpPoint:
    def __init__(self, world_entity: WorldEntity):
        self.world_entity = world_entity

    def make_visible(self):
        self.world_entity.visible = True


class CameraShake:

    def __init__(self, shake_frequency: Millis, duration: Millis, max_offset: int):
        self._timer = PeriodicTimer(shake_frequency)
        self._time_left = duration
        self._max_offset = max_offset
        self.offset = (0, 0)

    def notify_time_passed(self, time_passed: Millis):
        self._time_left -= time_passed
        if self._timer.update_and_check_if_ready(time_passed):
            self.offset = (random.randint(-self._max_offset, self._max_offset),
                           random.randint(-self._max_offset, self._max_offset))

    def has_time_left(self) -> bool:
        return self._time_left > 0


class GameState:
    def __init__(self, player_entity: WorldEntity, consumables_on_ground: List[ConsumableOnGround],
                 items_on_ground: List[ItemOnGround], money_piles_on_ground: List[MoneyPileOnGround],
                 non_player_characters: List[NonPlayerCharacter], walls: List[Wall], camera_size: Tuple[int, int],
                 entire_world_area: Rect, player_state: PlayerState,
                 decoration_entities: List[DecorationEntity], portals: List[Portal], chests: List[Chest]):
        self.camera_size = camera_size
        self.camera_world_area = Rect((0, 0), self.camera_size)
        self.camera_shake: CameraShake = None
        self.player_entity = player_entity
        self.projectile_entities: List[Projectile] = []
        # TODO: unify code for picking up stuff from the ground. The way they are rendered and picked up are similar,
        # and only the effect of picking them up is different.
        self.consumables_on_ground: List[ConsumableOnGround] = consumables_on_ground
        self.items_on_ground: List[ItemOnGround] = items_on_ground
        self.money_piles_on_ground: List[MoneyPileOnGround] = money_piles_on_ground
        self.non_player_characters: List[NonPlayerCharacter] = non_player_characters
        self.entire_world_area = entire_world_area
        self.walls_state = WallsState(walls, entire_world_area)
        self.visual_effects = []
        self.player_state: PlayerState = player_state
        self.pathfinder_wall_grid = self._setup_pathfinder_wall_grid(
            self.entire_world_area, [w.world_entity for w in walls])
        self.decorations_state = DecorationsState(decoration_entities, entire_world_area)
        self.portals: List[Portal] = portals
        self.player_spawn_position: Tuple[int, int] = player_entity.get_position()
        self.warp_points: List[WarpPoint] = []
        self.chests: List[Chest] = chests
        self.player_movement_speed_was_updated = Observable()

    @staticmethod
    def _setup_pathfinder_wall_grid(entire_world_area: Rect, walls: List[WorldEntity]):
        # TODO extract world area arithmetic
        grid_width = entire_world_area.w // GRID_CELL_WIDTH
        grid_height = entire_world_area.h // GRID_CELL_WIDTH
        grid = []
        for x in range(grid_width + 1):
            grid.append((grid_height + 1) * [0])
        for w in walls:
            cell_x = (w.x - entire_world_area.x) // GRID_CELL_WIDTH
            cell_y = (w.y - entire_world_area.y) // GRID_CELL_WIDTH
            grid[cell_x][cell_y] = 1
        return grid

    def handle_camera_shake(self, time_passed: Millis):
        if self.camera_shake is not None:
            self.camera_shake.notify_time_passed(time_passed)
            if not self.camera_shake.has_time_left():
                self.camera_shake = None

    def get_camera_world_area_including_camera_shake(self) -> Rect:
        camera_world_area = Rect(self.camera_world_area)
        if self.camera_shake is not None:
            camera_world_area[0] += self.camera_shake.offset[0]
            camera_world_area[1] += self.camera_shake.offset[1]
        return camera_world_area

    def modify_hero_stat(self, hero_stat: HeroStat, stat_delta: Union[int, float]):
        if hero_stat == HeroStat.MOVEMENT_SPEED:
            self.player_entity.add_to_speed_multiplier(stat_delta)
            self.notify_movement_speed_observers()
        else:
            self.player_state.modify_stat(hero_stat, stat_delta)

    def notify_movement_speed_observers(self):
        self.player_movement_speed_was_updated.notify(self.player_entity.get_speed_multiplier())

    def add_non_player_character(self, npc: NonPlayerCharacter):
        self.non_player_characters.append(npc)

    def remove_all_player_summons(self):
        self.non_player_characters = [npc for npc in self.non_player_characters
                                      if npc.npc_category != NpcCategory.PLAYER_SUMMON]

    def get_all_entities_to_render(self) -> List[WorldEntity]:
        walls_that_are_visible = self.walls_state.get_walls_in_camera(self.camera_world_area)
        other_entities = [self.player_entity] + \
                         [p.world_entity for p in self.consumables_on_ground] + \
                         [i.world_entity for i in self.items_on_ground] + \
                         [m.world_entity for m in self.money_piles_on_ground] + \
                         [e.world_entity for e in self.non_player_characters] + \
                         [p.world_entity for p in self.projectile_entities] + \
                         [p.world_entity for p in self.portals] + \
                         [w.world_entity for w in self.warp_points] + \
                         [c.world_entity for c in self.chests]
        return walls_that_are_visible + other_entities

    def get_decorations_to_render(self) -> List[DecorationEntity]:
        return self.decorations_state.get_decorations_in_camera(self.camera_world_area)

    def center_camera_on_player(self):
        new_camera_pos = get_position_from_center_position(self.player_entity.get_center_position(), self.camera_size)
        new_camera_pos_within_world = self.get_within_world(new_camera_pos, (self.camera_size[0], self.camera_size[1]))
        self.camera_world_area.topleft = new_camera_pos_within_world

    def translate_camera_position(self, translation_vector: Tuple[int, int]):
        new_camera_pos = (self.camera_world_area.x + translation_vector[0],
                          self.camera_world_area.y + translation_vector[1])
        new_camera_pos_within_world = self.get_within_world(new_camera_pos, (self.camera_size[0], self.camera_size[1]))
        self.camera_world_area.topleft = new_camera_pos_within_world

    def get_projectiles_intersecting_with(self, entity: WorldEntity) -> List[Projectile]:
        return [p for p in self.projectile_entities if boxes_intersect(entity.rect(), p.world_entity.rect())]

    def get_enemy_intersecting_with(self, entity: WorldEntity) -> List[NonPlayerCharacter]:
        return [e for e in self.non_player_characters if
                e.is_enemy and boxes_intersect(e.world_entity.rect(), entity.rect())]

    def get_enemy_intersecting_rect(self, rect: Rect) -> List[NonPlayerCharacter]:
        return [e for e in self.non_player_characters if e.is_enemy and rects_intersect(e.world_entity.rect(), rect)]

    def get_enemies_within_x_y_distance_of(self, distance: int, position: Tuple[int, int]):
        return [e for e in self.non_player_characters
                if e.is_enemy
                and is_x_and_y_within_distance(e.world_entity.get_center_position(), position, distance)]

    # NOTE: Very naive brute-force collision checking
    def update_world_entity_position_within_game_world(self, entity: WorldEntity, time_passed: Millis):
        new_position = entity.get_new_position_according_to_dir_and_speed(time_passed)
        if new_position:
            new_pos_within_world = self.get_within_world(new_position, (entity.w, entity.h))
            if not self.would_entity_collide_if_new_pos(entity, new_pos_within_world):
                entity.set_position(new_pos_within_world)

    # NOTE: Very naive brute-force collision checking
    def update_npc_position_within_game_world(self, npc: NonPlayerCharacter, time_passed: Millis):
        entity = npc.world_entity
        new_position = entity.get_new_position_according_to_dir_and_speed(time_passed)
        if new_position:
            if npc.max_distance_allowed_from_start_position:
                is_close_to_start_position = is_x_and_y_within_distance(
                    npc.start_position, new_position, npc.max_distance_allowed_from_start_position)
                if not is_close_to_start_position:
                    return
            new_pos_within_world = self.get_within_world(new_position, (entity.w, entity.h))
            if not self.would_entity_collide_if_new_pos(entity, new_pos_within_world):
                entity.set_position(new_pos_within_world)

    # TODO Improve the interaction between functions in here
    def would_entity_collide_if_new_pos(self, entity, new_pos_within_world):
        if not self.is_position_within_game_world(new_pos_within_world):
            raise Exception("not within game-world: " + str(new_pos_within_world))
        old_pos = entity.x, entity.y
        entity.set_position(new_pos_within_world)
        walls = self.walls_state.get_walls_close_to_position(entity.get_position())
        other_entities = [e.world_entity for e in self.non_player_characters] + \
                         [self.player_entity] + walls + [p.world_entity for p in self.portals] + \
                         [w.world_entity for w in self.warp_points] + [c.world_entity for c in self.chests]
        collision = any([other for other in other_entities if self._entities_collide(entity, other)
                         and entity is not other])
        entity.set_position(old_pos)
        return collision

    def get_within_world(self, pos: Tuple[int, int], size: Tuple[int, int]):
        # TODO extract world area arithmetic
        x = max(self.entire_world_area.x,
                min(self.entire_world_area.x + self.entire_world_area.w - size[0], pos[0]))
        y = max(self.entire_world_area.y, min(self.entire_world_area.y + self.entire_world_area.h - size[1], pos[1]))
        return x, y

    def is_position_within_game_world(self, position: Tuple[int, int]) -> bool:
        return self.entire_world_area.collidepoint(position[0], position[1])

    def remove_expired_projectiles(self):
        self.projectile_entities = [p for p in self.projectile_entities if not p.has_expired]

    def remove_dead_npcs(self) -> List[NonPlayerCharacter]:
        npcs_that_died = [npc for npc in self.non_player_characters if npc.health_resource.is_at_or_below_zero()]
        self.non_player_characters = [npc for npc in self.non_player_characters if
                                      not npc.health_resource.is_at_or_below_zero()]
        return npcs_that_died

    def remove_expired_visual_effects(self):
        self.visual_effects = [v for v in self.visual_effects if not v.has_expired]

    def remove_opened_chests(self):
        self.chests: List[Chest] = [c for c in self.chests if not c.has_been_opened]

    def remove_projectiles_that_have_been_destroyed(self):
        self.projectile_entities: List[Projectile] = [p for p in self.projectile_entities
                                                      if not p.has_collided_and_should_be_removed]

    def remove_money_piles_that_have_been_picked_up(self):
        self.money_piles_on_ground: List[MoneyPileOnGround] = [m for m in self.money_piles_on_ground
                                                               if not m.has_been_picked_up_and_should_be_removed]

    @staticmethod
    def _entities_collide(a: WorldEntity, b: WorldEntity):
        # Optimization: collision checking done with C-code from Pygame
        return a.pygame_collision_rect.colliderect(b.pygame_collision_rect)


class WallsState:
    def __init__(self, walls: List[Wall], entire_world_area: Rect):
        self.walls: List[Wall] = walls
        self._buckets = Buckets([w.world_entity for w in walls], entire_world_area)

    def add_wall(self, wall: Wall):
        self.walls.append(wall)
        self._buckets.add_entity(wall.world_entity)

    def remove_wall(self, wall: Wall):
        self.walls.remove(wall)
        self._buckets.remove_entity(wall.world_entity)

    # TODO Use _entities_collide?
    def does_entity_intersect_with_wall(self, entity: WorldEntity):
        nearby_walls = self.get_walls_close_to_position(entity.get_position())
        return any([w for w in nearby_walls if boxes_intersect(w.rect(), entity.rect())])

    # TODO Use _entities_collide?
    def does_rect_intersect_with_wall(self, rect: Rect):
        nearby_walls = self.get_walls_close_to_position((rect[0], rect[1]))
        return any([w for w in nearby_walls if rects_intersect(w.rect(), rect)])

    def get_walls_close_to_position(self, position: Tuple[int, int]) -> List[WorldEntity]:
        return self._buckets.get_entities_close_to_position(position)

    def get_walls_in_camera(self, camera_world_area: Rect) -> List[WorldEntity]:
        return self._buckets.get_entitites_close_to_world_area(camera_world_area)

    def get_walls_at_position(self, position: Tuple[int, int]) -> List[Wall]:
        return [w for w in self.walls if w.world_entity.get_position() == position]


class DecorationsState:
    def __init__(self, decoration_entities: List[DecorationEntity], entire_world_area: Rect):
        self.decoration_entities: List[DecorationEntity] = decoration_entities
        self._buckets = Buckets(decoration_entities, entire_world_area)

    def add_decoration(self, decoration: DecorationEntity):
        self.decoration_entities.append(decoration)
        self._buckets.add_entity(decoration)

    def remove_decoration(self, decoration: DecorationEntity):
        self.decoration_entities.remove(decoration)
        self._buckets.remove_entity(decoration)

    def get_decorations_in_camera(self, camera_world_area: Rect) -> List[DecorationEntity]:
        return self._buckets.get_entitites_close_to_world_area(camera_world_area)

    def get_decorations_at_position(self, position: Tuple[int, int]) -> List[DecorationEntity]:
        return [d for d in self.decoration_entities if d.get_position() == position]


# This class provides a way to store entities based on their location in the world,
# which improves performance mainly for collision checking and rendering
# NOTE: it should only be used for immovable objects (such as walls and floor tiles)
class Buckets:
    _BUCKET_WIDTH = 100
    _BUCKET_HEIGHT = 100

    def __init__(self, entities: List[Any], entire_world_area: Rect):
        self._buckets: Dict[int, Dict[int, List[Any]]] = {}
        self.entire_world_area = entire_world_area
        for x_bucket in range(self.entire_world_area.w // Buckets._BUCKET_WIDTH + 1):
            self._buckets[x_bucket] = {}
            for y_bucket in range(self.entire_world_area.h // Buckets._BUCKET_HEIGHT + 1):
                self._buckets[x_bucket][y_bucket] = []
        for entity in entities:
            self.add_entity(entity)

    def add_entity(self, entity: Any):
        bucket = self._bucket_for_world_position(entity.get_position())
        bucket.append(entity)

    def remove_entity(self, entity: Any):
        bucket = self._bucket_for_world_position(entity.get_position())
        bucket.remove(entity)

    def get_entitites_close_to_world_area(self, world_area: Rect) -> List[Any]:
        x0_bucket, y0_bucket = self._bucket_index_for_world_position(world_area.topleft)
        x1_bucket, y1_bucket = self._bucket_index_for_world_position(world_area.bottomright)
        buckets = self._buckets_between_indices(x0_bucket - 1, x1_bucket + 1, y0_bucket - 1, y1_bucket + 1)
        return [entity for bucket in buckets for entity in bucket]

    def get_entities_close_to_position(self, position: Tuple[int, int]) -> List[Any]:
        x_bucket, y_bucket = self._bucket_index_for_world_position(position)
        buckets = self._buckets_between_indices(x_bucket - 1, x_bucket + 1, y_bucket - 1, y_bucket + 1)
        return [entity for bucket in buckets for entity in bucket]

    def _buckets_between_indices(self, x0: int, x1: int, y0: int, y1: int) -> List[List[Any]]:
        for x_bucket in range(max(0, x0), min(x1 + 1, len(self._buckets) - 1)):
            for y_bucket in range(max(0, y0), min(y1 + 1, len(self._buckets[x_bucket]) - 1)):
                yield self._buckets[x_bucket][y_bucket]

    def _bucket_for_world_position(self, world_position: Tuple[int, int]):
        x_bucket, y_bucket = self._bucket_index_for_world_position(world_position)
        return self._buckets[x_bucket][y_bucket]

    def _bucket_index_for_world_position(self, world_position: Tuple[int, int]) -> Tuple[int, int]:
        x_bucket = int(world_position[0] - self.entire_world_area.x) // Buckets._BUCKET_WIDTH
        y_bucket = int(world_position[1] - self.entire_world_area.y) // Buckets._BUCKET_HEIGHT
        return x_bucket, y_bucket
