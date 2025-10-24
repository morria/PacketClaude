"""
Configuration management for PacketClaude
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv
from io import StringIO

class Config:
    """Configuration manager for PacketClaude"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration

        Args:
            config_path: Path to config.yaml file. If None, uses default location.
        """

        with open('.env', 'r') as f:
            env_content = f.read()
        load_dotenv(stream=StringIO(env_content))

        # Load environment variables
        load_dotenv()

        # Determine config file path
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config/config.yaml")

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please copy config/config.yaml.example to config/config.yaml"
            )

        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default=None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key: Configuration key (e.g., 'station.callsign')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def station_callsign(self) -> str:
        """Get station callsign"""
        return self.get('station.callsign', 'N0CALL-10')

    @property
    def station_description(self) -> str:
        """Get station description"""
        return self.get('station.description', 'PacketClaude AI Gateway')

    @property
    def welcome_message(self) -> str:
        """Get welcome message"""
        return self.get('station.welcome_message', 'Welcome to PacketClaude!')

    @property
    def direwolf_host(self) -> str:
        """Get Direwolf host"""
        return self.get('direwolf.host', 'localhost')

    @property
    def direwolf_port(self) -> int:
        """Get Direwolf port"""
        return self.get('direwolf.port', 8001)

    @property
    def direwolf_timeout(self) -> int:
        """Get Direwolf connection timeout"""
        return self.get('direwolf.timeout', 30)

    @property
    def telnet_enabled(self) -> bool:
        """Check if telnet server is enabled"""
        return self.get('telnet.enabled', False)

    @property
    def telnet_host(self) -> str:
        """Get telnet server host"""
        return self.get('telnet.host', 'localhost')

    @property
    def telnet_port(self) -> int:
        """Get telnet server port"""
        return self.get('telnet.port', 8023)

    @property
    def radio_enabled(self) -> bool:
        """Check if radio control is enabled"""
        return self.get('radio.enabled', True)

    @property
    def radio_model(self) -> str:
        """Get radio model"""
        return self.get('radio.model', 'FTX-1')

    @property
    def radio_device(self) -> str:
        """Get radio device path"""
        return self.get('radio.device', '/dev/ttyUSB0')

    @property
    def radio_baud(self) -> int:
        """Get radio baud rate"""
        return self.get('radio.baud', 4800)

    @property
    def claude_model(self) -> str:
        """Get Claude model name"""
        return self.get('claude.model', 'claude-3-5-sonnet-20241022')

    @property
    def claude_max_tokens(self) -> int:
        """Get Claude max tokens"""
        return self.get('claude.max_tokens', 500)

    @property
    def claude_temperature(self) -> float:
        """Get Claude temperature"""
        return self.get('claude.temperature', 0.7)

    @property
    def claude_system_prompt(self) -> str:
        """Get Claude system prompt"""
        default_prompt = (
            "You are Claude, an AI assistant accessible via amateur radio packet radio. "
            "Keep responses concise and clear as they will be transmitted over radio."
        )
        return self.get('claude.system_prompt', default_prompt)

    @property
    def search_enabled(self) -> bool:
        """Check if web search is enabled"""
        return self.get('search.enabled', False)

    @property
    def search_max_results(self) -> int:
        """Get maximum search results"""
        return self.get('search.max_results', 5)

    @property
    def pota_enabled(self) -> bool:
        """Check if POTA spots tool is enabled"""
        return self.get('pota.enabled', False)

    @property
    def pota_max_spots(self) -> int:
        """Get maximum POTA spots to return"""
        return self.get('pota.max_spots', 10)

    @property
    def band_conditions_enabled(self) -> bool:
        """Check if band conditions tool is enabled"""
        return self.get('band_conditions.enabled', True)

    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment"""
        key = os.getenv('ANTHROPIC_API_KEY')
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Please set it in .env file."
            )
        return key

    @property
    def qrz_api_key(self) -> str:
        """Get QRZ.com API key from environment"""
        return os.getenv('QRZ_API_KEY', '')

    @property
    def qrz_username(self) -> str:
        """Get QRZ.com username from environment"""
        return os.getenv('QRZ_USERNAME', '')

    @property
    def qrz_password(self) -> str:
        """Get QRZ.com password from environment"""
        return os.getenv('QRZ_PASSWORD', '')

    @property
    def qrz_enabled(self) -> bool:
        """Check if QRZ lookup is enabled (has API key or credentials)"""
        return bool(self.qrz_api_key or (self.qrz_username and self.qrz_password))

    @property
    def rate_limit_enabled(self) -> bool:
        """Check if rate limiting is enabled"""
        return self.get('rate_limits.enabled', True)

    @property
    def rate_limit_per_hour(self) -> int:
        """Get queries per hour limit"""
        return self.get('rate_limits.queries_per_hour', 10)

    @property
    def rate_limit_per_day(self) -> int:
        """Get queries per day limit"""
        return self.get('rate_limits.queries_per_day', 50)

    @property
    def max_response_chars(self) -> int:
        """Get maximum response characters"""
        return self.get('rate_limits.max_response_chars', 1024)

    @property
    def log_dir(self) -> Path:
        """Get log directory path"""
        log_dir = Path(self.get('logging.log_dir', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @property
    def log_format(self) -> str:
        """Get log format"""
        return self.get('logging.format', 'json')

    @property
    def log_level(self) -> str:
        """Get log level"""
        # Check environment variable first, then config, then default
        import os
        env_level = os.getenv('LOG_LEVEL')
        if env_level:
            return env_level.upper()
        return self.get('logging.level', 'INFO').upper()

    @property
    def database_path(self) -> Path:
        """Get database path"""
        db_path = Path(self.get('database.path', 'data/sessions.db'))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path

    @property
    def session_timeout(self) -> int:
        """Get session timeout in seconds"""
        return self.get('sessions.timeout', 0)

    @property
    def max_context_messages(self) -> int:
        """Get maximum context messages per session"""
        return self.get('sessions.max_context_messages', 20)

    def reload(self):
        """Reload configuration from file"""
        self._load_config()
