import unittest
from emoji import E
from keyboards import (
    get_main_menu_kb,
    get_result_kb,
    get_resolution_kb,
    get_media_kb,
    get_bg3d_kb,
    get_watermark_kb,
    get_scale_kb,
    get_color_kb,
    build_color_picker_kb,
    get_subscription_kb,
    DANGER,
)


class TestBannerConverterKeyboards(unittest.TestCase):
    def test_main_menu_layout_and_danger_style(self):
        kb = get_main_menu_kb({})
        rows = kb.inline_keyboard
        # 5 rows: 1, 1, 2, 2, 1
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(rows[0]), 1)
        self.assertEqual(len(rows[1]), 1)
        self.assertEqual(len(rows[2]), 2)
        self.assertEqual(len(rows[3]), 2)
        self.assertEqual(len(rows[4]), 1)

        # Primary actions are fiery danger
        self.assertEqual(rows[0][0].text, "Цвет фона")
        self.assertEqual(rows[0][0].style, DANGER)
        self.assertEqual(rows[0][0].icon_custom_emoji_id, E.BRUSH)

        self.assertEqual(rows[1][0].text, "3D Фон")
        self.assertEqual(rows[1][0].style, DANGER)
        self.assertEqual(rows[1][0].icon_custom_emoji_id, E.APPS)

        # Secondary settings
        self.assertEqual(rows[2][0].text, "Разрешение")
        self.assertIsNone(rows[2][0].style)
        self.assertEqual(rows[2][1].text, "ЦветEmoji")
        self.assertIsNone(rows[2][1].style)

    def test_result_kb_has_danger_style(self):
        kb = get_result_kb("output.mp4")
        rows = kb.inline_keyboard
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0].text, "Скачать файлом без сжатия")
        self.assertEqual(rows[0][0].style, DANGER)
        self.assertEqual(rows[0][0].callback_data, "send_doc:output.mp4")
        self.assertEqual(rows[1][0].text, "Настройки")

    def test_resolution_kb_primary_banner(self):
        kb = get_resolution_kb()
        rows = kb.inline_keyboard
        self.assertEqual(rows[0][0].text, "1920x530 (Баннер)")
        self.assertEqual(rows[0][0].style, DANGER)
        self.assertEqual(rows[0][0].callback_data, "set_res:1920x530")

    def test_media_kb_has_danger_style(self):
        kb = get_media_kb(has_custom=True)
        rows = kb.inline_keyboard
        self.assertEqual(rows[0][0].text, "Загрузить медиа")
        self.assertEqual(rows[0][0].style, DANGER)

    def test_color_picker_spectrum_button(self):
        kb = build_color_picker_kb(target="bg", active_cat="classic")
        spectrum_btns = [
            btn for row in kb.inline_keyboard for btn in row if "Спектр-палитра" in btn.text
        ]
        self.assertEqual(len(spectrum_btns), 1)
        self.assertEqual(spectrum_btns[0].style, DANGER)

    def test_back_buttons_no_duplicate_arrows(self):
        keyboards = [
            get_resolution_kb(),
            get_bg3d_kb("solid", True),
            get_media_kb(True),
            get_watermark_kb(True),
            get_scale_kb(100),
            get_color_kb("classic"),
        ]
        for kb in keyboards:
            for row in kb.inline_keyboard:
                for btn in row:
                    self.assertNotIn("◁", btn.text)
                    self.assertNotIn("◀", btn.text)
                    self.assertNotIn("⬅", btn.text)

    def test_subscription_kb(self):
        kb = get_subscription_kb("https://t.me/gifthemy")
        rows = kb.inline_keyboard
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0].text, "Подписаться на канал")
        self.assertEqual(rows[0][0].url, "https://t.me/gifthemy")
        self.assertEqual(rows[0][0].icon_custom_emoji_id, E.LINK)
        self.assertEqual(rows[1][0].text, "Проверить подписку")
        self.assertEqual(rows[1][0].callback_data, "check_subscription")
        self.assertEqual(rows[1][0].style, DANGER)
        self.assertEqual(rows[1][0].icon_custom_emoji_id, E.CHECK)

    def test_unified_gate_kb(self):
        from keyboards import get_unified_gate_kb
        kb = get_unified_gate_kb("https://t.me/gifthemy")
        rows = kb.inline_keyboard
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][0].text, "Подписаться на канал")
        self.assertEqual(rows[0][0].url, "https://t.me/gifthemy")
        self.assertEqual(rows[1][0].text, "Пользовательское соглашение")
        self.assertEqual(rows[1][0].callback_data, "legal:terms")
        self.assertEqual(rows[2][0].text, "Принять условия и войти")
        self.assertEqual(rows[2][0].callback_data, "action:accept_gate")
        self.assertEqual(rows[2][0].style, DANGER)


