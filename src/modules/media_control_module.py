import platform
import subprocess
from typing import Optional, Dict


def set_volume(value: int = 10, direction: Optional[str] = None) -> str:
    """
    Controls the system's master volume.

    - If `direction` is None (default), sets the volume to `value`.
    - If `direction` is "up", increases the volume by `value` percent.
    - If `direction` is "down", decreases the volume by `value` percent.

    Args:
        value (int): The percentage for setting or adjusting the volume. Defaults to 10.
        direction (Optional[str]): "up", "down", or None. Defaults to None.
    """
    os_type = platform.system()
    value = max(0, min(100, value)) # Clamp value between 0 and 100

    try:
        if os_type == "Windows":
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume.QueryInterface(IAudioEndpointVolume)

            if direction is None:
                # Set volume to a specific value (0-100)
                volume.SetMasterVolumeLevelScalar(value / 100.0, None)
                return f"Volume set to {value}%."

            # Adjust volume by a step
            step = value / 100.0  # Convert percentage step to scalar
            current_scalar = volume.GetMasterVolumeLevelScalar()

            if direction == "up":
                new_scalar = min(1.0, current_scalar + step)
                volume.SetMasterVolumeLevelScalar(new_scalar, None)
                return f"Volume increased to {int(new_scalar * 100)}%."
            elif direction == "down":
                new_scalar = max(0.0, current_scalar - step)
                volume.SetMasterVolumeLevelScalar(new_scalar, None)
                return f"Volume decreased to {int(new_scalar * 100)}%."

        elif os_type == "Linux":
            if direction is None:
                subprocess.run(["amixer", "sset", "Master", f"{value}%"], check=True)
                return f"Volume set to {value}%."
            elif direction == "up":
                subprocess.run(["amixer", "sset", "Master", f"{value}%+"], check=True)
                return f"Volume increased by {value}%."
            elif direction == "down":
                subprocess.run(["amixer", "sset", "Master", f"{value}%-"], check=True)
                return f"Volume decreased by {value}%."

        elif os_type == "Darwin":  # macOS
            if direction is None:
                subprocess.run(["osascript", "-e", f"set volume output volume {value}"], check=True)
                return f"Volume set to {value}%."
            
            # AppleScript for relative change is a bit more verbose
            current_vol_cmd = 'output volume of (get volume settings)'
            current_vol = int(subprocess.check_output(["osascript", "-e", current_vol_cmd]).strip())
            
            if direction == "up":
                new_vol = min(100, current_vol + value)
                subprocess.run(["osascript", "-e", f"set volume output volume {new_vol}"], check=True)
                return f"Volume increased to {new_vol}%."
            elif direction == "down":
                new_vol = max(0, current_vol - value)
                subprocess.run(["osascript", "-e", f"set volume output volume {new_vol}"], check=True)
                return f"Volume decreased to {new_vol}%."

        return "Unsupported operating system."

    except ImportError:
        return "Windows volume control failed: 'pycaw' not found. Please run 'pip install pycaw'."
    except FileNotFoundError:
        return f"{os_type} volume control failed: command-line tool not found. (Linux requires 'amixer')"
    except Exception as e:
        return f"Failed to control volume on {os_type}: {e}"


def _send_media_key(key: str) -> str:
    """Internal helper to send a media key command to the OS."""
    os_type = platform.system()
    try:
        if os_type == "Windows":
            import pyautogui
            pyautogui.press(key)
        elif os_type == "Linux":
            # Uses playerctl, a command-line controller for MPRIS-compatible media players
            subprocess.run(["playerctl", key.replace("track", "")], check=True)
        elif os_type == "Darwin":  # macOS
            # Simulates media key presses using AppleScript
            key_map = {
                "playpause": 'key code 100 using {control down, command down}', # This is a workaround for some keyboards
                "stop": 'key code 102 using {control down, command down}', # F11
                "nexttrack": 'key code 101 using {control down, command down}', # F9
                "prevtrack": 'key code 98 using {control down, command down}', # F7
            }
            # A more direct approach that works for most apps like Music and Spotify
            app_map = {
                "playpause": 'tell application "System Events" to tell (process 1 where frontmost is true) to keystroke " " using command down',
                "nexttrack": 'tell application "System Events" to key code 124 using command down',
                "prevtrack": 'tell application "System Events" to key code 123 using command down',
            }
            if key in app_map:
                 subprocess.run(["osascript", "-e", app_map[key]], check=True)
            else:
                 return f"Action '{key}' not supported on macOS."

        else:
            return "Unsupported operating system."
        return f"Media command '{key}' sent."
    except ImportError:
        return "Windows media control failed: 'pyautogui' not found. Please run 'pip install pyautogui'."
    except FileNotFoundError:
        return f"{os_type} media control failed: command-line tool not found. (Linux requires 'playerctl')"
    except Exception as e:
        return f"Failed to send media key '{key}' on {os_type}: {e}"


def media_play_pause() -> str:
    """
    Toggles Play/Pause on the system's active media player.
    """
    return _send_media_key("playpause")


def media_stop() -> str:
    """
    Stops playback on the system's active media player.
    Note: On Windows and macOS, this may act as play/pause.
    """
    return _send_media_key("stop")


def media_next() -> str:
    """
    Skips to the next track on the system's active media player.
    """
    return _send_media_key("nexttrack")


def media_previous() -> str:
    """
    Goes to the previous track on the system's active media player.
    """
    return _send_media_key("prevtrack")


def play_song(song_name: str) -> str:
    """
    Searches for and plays a song on YouTube.

    Args:
        song_name (str): The name of the song to play.

    Returns:
        A confirmation or error string.
    """
    try:
        import pywhatkit
        pywhatkit.playonyt(song_name)
        return f"Playing {song_name} on YouTube."
    except ImportError:
        return "Could not play song: 'pywhatkit' library not found. Please run 'pip install pywhatkit'."
    except Exception as e:
        return f"Sorry, I could not play the song. An error occurred: {e}"

# Testing
if __name__ == "__main__":
    print("Setting volume to 50%...")
    print(set_volume(value=50))

    print("\nIncreasing volume by 10%...")
    print(set_volume(value=90, direction="up"))

    print("\nDecreasing volume by 10%...")
    print(set_volume(value=40, direction="down"))

    print("\nPlaying a song on YouTube...")
    print(play_song("Never Gonna Give You Up"))