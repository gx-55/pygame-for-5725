from enum import Enum
from math import floor
from typing import List, Tuple, Optional, Any, Iterable

import pygame
from pygame.rect import Rect

from pythongame.core.common import ConsumableType, ItemType, AbilityType, PortraitIconSprite, HeroId
from pythongame.core.game_data import CONSUMABLES, ConsumableCategory, AbilityData, ConsumableData
from pythongame.core.game_state import PlayerState
from pythongame.core.item_inventory import ItemEquipmentCategory
from pythongame.core.talents import TalentTierStatus
from pythongame.core.view.render_util import DrawableArea, split_text_into_lines
from pythongame.scenes_game.game_ui_state import ToggleButtonId

COLOR_BLACK = (0, 0, 0)
COLOR_LIGHT_GRAY = (240, 240, 240)
COLOR_GRAY = (200, 200, 200)
COLOR_DARK_GRAY = (100, 100, 100)
COLOR_WHITE = (250, 250, 250)

COLOR_ICON_OUTLINE = (150, 150, 190)
COLOR_BUTTON_OUTLINE = (150, 150, 190)
COLOR_HOVERED = (200, 200, 250)
COLOR_ICON_HIGHLIGHTED = (250, 250, 150)
COLOR_TOGGLE_HIGHLIGHTED = (150, 250, 200)
COLOR_TOGGLE_OPENED = (50, 50, 120)
DIR_FONTS = './resources/fonts/'

TALENT_ICON_SIZE = (32, 32)


class UiComponent:
    def __init__(self):
        self.hovered = False


class DialogOption:
    def __init__(self, summary: str, detail_action_text: str, detail_image: Optional[Any],
                 detail_header: Optional[str] = None, detail_body: Optional[str] = None):
        self.summary = summary
        self.detail_action_text = detail_action_text
        self.detail_image = detail_image
        self.detail_header = detail_header
        self.detail_body = detail_body


class Dialog:
    def __init__(self, screen_render: DrawableArea, portrait_image: PortraitIconSprite, text_body: str,
                 options: List[DialogOption], active_option_index: int, portrait_image_size: Tuple[int, int],
                 option_image_size: Tuple[int, int]):
        self.screen_render = screen_render
        self.portrait_image = portrait_image
        self.text_body = text_body
        self.options = options
        self.active_option_index = active_option_index
        self.font_dialog = pygame.font.Font(DIR_FONTS + 'Merchant Copy.ttf', 24)
        self.font_dialog_option_detail_body = pygame.font.Font(DIR_FONTS + 'Monaco.dfont', 12)
        self.portrait_image_size = portrait_image_size
        self.option_image_size = option_image_size
        self.shown = False

    def render(self):
        if self.shown:
            self._render()

    def _render(self):

        tall_detail_section = any(
            [o.detail_body is not None or o.detail_header is not None or o.detail_image is not None
             for o in self.options])

        h_detail_section_expansion = 82

        options_margin = 10
        option_padding = 4
        h_option_line = 20
        if tall_detail_section:
            h_dialog_container = 310 + len(self.options) * (h_option_line + 2 * option_padding)
        else:
            h_dialog_container = 310 + len(self.options) * (h_option_line + 2 * option_padding) \
                                 - h_detail_section_expansion
        rect_dialog_container = Rect(100, 35, 500, h_dialog_container)

        x_left = rect_dialog_container[0]
        x_right = rect_dialog_container[0] + rect_dialog_container[2]
        self.screen_render.rect((210, 180, 60), rect_dialog_container, 5)
        self.screen_render.rect_transparent(rect_dialog_container, 200, COLOR_BLACK)
        color_separator = (170, 140, 20)
        dialog_container_portrait_padding = 10
        rect_portrait_pos = (x_left + dialog_container_portrait_padding,
                             rect_dialog_container[1] + dialog_container_portrait_padding)
        self.screen_render.image(self.portrait_image, rect_portrait_pos)
        rect_portrait = Rect(rect_portrait_pos[0], rect_portrait_pos[1], self.portrait_image_size[0],
                             self.portrait_image_size[1])
        self.screen_render.rect((160, 160, 180), rect_portrait, 2)

        dialog_pos = (x_left + 120, rect_dialog_container[1] + 15)
        dialog_lines = split_text_into_lines(self.text_body, 35)
        for i, dialog_text_line in enumerate(dialog_lines):
            if i == 6:
                print("WARN: too long dialog for NPC!")
                break
            self.screen_render.text(self.font_dialog, dialog_text_line, (dialog_pos[0] + 5, dialog_pos[1] + 32 * i),
                                    COLOR_WHITE)

        y_above_options = dialog_pos[1] + 150
        self.screen_render.line(color_separator, (x_left, y_above_options), (x_right, y_above_options), 2)

        for i, option in enumerate(self.options):
            x_option = x_left + 8
            y_option = y_above_options + options_margin + i * (h_option_line + 2 * option_padding)
            x_option_text = x_option + option_padding + 5
            y_option_text = y_option + option_padding + 2
            color_highlight = COLOR_WHITE

            is_option_active = self.active_option_index == i
            color_option_text = COLOR_WHITE if is_option_active else (160, 160, 160)
            if is_option_active:
                rect_highlight_active_option = Rect(
                    x_option, y_option, rect_dialog_container[2] - 16, h_option_line + 2 * option_padding)
                self.screen_render.rect_transparent(rect_highlight_active_option, 120, COLOR_WHITE)
                self.screen_render.rect(color_highlight, rect_highlight_active_option, 1)
            self.screen_render.text(self.font_dialog, option.summary, (x_option_text, y_option_text), color_option_text)

        active_option = self.options[self.active_option_index]
        y_under_options = y_above_options + 2 * options_margin \
                          + len(self.options) * (h_option_line + 2 * option_padding)
        self.screen_render.line(color_separator, (x_left, y_under_options), (x_right, y_under_options), 2)

        if tall_detail_section:
            y_action_text = y_under_options + 15 + h_detail_section_expansion
        else:
            y_action_text = y_under_options + 15

        if tall_detail_section:
            if active_option.detail_image is not None:
                active_option_image = active_option.detail_image
                pos_option_image = x_left + 6, y_under_options + 7
                self.screen_render.image(active_option_image, pos_option_image)
                rect_option_image = Rect(pos_option_image[0], pos_option_image[1], self.option_image_size[0],
                                         self.option_image_size[1])
                self.screen_render.rect((150, 150, 150), rect_option_image, 1)
            if active_option.detail_header is not None:
                self.screen_render.text(self.font_dialog, active_option.detail_header,
                                        (x_left + 14 + self.option_image_size[0] + 4,
                                         y_action_text - h_detail_section_expansion))
            if active_option.detail_body is not None:
                detail_body_lines = split_text_into_lines(active_option.detail_body, 70)
                for i, line in enumerate(detail_body_lines):
                    line_pos = (x_left + 10, y_action_text - h_detail_section_expansion + 35 + 20 * i)
                    self.screen_render.text(self.font_dialog_option_detail_body, line, line_pos)
        action_text = active_option.detail_action_text
        self.screen_render.text(self.font_dialog, "[Space] : " + action_text, (x_left + 10, y_action_text))


