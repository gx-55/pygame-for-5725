import random
from typing import List, Tuple

from pythongame.core.common import *
from pythongame.core.entity_creation import create_money_pile_on_ground, create_item_on_ground, \
    create_consumable_on_ground
from pythongame.core.game_data import CONSUMABLES, ITEMS, NON_PLAYER_CHARACTERS, allocate_input_keys_for_abilities, \
    NpcCategory
from pythongame.core.game_state import GameState, ItemOnGround, ConsumableOnGround, LootableOnGround, BuffWithDuration, \
    EnemyDiedEvent, NonPlayerCharacter
from pythongame.core.item_effects import get_item_effect
from pythongame.core.loot import LootEntry
from pythongame.core.math import boxes_intersect, rects_intersect, sum_of_vectors, \
    get_rect_with_increased_size_in_all_directions
from pythongame.core.player_controls import PlayerControls
from pythongame.core.sound_player import play_sound
from pythongame.core.view_state import ViewState
from pythongame.core.visual_effects import create_visual_exp_text, VisualCircle, VisualRect


class GameEngine:

    def __init__(self, game_state: GameState, view_state: ViewState):
        self.game_state = game_state
        self.player_spawn_position = game_state.player_entity.get_position()
        self.view_state = view_state

    def initialize(self):
        for item_effect in self.game_state.player_state.item_slots.values():
            if item_effect:
                item_effect.apply_start_effect(self.game_state)

    def try_use_ability(self, ability_type: AbilityType):
        PlayerControls.try_use_ability(ability_type, self.game_state, self.view_state)

    def try_use_consumable(self, slot_number: int):
        PlayerControls.try_use_consumable(slot_number, self.game_state, self.view_state)

    def move_in_direction(self, direction: Direction):
        if not self.game_state.player_state.is_stunned():
            self.game_state.player_entity.set_moving_in_dir(direction)

    def stop_moving(self):
        # Don't stop moving if stunned (could be charging)
        if not self.game_state.player_state.is_stunned():
            self.game_state.player_entity.set_not_moving()

    def switch_inventory_items(self, slot_1: int, slot_2: int):
        self.game_state.player_state.switch_item_slots(slot_1, slot_2)

    def drag_consumable_between_slots(self, from_slot: int, to_slot: int):
        self.game_state.player_state.consumable_inventory.drag_consumable_between_slots(from_slot, to_slot)

    def drop_inventory_item_on_ground(self, item_slot: int, game_world_position: Tuple[int, int]):
        item_type = self.game_state.player_state.item_slots[item_slot].get_item_type()
        item = create_item_on_ground(item_type, game_world_position)
        self.game_state.items_on_ground.append(item)
        get_item_effect(item_type).apply_end_effect(self.game_state)
        self.game_state.player_state.item_slots[item_slot] = None

    def drop_consumable_on_ground(self, consumable_slot: int, game_world_position: Tuple[int, int]):
        consumable_type = self.game_state.player_state.consumable_inventory.remove_consumable_from_slot(consumable_slot)
        consumable = create_consumable_on_ground(consumable_type, game_world_position)
        self.game_state.consumables_on_ground.append(consumable)

    def try_pick_up_loot_from_ground(self, loot: LootableOnGround):
        if isinstance(loot, ConsumableOnGround):
            self._try_pick_up_consumable_from_ground(loot)
        elif isinstance(loot, ItemOnGround):
            self._try_pick_up_item_from_ground(loot)
        else:
            raise Exception("Unhandled type of loot: " + str(loot))

    def _try_pick_up_item_from_ground(self, item: ItemOnGround):
        empty_item_slot = self.game_state.player_state.find_first_empty_item_slot()
        item_name = ITEMS[item.item_type].name
        if empty_item_slot:
            item_effect = get_item_effect(item.item_type)
            self.game_state.player_state.item_slots[empty_item_slot] = item_effect
            item_effect.apply_start_effect(self.game_state)
            self.view_state.set_message("You picked up " + item_name)
            play_sound(SoundId.EVENT_PICKED_UP)
            self.game_state.remove_entities([item])
        else:
            self.view_state.set_message("No space for " + item_name)

    def _try_pick_up_consumable_from_ground(self, consumable: ConsumableOnGround):
        has_space = self.game_state.player_state.consumable_inventory.has_space_for_more()
        consumable_type = consumable.consumable_type
        consumable_name = CONSUMABLES[consumable_type].name
        if has_space:
            self.game_state.player_state.consumable_inventory.add_consumable(consumable_type)
            self.view_state.set_message("You picked up " + consumable_name)
            play_sound(SoundId.EVENT_PICKED_UP)
            self.game_state.remove_entities([consumable])
        else:
            self.view_state.set_message("No space for " + consumable_name)

    def run_one_frame(self, time_passed: Millis):
        for npc in self.game_state.non_player_characters:
            # NonPlayerCharacter AI shouldn't run if enemy is too far out of sight
            if self._is_npc_close_to_camera(npc) and not npc.is_stunned():
                npc.npc_mind.control_npc(self.game_state, npc, self.game_state.player_entity,
                                         self.game_state.player_state.is_invisible, time_passed)

        self.view_state.notify_player_entity_center_position(self.game_state.player_entity.get_center_position())

        self.view_state.notify_time_passed(time_passed)

        for projectile in self.game_state.projectile_entities:
            projectile.projectile_controller.notify_time_passed(self.game_state, projectile, time_passed)

        for visual_effect in self.game_state.visual_effects:
            visual_effect.notify_time_passed(time_passed)

        npcs_that_died = self.game_state.remove_dead_npcs()
        enemies_that_died = [e for e in npcs_that_died if e.is_enemy]
        if enemies_that_died:
            exp_gained = sum([NON_PLAYER_CHARACTERS[e.npc_type].exp_reward for e in enemies_that_died])
            self.game_state.visual_effects.append(create_visual_exp_text(self.game_state.player_entity, exp_gained))
            did_player_level_up = self.game_state.player_state.gain_exp(exp_gained)
            if did_player_level_up:
                play_sound(SoundId.EVENT_PLAYER_LEVELED_UP)
                self.view_state.set_message("You reached level " + str(self.game_state.player_state.level))
                allocate_input_keys_for_abilities(self.game_state.player_state.abilities)
            for enemy_that_died in enemies_that_died:
                if enemy_that_died.death_sound_id:
                    play_sound(enemy_that_died.death_sound_id)
                else:
                    play_sound(SoundId.EVENT_ENEMY_DIED)
                loot = enemy_that_died.enemy_loot_table.generate_loot()
                enemy_death_position = enemy_that_died.world_entity.get_position()
                self._put_loot_on_ground(enemy_death_position, loot)
                self.game_state.player_state.notify_about_event(EnemyDiedEvent(), self.game_state)

        self.game_state.remove_expired_projectiles()
        self.game_state.remove_expired_visual_effects()

        player_buffs_update = handle_buffs(self.game_state.player_state.active_buffs, time_passed)
        for buff in player_buffs_update.buffs_that_started:
            buff.buff_effect.apply_start_effect(self.game_state, self.game_state.player_entity, None)
        for buff in player_buffs_update.buffs_that_were_active:
            buff_should_end = buff.buff_effect.apply_middle_effect(
                self.game_state, self.game_state.player_entity, None, time_passed)
            if buff_should_end:
                buff.force_cancel()

        for buff in player_buffs_update.buffs_that_ended:
            buff.buff_effect.apply_end_effect(self.game_state, self.game_state.player_entity, None)

        for enemy in self.game_state.non_player_characters:
            enemy.health_resource.regenerate(time_passed)
            buffs_update = handle_buffs(enemy.active_buffs, time_passed)
            for buff in buffs_update.buffs_that_started:
                buff.buff_effect.apply_start_effect(self.game_state, enemy.world_entity, enemy)
            for buff in buffs_update.buffs_that_were_active:
                buff.buff_effect.apply_middle_effect(self.game_state, enemy.world_entity, enemy, time_passed)
            for buff in buffs_update.buffs_that_ended:
                buff.buff_effect.apply_end_effect(self.game_state, enemy.world_entity, enemy)

        for item_effect in self.game_state.player_state.item_slots.values():
            if item_effect:
                item_effect.apply_middle_effect(self.game_state, time_passed)

        self.game_state.player_state.regenerate_health_and_mana(time_passed)
        self.game_state.player_state.recharge_ability_cooldowns(time_passed)

        self.game_state.player_entity.update_movement_animation(time_passed)
        for npc in self.game_state.non_player_characters:
            npc.world_entity.update_movement_animation(time_passed)
        for projectile in self.game_state.projectile_entities:
            projectile.world_entity.update_movement_animation(time_passed)

        for npc in self.game_state.non_player_characters:
            # Enemies shouldn't move towards player when they are out of sight
            if self._is_npc_close_to_camera(npc) and not npc.is_stunned():
                self.game_state.update_npc_position_within_game_world(npc, time_passed)
        # player can still move when stunned (could be charging)
        self.game_state.update_world_entity_position_within_game_world(self.game_state.player_entity, time_passed)
        for projectile in self.game_state.projectile_entities:
            new_pos = projectile.world_entity.get_new_position_according_to_dir_and_speed(time_passed)
            projectile.world_entity.set_position(new_pos)

        for visual_effect in self.game_state.visual_effects:
            visual_effect.update_position_if_attached_to_entity()
            if visual_effect.attached_to_entity \
                    and not visual_effect.attached_to_entity in [e.world_entity for e in
                                                                 self.game_state.non_player_characters] \
                    and visual_effect.attached_to_entity != self.game_state.player_entity:
                visual_effect.has_expired = True

        # ------------------------------------
        #          HANDLE COLLISIONS
        # ------------------------------------

        entities_to_remove = []
        for money_pile in self.game_state.money_piles_on_ground:
            if boxes_intersect(self.game_state.player_entity, money_pile.world_entity):
                play_sound(SoundId.EVENT_PICKED_UP_MONEY)
                entities_to_remove.append(money_pile)
                self.game_state.player_state.money += money_pile.amount

        for enemy in [e for e in self.game_state.non_player_characters if e.is_enemy]:
            for projectile in self.game_state.get_projectiles_intersecting_with(enemy.world_entity):
                should_remove_projectile = projectile.projectile_controller.apply_enemy_collision(
                    enemy, self.game_state)
                if should_remove_projectile:
                    entities_to_remove.append(projectile)

        for player_summon in [npc for npc in self.game_state.non_player_characters
                              if npc.npc_category == NpcCategory.PLAYER_SUMMON]:
            for projectile in self.game_state.get_projectiles_intersecting_with(player_summon.world_entity):
                should_remove_projectile = projectile.projectile_controller.apply_player_summon_collision(
                    player_summon, self.game_state)
                if should_remove_projectile:
                    entities_to_remove.append(projectile)

        for projectile in self.game_state.get_projectiles_intersecting_with(self.game_state.player_entity):
            should_remove_projectile = projectile.projectile_controller.apply_player_collision(self.game_state)
            if should_remove_projectile:
                entities_to_remove.append(projectile)

        for projectile in self.game_state.projectile_entities:
            if self.game_state.does_entity_intersect_with_wall(projectile.world_entity):
                should_remove_projectile = projectile.projectile_controller.apply_wall_collision(self.game_state)
                if should_remove_projectile:
                    entities_to_remove.append(projectile)

        self.game_state.remove_entities(entities_to_remove)

        # ------------------------------------
        #       UPDATE CAMERA POSITION
        # ------------------------------------

        self.game_state.center_camera_on_player()

        if self.game_state.player_state.health_resource.is_at_or_below_zero():
            self._spawn_player_after_death()

    def _spawn_player_after_death(self):
        self.game_state.player_entity.set_position(self.player_spawn_position)
        self.game_state.player_state.health_resource.set_to_partial_of_max(0.5)
        self.game_state.player_state.lose_exp_from_death()
        self.view_state.set_message("Lost exp from dying")
        play_sound(SoundId.EVENT_PLAYER_DIED)
        color = (140, 140, 230)
        effect_position = self.game_state.player_entity.get_center_position()
        self.game_state.visual_effects.append(VisualCircle(color, effect_position, 17, 35, Millis(150), 1))
        self.game_state.visual_effects.append(VisualRect(color, effect_position, 37, 50, Millis(150), 1))
        self.game_state.visual_effects.append(VisualCircle(color, effect_position, 25, 50, Millis(300), 2))

    def _is_npc_close_to_camera(self, npc: NonPlayerCharacter):
        camera_rect_with_margin = get_rect_with_increased_size_in_all_directions(
            self.game_state.camera_world_area.rect(), 100)
        return rects_intersect(npc.world_entity.rect(), camera_rect_with_margin)

    def _put_loot_on_ground(self, enemy_death_position: Tuple[int, int], loot: List[LootEntry]):
        for loot_entry in loot:
            if len(loot) > 1:
                position_offset = (random.randint(-20, 20), random.randint(-20, 20))
            else:
                position_offset = (0, 0)
            loot_position = sum_of_vectors(enemy_death_position, position_offset)

            if loot_entry.money_amount:
                money_pile_on_ground = create_money_pile_on_ground(loot_entry.money_amount, loot_position)
                self.game_state.money_piles_on_ground.append(money_pile_on_ground)
            elif loot_entry.item_type:
                item_on_ground = create_item_on_ground(loot_entry.item_type, loot_position)
                self.game_state.items_on_ground.append(item_on_ground)
            elif loot_entry.consumable_type:
                consumable_on_ground = create_consumable_on_ground(loot_entry.consumable_type, loot_position)
                self.game_state.consumables_on_ground.append(consumable_on_ground)


class AgentBuffsUpdate:
    def __init__(self, buffs_that_started: List[BuffWithDuration], buffs_that_were_active: List[BuffWithDuration],
                 buffs_that_ended: List[BuffWithDuration]):
        self.buffs_that_started = buffs_that_started
        self.buffs_that_were_active = buffs_that_were_active
        self.buffs_that_ended = buffs_that_ended


def handle_buffs(active_buffs: List[BuffWithDuration], time_passed: Millis) -> AgentBuffsUpdate:
    copied_buffs_list = list(active_buffs)
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
            active_buffs.remove(buff)
            buffs_that_ended.append(buff)
    return AgentBuffsUpdate(buffs_that_started, buffs_that_were_active, buffs_that_ended)
