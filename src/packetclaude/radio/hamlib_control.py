"""
Hamlib radio control for PTT and radio status
Gracefully handles when Hamlib is not available
"""
import logging
from typing import Optional


logger = logging.getLogger(__name__)


# Try to import Hamlib, but don't fail if not available
try:
    import Hamlib
    HAMLIB_AVAILABLE = True
    logger.info("Hamlib is available")
except ImportError:
    HAMLIB_AVAILABLE = False
    logger.warning("Hamlib not available - radio control disabled")


class RadioControl:
    """
    Radio control interface using Hamlib
    Provides PTT control and radio status monitoring
    """

    def __init__(self, model: str = "FTX-1",
                 device: str = "/dev/ttyUSB0",
                 baud: int = 4800,
                 enabled: bool = True):
        """
        Initialize radio control

        Args:
            model: Radio model name or number
            device: Serial device path
            baud: Baud rate
            enabled: Enable radio control
        """
        self.model = model
        self.device = device
        self.baud = baud
        self.enabled = enabled and HAMLIB_AVAILABLE
        self.rig = None
        self.connected = False

        if not HAMLIB_AVAILABLE and enabled:
            logger.warning(
                "Radio control requested but Hamlib not available. "
                "Install Hamlib Python bindings to enable radio control."
            )

    def connect(self) -> bool:
        """
        Connect to radio

        Returns:
            True if successful or if radio control is disabled
        """
        if not self.enabled:
            logger.info("Radio control disabled")
            return True

        if not HAMLIB_AVAILABLE:
            logger.warning("Cannot connect: Hamlib not available")
            return False

        try:
            # Map model name to Hamlib model number
            model_num = self._get_model_number()

            # Initialize rig
            Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
            self.rig = Hamlib.Rig(model_num)

            # Set parameters
            self.rig.state.rigport.pathname = self.device
            self.rig.state.rigport.parm.serial.rate = self.baud

            # Open connection
            self.rig.open()
            self.connected = True

            logger.info(f"Connected to {self.model} on {self.device}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to radio: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from radio"""
        if self.rig and self.connected:
            try:
                self.rig.close()
                logger.info("Disconnected from radio")
            except Exception as e:
                logger.error(f"Error disconnecting from radio: {e}")
            finally:
                self.rig = None
                self.connected = False

    def set_ptt(self, state: bool) -> bool:
        """
        Set PTT (Push-to-Talk) state

        Args:
            state: True for transmit, False for receive

        Returns:
            True if successful
        """
        if not self.enabled:
            return True

        if not self.connected or not self.rig:
            logger.warning("Cannot set PTT: not connected to radio")
            return False

        try:
            ptt_value = Hamlib.RIG_PTT_ON if state else Hamlib.RIG_PTT_OFF
            self.rig.set_ptt(Hamlib.RIG_VFO_CURR, ptt_value)
            logger.debug(f"PTT {'ON' if state else 'OFF'}")
            return True
        except Exception as e:
            logger.error(f"Failed to set PTT: {e}")
            return False

    def get_ptt(self) -> Optional[bool]:
        """
        Get current PTT state

        Returns:
            True if transmitting, False if receiving, None if error
        """
        if not self.enabled:
            return False

        if not self.connected or not self.rig:
            return None

        try:
            ptt = self.rig.get_ptt(Hamlib.RIG_VFO_CURR)
            return ptt == Hamlib.RIG_PTT_ON
        except Exception as e:
            logger.error(f"Failed to get PTT: {e}")
            return None

    def get_frequency(self) -> Optional[float]:
        """
        Get current frequency in Hz

        Returns:
            Frequency in Hz or None if error
        """
        if not self.enabled or not self.connected or not self.rig:
            return None

        try:
            freq = self.rig.get_freq(Hamlib.RIG_VFO_CURR)
            return freq
        except Exception as e:
            logger.error(f"Failed to get frequency: {e}")
            return None

    def set_frequency(self, freq_hz: float) -> bool:
        """
        Set frequency

        Args:
            freq_hz: Frequency in Hz

        Returns:
            True if successful
        """
        if not self.enabled or not self.connected or not self.rig:
            return False

        try:
            self.rig.set_freq(Hamlib.RIG_VFO_CURR, freq_hz)
            logger.info(f"Set frequency to {freq_hz} Hz")
            return True
        except Exception as e:
            logger.error(f"Failed to set frequency: {e}")
            return False

    def get_signal_strength(self) -> Optional[int]:
        """
        Get signal strength (S-meter reading)

        Returns:
            Signal strength in dB or None if error
        """
        if not self.enabled or not self.connected or not self.rig:
            return None

        try:
            level = self.rig.get_level_i(Hamlib.RIG_LEVEL_STRENGTH)
            return level
        except Exception as e:
            logger.error(f"Failed to get signal strength: {e}")
            return None

    def get_info(self) -> Optional[str]:
        """
        Get radio information

        Returns:
            Radio info string or None if error
        """
        if not self.enabled or not self.connected or not self.rig:
            return None

        try:
            info = self.rig.get_info()
            return info
        except Exception as e:
            logger.error(f"Failed to get radio info: {e}")
            return None

    def _get_model_number(self) -> int:
        """
        Get Hamlib model number from model name

        Returns:
            Hamlib model number
        """
        if not HAMLIB_AVAILABLE:
            return 0

        # Try to match model name
        model_upper = self.model.upper()

        # Check if it's already a number
        try:
            return int(self.model)
        except ValueError:
            pass

        # Try to find model by name
        # This is a simplified version - in reality, you'd need to
        # look up the exact model number from Hamlib's rig list
        model_map = {
            'FTX-1': 1044,  # Yaesu FTX-1 (example - verify actual number)
            'FT-817': 120,
            'FT-818': 1043,
            'IC-705': 3085,
            'IC-7300': 3073,
        }

        if model_upper in model_map:
            return model_map[model_upper]

        # Default to dummy rig for testing
        logger.warning(
            f"Unknown model '{self.model}', using dummy rig. "
            f"Check Hamlib documentation for correct model number."
        )
        return Hamlib.RIG_MODEL_DUMMY

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


class DummyRadioControl:
    """
    Dummy radio control for testing without hardware
    """

    def __init__(self, *args, **kwargs):
        self.enabled = False
        self.connected = True
        logger.info("Using dummy radio control")

    def connect(self) -> bool:
        return True

    def disconnect(self):
        pass

    def set_ptt(self, state: bool) -> bool:
        logger.debug(f"[DUMMY] PTT {'ON' if state else 'OFF'}")
        return True

    def get_ptt(self) -> bool:
        return False

    def get_frequency(self) -> Optional[float]:
        return 144390000.0  # 2m APRS frequency

    def set_frequency(self, freq_hz: float) -> bool:
        logger.debug(f"[DUMMY] Set frequency to {freq_hz} Hz")
        return True

    def get_signal_strength(self) -> Optional[int]:
        return -73  # S9 signal

    def get_info(self) -> str:
        return "Dummy Radio Control"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