class TooltipGraphics:
    def __init__(self, ui_render: DrawableArea, title_color: Tuple[int, int, int],
                 title: str, details: List[str], bottom_left: Optional[Tuple[int, int]] = None,
                 bottom_right: Optional[Tuple[int, int]] = None):
        self._ui_render = ui_render
        self._font_header = pygame.font.Font(DIR_FONTS + 'Herculanum.ttf', 16)
        self._font_details = pygame.font.Font(DIR_FONTS + 'Monaco.dfont', 12)
        self._title_color = title_color
        self._title = title
        self._detail_lines = []
        for detail in details:
            self._detail_lines += split_text_into_lines(detail, 32)
        w = 260
        h = 60 + 17 * len(self._detail_lines)
        if bottom_left:
            self._rect = Rect(bottom_left[0], bottom_left[1] - h - 3, w, h)
        else:
            self._rect = Rect(bottom_right[0] - w, bottom_right[1] - h - 3, w, h)

    def render(self):
        self._ui_render.rect_transparent(self._rect, 200, (0, 0, 0))
        self._ui_render.rect(COLOR_DARK_GRAY, self._rect, 1)
        header_position = (self._rect.x + 20, self._rect.y + 12)
        self._ui_render.text(self._font_header, self._title, header_position, self._title_color)
        y_separator = self._rect.y + 37
        separator_start = (self._rect.x + 10, y_separator)
        separator_end = (self._rect.x + self._rect.w - 10, y_separator)
        self._ui_render.line(COLOR_WHITE, separator_start, separator_end, 1)
        for i, line in enumerate(self._detail_lines):
            self._ui_render.text(self._font_details, line, (self._rect.x + 20, self._rect.y + 47 + i * 18), COLOR_WHITE)


