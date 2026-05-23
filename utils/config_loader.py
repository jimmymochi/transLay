import os
import json
from utils.logger import get_logger

DEFAULT_CONFIG = {
  "default_translator": "google",
  "google": {
    "timeout": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  },
  "openai": {
    "api_key": "",
    "model": "gpt-4o-mini",
    "temperature": 0.3
  },
  "deepl": {
    "api_key": ""
  },
  "layout": {
    "min_font_size": 8.0,
    "min_line_height": 1.05,
    "default_line_height": 1.25,
    "enable_dynamic_expansion": True,
    "enable_redaction": True
  },
  "fonts": {
    "windows_font": "msjh.ttc",
    "mac_font": "/System/Library/Fonts/PingFang.ttc",
    "fallback_font": "gkai00mp.ttf"
  }
}

def load_config(config_path="config.json"):
    """
    載入專案的設定檔，如果不存在則回覆預設值。
    """
    logger = get_logger()
    if not os.path.exists(config_path):
        logger.warning(f"設定檔 {config_path} 不存在，將使用預設組態設定。")
        return DEFAULT_CONFIG

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            
        # 深度合併預設值，以防缺少某些欄位
        config = DEFAULT_CONFIG.copy()
        for key, val in user_config.items():
            if isinstance(val, dict) and key in config:
                config[key].update(val)
            else:
                config[key] = val
        return config
    except Exception as e:
        logger.error(f"讀取設定檔時發生錯誤: {e}，將改用預設組態設定。")
        return DEFAULT_CONFIG
