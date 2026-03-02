"""Application coordinator: assembles and orchestrates all modules."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from PySide6.QtCore import QObject, QPoint, Signal, Slot, QTimer

from netherix.brain.intent_parser import Intent, IntentParser
from netherix.brain.llm_client import LLMClient
from netherix.brain.memory import ConversationMemory
from netherix.brain.planner import ExecutionPlan, StepType, TaskPlanner
from netherix.automation.app_launcher import AppLauncher
from netherix.automation.file_operator import FileOperator
from netherix.automation.mouse_keyboard import MouseKeyboardController
from netherix.automation.system_control import SystemController
from netherix.pet.pet_widget import PetWidget
from netherix.pet.sprite_engine import PetState
from netherix.skills.base_skill import SkillResult
from netherix.skills.builtin.reminder import ReminderSkill
from netherix.skills.builtin.translator import TranslatorSkill
from netherix.skills.skill_manager import SkillManager
from netherix.ui.chat_bubble import ChatBubble
from netherix.ui.input_box import FloatingInputBox
from netherix.ui.settings_dialog import SettingsDialog
from netherix.ui.tray import TrayManager
from netherix.voice.tts_engine import TTSEngine


class NetherIXApp(QObject):
    """Main application controller."""

    _reply_ready = Signal(str)

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        self._config = config
        self._root_dir = Path(__file__).resolve().parent.parent

        self._setup_logging()
        self._setup_pet()
        self._setup_brain()
        self._setup_skills()
        self._setup_ui()
        self._setup_voice()
        self._setup_hotkey()
        self._connect_signals()

        logger.info("NetherIX initialized")

    def _setup_logging(self):
        log_cfg = self._config.get("logging", {})
        log_file = log_cfg.get("file", "logs/netherix.log")
        log_level = log_cfg.get("level", "INFO")
        log_path = self._root_dir / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(str(log_path), level=log_level, rotation="5 MB", retention="7 days")

    def _setup_pet(self):
        pet_cfg = self._config.get("pet", {})
        assets_dir = str(self._root_dir / "assets")
        self._pet = PetWidget(
            assets_dir=assets_dir,
            size=pet_cfg.get("size", 128),
            fps=pet_cfg.get("fps", 10),
            walk_speed=pet_cfg.get("walk_speed", 2),
            idle_timeout=pet_cfg.get("idle_timeout", 30),
            sleep_timeout=pet_cfg.get("sleep_timeout", 300),
            auto_walk=pet_cfg.get("auto_walk", True),
            gravity=pet_cfg.get("gravity", True),
        )

    def _setup_brain(self):
        ai_cfg = self._config.get("ai", {})
        api_key = ai_cfg.get("api_key", "")
        if not api_key:
            logger.warning("No API key configured, AI features disabled")

        self._llm = LLMClient(
            api_key=api_key,
            base_url=ai_cfg.get("base_url", "https://api.openai.com/v1"),
            model=ai_cfg.get("model", "qwen-plus"),
            temperature=ai_cfg.get("temperature", 0.7),
            max_tokens=ai_cfg.get("max_tokens", 2048),
            system_prompt=ai_cfg.get("system_prompt", ""),
        )
        self._intent_parser = IntentParser(self._llm)
        self._planner = TaskPlanner(self._llm)
        self._memory = ConversationMemory()

    def _setup_skills(self):
        self._skill_manager = SkillManager()
        skills_cfg = self._config.get("skills", {})
        self._skill_manager.load_builtin(skills_cfg.get("enabled_builtin"))

        TranslatorSkill.set_llm(self._llm)

        custom_dir = skills_cfg.get("custom_dir", "skills")
        self._skill_manager.load_custom_dir(str(self._root_dir / custom_dir))

    def _setup_ui(self):
        self._bubble = ChatBubble(
            duration=self._config.get("ui", {}).get("bubble_duration", 5) * 1000,
        )
        self._input_box = FloatingInputBox()
        self._tray = TrayManager()

    def _setup_voice(self):
        voice_cfg = self._config.get("voice", {})
        self._tts = TTSEngine(
            voice=voice_cfg.get("tts_voice"),
            enabled=voice_cfg.get("tts_enabled", False),
        )

    def _setup_hotkey(self):
        hotkey_str = self._config.get("ui", {}).get("hotkey", "ctrl+space")
        try:
            import keyboard
            keyboard.add_hotkey(hotkey_str, self._on_hotkey_pressed)
            logger.info("Hotkey registered: {}", hotkey_str)
        except Exception as e:
            logger.warning("Failed to register hotkey: {}", e)

    def _on_hotkey_pressed(self):
        QTimer.singleShot(0, self._input_box.toggle)

    def _connect_signals(self):
        self._pet.double_clicked.connect(self._input_box.toggle)
        self._input_box.message_submitted.connect(self._handle_user_message)
        self._tray.show_input_requested.connect(self._input_box.toggle)
        self._tray.settings_requested.connect(self._show_settings)
        self._tray.quit_requested.connect(self._quit)
        self._reply_ready.connect(self._show_reply)

        ReminderSkill.set_notify_callback(
            lambda msg: self._reply_ready.emit(msg)
        )

    def start(self):
        self._pet.show()
        self._tray.show()
        self._show_reply("冥九灵已苏醒... 随时为你效劳 ✨")
        logger.info("NetherIX started")

    @Slot(str)
    def _handle_user_message(self, text: str):
        logger.info("User: {}", text)
        self._pet.set_pet_state(PetState.TALK)
        self._show_reply("让我想想...")
        self._memory.add("user", text)

        thread = threading.Thread(target=self._process_message, args=(text,), daemon=True)
        thread.start()

    def _process_message(self, text: str):
        try:
            intent_result = self._intent_parser.parse(text)
            intent = intent_result["intent"]
            params = intent_result["params"]
            logger.info("Intent: {} params: {}", intent.value, params)

            if intent == Intent.CHAT:
                self._handle_chat(text)
                return

            plan = self._planner.plan(text, intent, params)
            self._execute_plan(plan)
        except Exception as e:
            logger.error("Processing failed: {}", e)
            self._reply_ready.emit(f"处理出了点问题: {e}")

    def _handle_chat(self, text: str):
        messages = self._memory.get_messages()
        tools = self._skill_manager.get_tools_schema()

        result = self._llm.chat(messages, tools=tools if tools else None)

        if result.get("tool_calls"):
            for tc in result["tool_calls"]:
                fn = tc["function"]
                try:
                    params = json.loads(fn["arguments"])
                except json.JSONDecodeError:
                    params = {}
                skill_result = self._skill_manager.execute_sync(fn["name"], params)
                self._memory.add_tool_result(tc["id"], fn["name"], skill_result.message)

            follow_up = self._llm.chat(self._memory.get_messages())
            reply = follow_up.get("content", "完成了！")
        else:
            reply = result.get("content", "...")

        self._memory.add("assistant", reply)
        self._reply_ready.emit(reply)

    def _execute_plan(self, plan: ExecutionPlan):
        results = []
        for step in plan.steps:
            if step.step_type == StepType.AUTOMATION:
                r = self._execute_automation(step.action, step.params)
                results.append(r)
            elif step.step_type == StepType.SKILL:
                r = self._skill_manager.execute_sync(step.action, step.params)
                results.append(r.message)
            elif step.step_type == StepType.REPLY:
                self._handle_chat(step.params.get("input", plan.original_input))
                return

        summary = "\n".join(str(r) for r in results if r)
        if summary:
            self._memory.add("assistant", summary)
            self._reply_ready.emit(summary)

    def _execute_automation(self, action: str, params: dict) -> str:
        handlers = {
            "open_app": lambda p: (
                AppLauncher.open_app(p.get("name", "")),
                f"已打开: {p.get('name', '')}",
            ),
            "click": lambda p: (
                MouseKeyboardController.click(p.get("x", 0), p.get("y", 0)),
                "已点击",
            ),
            "type_text": lambda p: (
                MouseKeyboardController.type_text(p.get("text", "")),
                "已输入文本",
            ),
            "hotkey": lambda p: (
                MouseKeyboardController.hotkey(*p.get("keys", [])),
                f"已按下: {'+'.join(p.get('keys', []))}",
            ),
            "volume": lambda p: SystemController.set_volume(p.get("level", 50)).get("success", False) and "音量已调整" or "音量调整失败",
            "volume_up": lambda p: (SystemController.volume_up(p.get("steps", 2)), "音量已增大"),
            "volume_down": lambda p: (SystemController.volume_down(p.get("steps", 2)), "音量已减小"),
            "screenshot": lambda p: f"截图已保存: {SystemController.take_screenshot(p.get('path')).get('path', '')}",
            "file_create": lambda p: FileOperator.create_file(p.get("path", ""), p.get("content", "")).get("path", "创建失败"),
            "file_delete": lambda p: "已删除" if FileOperator.delete(p.get("path", "")).get("success") else "删除失败",
            "file_move": lambda p: "已移动" if FileOperator.move(p.get("src", ""), p.get("dst", "")).get("success") else "移动失败",
            "file_search": lambda p: str(FileOperator.search(p.get("directory", "."), p.get("pattern", "*"))),
            "file_list": lambda p: str(FileOperator.list_dir(p.get("directory", "."))),
            "focus_window": lambda p: "已聚焦" if AppLauncher.focus_window(p.get("title", "")) else "未找到窗口",
            "close_window": lambda p: "已关闭" if AppLauncher.close_window(p.get("title", "")) else "未找到窗口",
            "lock_screen": lambda p: SystemController.lock_screen(),
            "open_url": lambda p: SystemController.open_url(p.get("url", "")),
        }

        handler = handlers.get(action)
        if handler:
            try:
                result = handler(params)
                if isinstance(result, tuple):
                    return str(result[-1])
                return str(result)
            except Exception as e:
                logger.error("Automation {} failed: {}", action, e)
                return f"操作失败: {e}"
        return f"未知操作: {action}"

    @Slot(str)
    def _show_reply(self, text: str):
        logger.info("NIX: {}", text)
        pet_pos = self._pet.pos()
        anchor = QPoint(
            pet_pos.x() + self._pet.width() // 2,
            pet_pos.y(),
        )
        self._bubble.show_message(text, anchor)
        self._pet.release_pet_state()
        if self._tts.enabled:
            self._tts.speak(text)

    def _show_settings(self):
        dialog = SettingsDialog(self._config)
        dialog.settings_saved.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, updated: dict):
        for section, values in updated.items():
            if section in self._config:
                self._config[section].update(values)
            else:
                self._config[section] = values

        config_path = self._root_dir / "config.yaml"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            logger.info("Settings saved to config.yaml")
            self._show_reply("设置已保存，部分更改需要重启生效")
        except Exception as e:
            logger.error("Failed to save config: {}", e)

    def _quit(self):
        logger.info("NetherIX shutting down")
        self._bubble.hide()
        self._pet.hide()
        self._tray.hide()
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