class AbilityIcon(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, image, label: str, font, tooltip: TooltipGraphics,
                 ability_type: AbilityType, cooldown_remaining_ratio: float):
        super().__init__()
        self._ui_render = ui_render
        self._font = font
        self.rect = rect
        self.image = image
        self.label = label
        self.tooltip = tooltip
        self.ability_type = ability_type
        self.cooldown_remaining_ratio = cooldown_remaining_ratio

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point[0], point[1])

    def render(self, recently_clicked: bool):
        self._ui_render.rect_filled((40, 40, 50), self.rect)
        self._ui_render.image(self.image, self.rect.topleft)
        self._ui_render.rect(COLOR_ICON_OUTLINE, self.rect, 1)
        if recently_clicked:
            self._ui_render.rect(COLOR_ICON_HIGHLIGHTED,
                                 Rect(self.rect.x - 1, self.rect.y - 1, self.rect.w + 2, self.rect.h + 2), 3)
        elif self.hovered:
            self._ui_render.rect(COLOR_HOVERED, self.rect, 1)
        self._ui_render.text(self._font, self.label, (self.rect.x + 12, self.rect.y + self.rect.h + 4))

        if self.cooldown_remaining_ratio > 0:
            cooldown_rect = Rect(self.rect.x + 1,
                                 self.rect.y + 1 + (self.rect.h - 2) * (1 - self.cooldown_remaining_ratio),
                                 self.rect.w - 2,
                                 (self.rect.h - 2) * self.cooldown_remaining_ratio + 1)
            self._ui_render.rect_filled((100, 30, 30), cooldown_rect)
            self._ui_render.rect((180, 30, 30), self.rect, 2)

    def update(self, image, label: str, ability: AbilityData, ability_type: AbilityType):
        self.image = image
        self.label = label
        tooltip_details = ["Cooldown: " + str(ability.cooldown / 1000.0) + " s",
                           "Mana: " + str(ability.mana_cost),
                           ability.description]
        self.tooltip = TooltipGraphics(self._ui_render, COLOR_WHITE, ability.name, tooltip_details,
                                       bottom_left=self.rect.topleft)
        self.ability_type = ability_type


