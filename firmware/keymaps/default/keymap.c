// Copyright 2023 QMK
// SPDX-License-Identifier: GPL-2.0-or-later

#include QMK_KEYBOARD_H

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_DOT,    KC_MINS,   KC_SPC,   KC_H,
        KC_LCTL,   KC_RGUI
    )
};