class ConsumableIcon(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, image, label: str, font, tooltip: TooltipGraphics,
                 consumable_types: List[ConsumableType], slot_number: int):
        super().__init__()
        self._ui_render = ui_render
        self._rect = rect
        self._image = image
        self._label = label
        self._font = font
        self.consumable_types = consumable_types
        self.tooltip = tooltip
        self.slot_number = slot_number

    def get_collision_offset(self, point: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        if self._rect.collidepoint(point[0], point[1]):
            return point[0] - self._rect.x, point[1] - self._rect.y
        return None

    def render(self, recently_clicked: bool):
        self._ui_render.rect_filled((40, 40, 50), self._rect)
        if self._image:
            self._ui_render.image(self._image, self._rect.topleft)
        self._ui_render.rect(COLOR_ICON_OUTLINE, self._rect, 1)

        sub_rect_h = 3
        for i in range(len(self.consumable_types)):
            sub_consumable_type = self.consumable_types[i]
            consumable_category = CONSUMABLES[sub_consumable_type].category
            if consumable_category == ConsumableCategory.HEALTH:
                sub_rect_color = (160, 110, 110)
            elif consumable_category == ConsumableCategory.MANA:
                sub_rect_color = (110, 110, 200)
            else:
                sub_rect_color = (170, 170, 170)
            self._ui_render.rect_filled(
                sub_rect_color,
                Rect(self._rect.x, self._rect.y - 2 - (sub_rect_h + 1) * (i + 1), self._rect.w, sub_rect_h))

        if recently_clicked:
            self._ui_render.rect(COLOR_ICON_HIGHLIGHTED,
                                 Rect(self._rect.x - 1, self._rect.y - 1, self._rect.w + 2, self._rect.h + 2), 3)
        elif self.hovered:
            self._ui_render.rect(COLOR_HOVERED, self._rect, 1)
        self._ui_render.text(self._font, self._label, (self._rect.x + 12, self._rect.y + self._rect.h + 4))

    def update(self, image, top_consumable: ConsumableData, consumable_types: List[ConsumableType]):
        self._image = image
        self.consumable_types = consumable_types
        if top_consumable:
            self.tooltip = TooltipGraphics(self._ui_render, COLOR_WHITE, top_consumable.name,
                                           [top_consumable.description], bottom_left=self._rect.topleft)
        else:
            self.tooltip = None


class ItemIcon(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, image, tooltip: TooltipGraphics,
                 slot_equipment_category: ItemEquipmentCategory, item_type: ItemType, inventory_slot_index: int):
        super().__init__()
        self._ui_render = ui_render
        self.rect = rect
        self._rect_highlighted = Rect(self.rect.x - 1, self.rect.y - 1, self.rect.w + 1, self.rect.h + 1)
        self.image = image
        self.slot_equipment_category = slot_equipment_category
        self.tooltip = tooltip
        self.item_type = item_type
        self.inventory_slot_index = inventory_slot_index

    def get_collision_offset(self, point: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        if self.rect.collidepoint(point[0], point[1]):
            return point[0] - self.rect.x, point[1] - self.rect.y
        return None

    def render(self, highlighted: bool):
        has_equipped_item = self.slot_equipment_category and self.item_type
        color_bg = (60, 60, 90) if has_equipped_item else (40, 40, 50)
        color_outline = (160, 160, 160) if has_equipped_item else (100, 100, 140)

        self._ui_render.rect_filled(color_bg, self.rect)
        if self.image:
            self._ui_render.image(self.image, self.rect.topleft)
        self._ui_render.rect(color_outline, self.rect, 1)

        if highlighted:
            self._ui_render.rect(COLOR_ICON_HIGHLIGHTED, self._rect_highlighted, 2)
        elif self.hovered:
            self._ui_render.rect(COLOR_HOVERED, self.rect, 1)


class StatBar:
    def __init__(self, ui_render: DrawableArea, rect: Rect, color: Tuple[int, int, int], tooltip: TooltipGraphics,
                 value: int, max_value: int, show_numbers: bool, font):
        self.ui_render = ui_render
        self.rect = rect
        self.color = color
        self.tooltip = tooltip
        self.show_numbers = show_numbers
        self.font = font
        self._value = value
        self._max_value = max_value
        self.ratio_filled = self._value / self._max_value

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point[0], point[1])

    def render(self):
        self.ui_render.stat_bar(
            self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.ratio_filled, self.color, (160, 160, 180))
        if self.show_numbers:
            text = str(self._value) + "/" + str(self._max_value)
            self.ui_render.text(self.font, text, (self.rect.x + 20, self.rect.y - 1))

    def update(self, value: int, max_value: int):
        self._value = value
        self._max_value = max_value
        self.ratio_filled = self._value / self._max_value


class UiWindow:
    def __init__(self):
        self.shown = False


class ToggleButton(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, font, text: str, toggle_id: ToggleButtonId,
                 highlighted: bool,
                 linked_window: UiWindow):
        super().__init__()
        self.ui_render = ui_render
        self.rect = rect
        self.font = font
        self.text = text
        self.toggle_id = toggle_id
        self.highlighted = highlighted
        self.tooltip = None
        self.is_open = False
        self.linked_window = linked_window

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point[0], point[1])

    def render(self):
        if self.is_open:
            self.ui_render.rect_filled(COLOR_TOGGLE_OPENED, self.rect)
        self.ui_render.rect(COLOR_BUTTON_OUTLINE, self.rect, 1)
        text_color = COLOR_WHITE if self.hovered or self.highlighted else COLOR_LIGHT_GRAY
        self.ui_render.text(self.font, self.text, (self.rect.x + 20, self.rect.y + 2), text_color)
        if self.hovered:
            self.ui_render.rect(COLOR_HOVERED, self.rect, 1)
        if self.highlighted:
            self.ui_render.rect(COLOR_TOGGLE_HIGHLIGHTED, self.rect, 1)

    def open(self):
        self.is_open = True
        self.highlighted = False
        self.linked_window.shown = True

    def close(self):
        self.is_open = False
        self.linked_window.shown = False


class Checkbox(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, font, label: str, checked: bool):
        super().__init__()
        self.ui_render = ui_render
        self.rect = rect
        self.font = font
        self.label = label
        self.checked = checked
        self.tooltip = None

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point[0], point[1])

    def render(self):
        self.ui_render.rect(COLOR_BUTTON_OUTLINE, self.rect, 1)
        text = self.label + ": " + ("Y" if self.checked else "N")
        text_color = COLOR_WHITE if self.hovered else COLOR_LIGHT_GRAY
        self.ui_render.text(self.font, text, (self.rect.x + 4, self.rect.y + 2), text_color)
        if self.hovered:
            self.ui_render.rect(COLOR_HOVERED, self.rect, 1)

    def on_click(self):
        self.checked = not self.checked


class Button(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, font, text: str):
        super().__init__()
        self.ui_render = ui_render
        self.rect = rect
        self.font = font
        self.text = text
        self.tooltip = None

    def contains(self, point: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(point[0], point[1])

    def render(self):
        self.ui_render.rect(COLOR_BUTTON_OUTLINE, self.rect, 1)
        text_color = COLOR_WHITE if self.hovered else COLOR_LIGHT_GRAY
        self.ui_render.text(self.font, self.text, (self.rect.x + 7, self.rect.y + 2), text_color)
        if self.hovered:
            self.ui_render.rect(COLOR_HOVERED, self.rect, 1)


class ControlsWindow(UiWindow):
    def __init__(self, ui_render: DrawableArea, font_header, font_details):
        super().__init__()
        self._ui_render = ui_render
        self._rect = Rect(365, -360, 320, 310)
        self._font_header = font_header
        self._font_details = font_details

    def render(self):
        if self.shown:
            self._render()

    def _render(self):

        self._ui_render.rect_filled((50, 50, 50), self._rect)
        self._ui_render.rect((80, 50, 50), self._rect, 2)
        w = 135
        h = 20
        x = self._rect.left + self._rect.w // 2 - w // 2
        y = self._rect.top + 15
        rect = Rect(x, y - 3, w, h)
        self._ui_render.rect_filled((40, 40, 40), rect)
        self._ui_render.text(self._font_header, "HELP", (x + 50, y))

        x = self._rect[0] + 15

        y = self._rect[1] + 45
        self._ui_render.text(self._font_header, "Basic controls", (x, y), (220, 220, 250))
        y += 24
        text_basic_controls = split_text_into_lines(
            "Move with the arrow-keys. Attack with 'Q'. Use potions with the number-keys ('1' through '5').", 47)
        for line in text_basic_controls:
            self._ui_render.text(self._font_details, line, (x, y))
            y += 16

        y += 10
        self._ui_render.text(self._font_header, "Inventory", (x, y), (220, 220, 250))
        y += 24
        text_inventory = "Potions and items can be moved around in your inventory by dragging them with the mouse. " \
                         "Wearables must be put in the appropriate inventory slot to be effective!"
        for line in split_text_into_lines(text_inventory, 47):
            self._ui_render.text(self._font_details, line, (x, y))
            y += 16

        y += 10
        self._ui_render.text(self._font_header, "Interactions", (x, y), (220, 220, 250))
        y += 24
        text_inventory = "Use the 'Space' key to interact with NPC's and objects in your surroundings. Be sure to " \
                         "talk to NPC's to fill up on potions, and complete quests. "
        for line in split_text_into_lines(text_inventory, 47):
            self._ui_render.text(self._font_details, line, (x, y))
            y += 16


class StatsWindow(UiWindow):
    def __init__(self, ui_render: DrawableArea, font_header, font_details, player_state: PlayerState,
                 player_speed_multiplier: float, hero_id: HeroId, level: int):
        super().__init__()
        self.ui_render = ui_render
        self.rect = Rect(365, -380, 320, 330)
        self.font_header = font_header
        self.font_details = font_details
        self.player_state = player_state
        self.player_speed_multiplier = player_speed_multiplier
        self.hero_id = hero_id
        self.level = level

    def render(self):
        if self.shown:
            self._render()

    def _render(self):
        self.ui_render.rect_filled((50, 50, 50), self.rect)
        self.ui_render.rect((80, 50, 50), self.rect, 2)

        player_state = self.player_state
        health = player_state.health_resource
        mana = player_state.mana_resource

        x_left = self.rect[0] + 15
        x_right = x_left + 155
        y_0 = self.rect[1] + 15

        perc = lambda value: int(value * 100)

        y_hero_and_level = y_0
        self._render_header((x_left, y_hero_and_level), self.hero_id.name)
        self._render_header((x_right, y_hero_and_level), "Level " + str(self.level))

        y_health = y_0 + 40
        self._render_sub_header((x_left, y_health), "HEALTH")
        self._render_stat((x_left, y_health + 25), "max", health.max_value)
        self._render_stat((x_left, y_health + 45), "regen", health.base_regen, health.get_effective_regen())

        y_mana = y_0 + 40
        self._render_sub_header((x_right, y_mana), "MANA")
        self._render_stat((x_right, y_mana + 25), "max", mana.max_value)
        self._render_stat((x_right, y_mana + 45), "regen", mana.base_regen, mana.get_effective_regen())

        y_damage = y_0 + 130
        self._render_sub_header((x_left, y_damage), "DAMAGE")
        self._render_stat((x_left, y_damage + 25), "physical %", perc(player_state.base_physical_damage_modifier),
                          perc(player_state.get_effective_physical_damage_modifier()))
        self._render_stat((x_left, y_damage + 45), "magic %", perc(player_state.base_magic_damage_modifier),
                          perc(player_state.get_effective_magic_damage_modifier()))

        y_defense = y_0 + 130
        self._render_sub_header((x_right, y_defense), "DEFENSE")
        self._render_stat((x_right, y_defense + 25), "armor", str(floor(player_state.base_armor)),
                          str(floor(player_state.base_armor + player_state.armor_bonus)))
        self._render_stat((x_right, y_defense + 45), "dodge %", perc(player_state.base_dodge_chance),
                          perc(player_state.get_effective_dodge_change()))
        self._render_stat((x_right, y_defense + 65), "block %", perc(player_state.block_chance))
        self._render_stat((x_right, y_defense + 85), "amount", player_state.block_damage_reduction)

        y_misc = y_0 + 220
        self._render_sub_header((x_left, y_misc), "MISC.")
        self._render_stat((x_left, y_misc + 25), "speed %", perc(self.player_speed_multiplier))
        self._render_stat((x_left, y_misc + 45), "lifesteal %", perc(player_state.life_steal_ratio))

    def _render_header(self, pos: Tuple[int, int], text: str):
        w = 135
        h = 20
        rect = Rect(pos[0], pos[1] - 3, w, h)
        self.ui_render.rect_filled((40, 40, 40), rect)
        text_pos = (pos[0] + w // 2 - 2 - len(text) * 3, pos[1])
        self.ui_render.text(self.font_header, text, text_pos)

    def _render_sub_header(self, pos: Tuple[int, int], text: str):
        w = 70
        text_pos = (pos[0] + w // 2 - 2 - len(text) * 3, pos[1])
        self.ui_render.text(self.font_header, text, text_pos, (220, 220, 250))

    def _render_stat(self, label_pos: Tuple[int, int], label: str, value: Any, value_with_bonus: Optional[Any] = None):
        x_label, y = label_pos
        w_label_rect = 70
        rect_label = Rect(x_label, y - 2, w_label_rect, 15)
        self.ui_render.rect_filled((40, 40, 40), rect_label)
        x_label_text = x_label + w_label_rect // 2 - len(label) * 3
        self.ui_render.text(self.font_details, label, (x_label_text, y))
        x_value = x_label + 80
        w_value_rect = 30
        color_rect_bg = (20, 20, 20)
        self._render_value(color_rect_bg, value, w_value_rect, (x_value, y), COLOR_WHITE)
        if value_with_bonus is not None:
            color = (170, 230, 170) if value_with_bonus > value else COLOR_WHITE
            x_value_2 = x_value + w_value_rect - 1
            self._render_value(color_rect_bg, value_with_bonus, w_value_rect, (x_value_2, y), color)

    def _render_value(self, color_bg, value, w_rect, position: Tuple[int, int], color: Tuple[int, int, int]):
        text = str(value)
        x, y = position
        rect = Rect(x - 5, y - 2, w_rect, 15)
        x_text = x + w_rect // 2 - 3 - len(text) * 4
        self.ui_render.rect_filled(color_bg, rect)
        self.ui_render.rect(COLOR_GRAY, rect, 1)
        self.ui_render.text(self.font_details, text, (x_text, y), color)


class TalentIconStatus(Enum):
    PENDING = 1
    PICKED = 2
    FADED = 3


class TalentOptionData:
    def __init__(self, name: str, description: str, image):
        self.name = name
        self.description = description
        self.image = image


class TalentTierData:
    def __init__(self, status: TalentTierStatus, level_required: int, picked_index: Optional[int],
                 options: List[TalentOptionData]):
        self.status = status
        self.level_required = level_required
        self.picked_index = picked_index
        self.options = options


class TalentIcon(UiComponent):
    def __init__(self, ui_render: DrawableArea, rect: Rect, image, tooltip: TooltipGraphics, chosen: bool,
                 talent_name: str, font, tier_index: int, option_index: int, status: TalentIconStatus):
        super().__init__()
        self._ui_render = ui_render
        self._rect = rect
        self._image = image
        self._chosen = chosen
        self._font = font
        self._status = status

        self.tooltip = tooltip
        self.talent_name = talent_name
        self.tier_index = tier_index
        self.option_index = option_index

    def contains(self, point: Tuple[int, int]) -> bool:
        return self._rect.collidepoint(point[0], point[1])

    def render(self):
        self._ui_render.rect_filled(COLOR_BLACK, self._rect)
        self._ui_render.image(self._image, self._rect.topleft)

        if self._status == TalentIconStatus.FADED:
            self._ui_render.rect_transparent(self._rect, 150, (50, 0, 0))
        elif self._status == TalentIconStatus.PICKED:
            self._ui_render.rect((250, 250, 150), self._rect, 2)
        elif self._status == TalentIconStatus.PENDING:
            self._ui_render.rect((150, 150, 150), self._rect, 1)
        if self.hovered:
            self._ui_render.rect(COLOR_HOVERED, self._rect, 1)


class TalentTier:
    def __init__(self, ui_render: DrawableArea, rect: Rect, font, icons: List[TalentIcon],
                 status: TalentTierStatus, picked_index: int, level_required: int):
        super().__init__()
        self._ui_render = ui_render
        self._rect = rect
        self._font = font
        self.icons = icons
        self._status = status
        self._picked_index = picked_index
        self._level_required = level_required

    def render(self):
        if self._status == TalentTierStatus.PENDING:
            self._ui_render.rect_transparent(self._rect, 30, (50, 250, 50))
            self._render_text("<-- Pick one!", COLOR_WHITE, False)
        elif self._status == TalentTierStatus.PICKED:
            self._render_text(self.icons[self._picked_index].talent_name, COLOR_WHITE, True)
        elif self._status == TalentTierStatus.LOCKED:
            self._render_text("Locked (level " + str(self._level_required) + ")", (150, 75, 75), False)
        self.icons[0].render()
        self.icons[1].render()

    def _render_text(self, text: str, color: Tuple[int, int, int], background: bool):
        x = self._rect.right - 50 - len(text) * 3
        y = self._rect.top + 17
        if background:
            w_label_rect = 90
            rect_label = Rect(self._rect.right - 95, y - 2, w_label_rect, 15)
            self._ui_render.rect_filled((40, 40, 40), rect_label)
        self._ui_render.text(self._font, text, (x, y), color)

    def is_pickable(self) -> bool:
        return self._status == TalentTierStatus.PENDING


class TalentsWindow(UiWindow):
    def __init__(self, ui_render: DrawableArea, font_header, font_details,
                 talent_tiers: List[TalentTierData]):
        super().__init__()
        self._ui_render = ui_render
        self._rect = Rect(475, -420, 210, 370)
        self._font_header = font_header
        self._font_details = font_details

        self._talent_tiers: List[TalentTier] = []
        self.update(talent_tiers)

    def get_icon_containing(self, point: Tuple[int, int]) -> Optional[TalentIcon]:
        for tier in self._talent_tiers:
            for icon in tier.icons:
                if icon.contains(point):
                    return icon
        return None

    def get_pickable_talent_icons(self) -> Iterable[TalentIcon]:
        if self._talent_tiers:
            for tier in self._talent_tiers:
                if tier.is_pickable():
                    yield from tier.icons

    def render(self):
        if self.shown:
            self._render()

    def _render(self):
        self._ui_render.rect_filled((50, 50, 50), self._rect)
        self._ui_render.rect((80, 50, 50), self._rect, 2)
        w = 135
        h = 20
        x = self._rect.left + self._rect.w // 2 - w // 2
        y = self._rect.top + 15
        rect = Rect(x, y - 3, w, h)
        self._ui_render.rect_filled((40, 40, 40), rect)
        self._ui_render.text(self._font_header, "TALENTS", (x + 40, y))

        for tier in self._talent_tiers:
            tier.render()

    def update(self, talent_tiers: List[TalentTierData]):
        window_padding = 10
        tier_padding = 5
        h_tier = TALENT_ICON_SIZE[1] + tier_padding * 2
        self._talent_tiers: List[TalentTier] = []
        tier_row_space = 5
        for tier_index, tier_data in enumerate(talent_tiers):

            rect_tier = Rect(
                self._rect.left + window_padding,
                self._rect.top + 45 + (h_tier + tier_row_space) * tier_index,
                self._rect.w - window_padding * 2,
                h_tier)

            icons = []
            for option_index, option in enumerate(tier_data.options):
                if tier_data.status == TalentTierStatus.PICKED:
                    status = TalentIconStatus.PICKED if tier_data.picked_index == option_index else TalentIconStatus.FADED
                elif tier_data.status == TalentTierStatus.PENDING:
                    status = TalentIconStatus.PENDING
                else:
                    status = TalentIconStatus.FADED
                rect_icon = Rect(rect_tier.left + tier_padding + (TALENT_ICON_SIZE[0] + 15) * option_index,
                                 rect_tier.top + tier_padding,
                                 TALENT_ICON_SIZE[0],
                                 TALENT_ICON_SIZE[1])
                tooltip = TooltipGraphics(self._ui_render, COLOR_WHITE, option.name, [option.description],
                                          bottom_right=(rect_icon.right, rect_icon.top - 2))
                icons.append(
                    TalentIcon(self._ui_render, rect_icon,
                               option.image, tooltip, False, option.name, self._font_details, tier_index, option_index,
                               status))

            tier = TalentTier(self._ui_render, rect_tier, self._font_details, icons,
                              tier_data.status, tier_data.picked_index, tier_data.level_required)
            self._talent_tiers.append(tier)


class ExpBar:
    def __init__(self, ui_render: DrawableArea, rect: Rect, font):
        self.ui_render = ui_render
        self.rect = rect
        self.font = font
        self.level = 1
        self.filled_ratio = 0

    def render(self):
        self.ui_render.text(self.font, "LEVEL: " + str(self.level), (self.rect.x, self.rect.y - 18))
        self.ui_render.stat_bar(self.rect.x, self.rect.y, self.rect.w, self.rect.h, self.filled_ratio, (200, 200, 200),
                                (160, 160, 180))

    def update(self, level: int, filled_ratio: float):
        self.level = level
        self.filled_ratio = filled_ratio


class Portrait:
    def __init__(self, ui_render: DrawableArea, rect: Rect, image):
        self.ui_render = ui_render
        self.rect = rect
        self.image = image

    def render(self):
        self.ui_render.image(self.image, self.rect.topleft)
        self.ui_render.rect((160, 160, 180), self.rect, 2)


class Minimap:
    def __init__(self, ui_render: DrawableArea, rect: Rect):
        self.ui_render = ui_render
        self.rect = rect
        self.padding_rect = Rect(rect.x - 2, rect.y - 2, rect.w + 4, rect.h + 4)

    def render(self, player_relative_position: Tuple[float, float]):
        self.ui_render.rect_filled((60, 60, 80), self.padding_rect)
        self.ui_render.rect_filled((40, 40, 50), self.rect)
        self.ui_render.rect((150, 150, 190), self.rect, 1)
        dot_x = self.rect[0] + player_relative_position[0] * self.rect.w
        dot_y = self.rect[1] + player_relative_position[1] * self.rect.h
        dot_w = 4
        self.ui_render.rect_filled((100, 160, 100), Rect(dot_x - dot_w / 2, dot_y - dot_w / 2, dot_w, dot_w))


class Buffs:
    def __init__(self, ui_render: DrawableArea, font, bottomleft: Tuple[int, int]):
        self.ui_render = ui_render
        self.font = font
        self.bottomleft = bottomleft
        self.rect_padding = 5
        self.w = 140 + self.rect_padding * 2
        self.buffs = []
        h = len(self.buffs) * 25 + self.rect_padding * 2
        self.rect = Rect(self.bottomleft[0], self.bottomleft[1] - h, self.w, h)

    def render(self):
        if self.buffs:
            self.ui_render.rect_transparent(self.rect, 125, COLOR_BLACK)
            for i, (text, ratio_remaining) in enumerate(self.buffs):
                x = self.rect[0] + self.rect_padding
                y = self.rect[1] + self.rect_padding + i * 25
                self.ui_render.text(self.font, text, (x, y))
                self.ui_render.stat_bar(x, y + 20, 60, 2, ratio_remaining, (250, 250, 0))

    def update(self, buffs: List[Tuple[str, float]]):
        self.buffs = buffs
        h = len(self.buffs) * 25 + self.rect_padding * 2
        self.rect = Rect(self.bottomleft[0], self.bottomleft[1] - h, self.w, h)


class Text:
    def __init__(self, ui_render: DrawableArea, font, ui_position: Tuple[int, int], text: str):
        self.ui_render = ui_render
        self.font = font
        self.ui_position = ui_position
        self.text = text

    def render(self):
        self.ui_render.text(self.font, self.text, self.ui_position)


class Message:

    def __init__(self, screen_render: DrawableArea, font, center_x: int, y: int):
        self.screen_render = screen_render
        self.font = font
        self.center_x = center_x
        self.y = y

    def render(self, message: Optional[str]):
        if message:
            w = len(message) * 9 + 10
            text_x = self.center_x - w // 2
            rect = Rect(text_x - 10, self.y - 5, w, 28)
            self.screen_render.rect_transparent(rect, 135, (0, 0, 0))
            self.screen_render.text(self.font, message, (text_x, self.y))


class PausedSplashScreen:

    def __init__(self, screen_render: DrawableArea, font, rect: Rect):
        self._screen_render = screen_render
        self._font = font
        self._rect = rect
        self.shown = False

    def render(self):
        if self.shown:
            self._screen_render.rect_transparent(self._rect, 140, COLOR_BLACK)
            self._double_text("PAUSED", self._rect.w // 2 - 110, self._rect.h // 2 - 50)

    def _double_text(self, text, x, y):
        self._screen_render.text(self._font, text, (x, y), COLOR_WHITE)
        self._screen_render.text(self._font, text, (x + 2, y + 2), COLOR_BLACK)
