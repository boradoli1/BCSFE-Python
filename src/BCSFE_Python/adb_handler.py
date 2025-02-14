"""Handle adb commands"""

import enum
import os
import subprocess
from typing import Union
from . import helper, user_input_handler


class ADBExceptionTypes(enum.Enum):
    """ADB exception types"""

    NO_DEVICE = enum.auto()
    DEVICE_OFFLINE = enum.auto()
    PATH_NOT_FOUND = enum.auto()
    ADB_NOT_INSTALLED = enum.auto()
    MORE_THAN_ONE_DEVICE = enum.auto()
    UNKNOWN = enum.auto()


class ADBException(Exception):
    """ADB exception"""

    def __init__(self, exception_type: ADBExceptionTypes, message: str = ""):
        """Initialize exception."""

        super().__init__(message)
        self.message = message
        self.exception_type = exception_type


def adb_pull(package_name: str, device_file_path: str, local_file_path: str):
    """Pull a file from a device"""
    if local_file_path:
        local_file_path = f'"{local_file_path}"'
    path = f"/data/data/{package_name}/{device_file_path}"
    run_adb_command(f'pull "{path}" {local_file_path}')


def adb_push(package_name: str, local_file_path: str, device_file_path: str):
    """Push a file to a device"""

    path = f"/data/data/{package_name}/{device_file_path}"
    run_adb_command(f'push "{local_file_path}" "{path}"')


def adb_delete_file(package_name: str, device_file_path: str, options: str = ""):
    """Delete a file on a device"""

    path = f"/data/data/{package_name}/{device_file_path}"
    run_adb_command(f'shell "su 0 rm "{path}" {options}"')


def adb_close_process(package_name: str):
    """Close a process"""

    run_adb_command(f"shell am force-stop {package_name}")


def adb_run_process(package_name: str):
    """Run a process"""

    run_adb_command(f"shell monkey -p {package_name} -v 1")

def adb_reboot():
    """Reboot adb server"""

    adb_kill_server()
    is_adb_installed()

def adb_root():
    """Start adb server as root"""

    subprocess.run("adb root", shell=True, check=True, text=True, capture_output=True)


def is_adb_installed():
    """Test if adb is installed"""

    try:
        subprocess.run(
            "adb start-server",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def run_adb_command(command: str) -> bool:
    """Run an ADB command"""

    command = f"adb {command}"
    if not is_adb_installed():
        raise ADBException(ADBExceptionTypes.ADB_NOT_INSTALLED)
    try:
        adb_root()
        subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as err:
        adb_error_handler(err)
    return True


def adb_kill_server():
    """Kill ADB server"""

    try:
        subprocess.run("adb kill-server", shell=True, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as err:
        adb_error_handler(err)


def adb_error_handler(err: subprocess.CalledProcessError):
    """Handle ADB errors"""

    if "not found" in err.stderr:
        raise ADBException(ADBExceptionTypes.NO_DEVICE)
    if "offline" in err.stderr:
        print(err.stderr)
        raise ADBException(ADBExceptionTypes.DEVICE_OFFLINE)
    if "does not exist" in err.stderr:
        raise ADBException(ADBExceptionTypes.PATH_NOT_FOUND)
    if "'adb' is not recognized" in err.stderr:
        raise ADBException(ADBExceptionTypes.ADB_NOT_INSTALLED)
    if "more than one device" in err.stderr:
        raise ADBException(ADBExceptionTypes.MORE_THAN_ONE_DEVICE)
    raise ADBException(ADBExceptionTypes.UNKNOWN, err.stderr)


def find_adb_path() -> Union[str, None]:
    """Find adb path automatically in common locations"""

    drive_letters = ["C", "D", "E"]
    paths = [
        "LDPlayer\\LDPlayer4.0",
        "LDPlayer\\LDPlayer9",
        "Program Files (x86)\\Nox\\bin",
        "adb",
    ]
    for drive_letter in drive_letters:
        for path in paths:
            path = f"{drive_letter}:\\{path}"
            if os.path.exists(path):
                return path

    return None

def if_windows() -> bool:
    """Check if windows"""

    return os.name == "nt"

def add_to_path() -> None:
    """Try to add adb to path environment variable automatically"""

    if not if_windows():
        helper.colored_text(
            "ADB path not added to PATH environment variable.\n"
            "Please add it manually to your system PATH variable.",
            helper.RED,
        )
        return

    adb_path = find_adb_path()
    if not adb_path:
        adb_path = input(
            "Please enter the path to the folder than contains adb: download link here: https://dl.google.com/android/repository/platform-tools-latest-windows.zip:"
        )
        if os.path.isfile(adb_path):
            adb_path = os.path.dirname(adb_path)

    print(f"Adding {adb_path} to your path environment variable")
    subprocess.run(f"set PATH={adb_path};%PATH%", shell=True, check=True)
    subprocess.run(f"setx PATH {adb_path};%PATH%", shell=True, check=True)
    print("Successfully added adb to path")


def adb_err_handler(err: ADBException):
    """Handle ADB errors"""
    if err.exception_type in (
        ADBExceptionTypes.NO_DEVICE,
        ADBExceptionTypes.DEVICE_OFFLINE,
    ):
        helper.colored_text(
            "Error: No device with an adb connection can be found, please connect one and try again. (You may have to wait aprox 1min for the device to be detected)",
            base=helper.RED,
        )
        adb_reboot()
    elif err.exception_type == ADBExceptionTypes.PATH_NOT_FOUND:
        helper.colored_text(
            "Error: You don't seem to have this game version installed on this device / no root access / SAVE_DATA couldn't be located, please make sure you have loaded into the game and clicked \"START\" and try again.",
            base=helper.RED,
        )
    elif err.exception_type == ADBExceptionTypes.ADB_NOT_INSTALLED:
        add_adb = (
            user_input_handler.colored_input(
                "Error, adb is not in your Path environment variable. There is a tutorial in the github's readme. Would you like to try to add adb to your path now?(&y&/&n&):"
            )
            == "y"
        )
        if add_adb:
            add_to_path()
            print("Please re-run the editor to try again")
    elif err.exception_type == ADBExceptionTypes.MORE_THAN_ONE_DEVICE:
        helper.colored_text(
            "Error: More than one device with an adb connection can be found, please make sure that only 1 device is connected. (You may have to wait aprox 1min for the device to be detected)",
            base=helper.RED,
        )
        adb_reboot()
    else:
        helper.colored_text(
            "Error: " + str(err.message),
            base=helper.RED,
        )
    helper.exit_editor()


def adb_pull_save_data(game_version: str) -> str:
    """Pull save data from device"""
    helper.colored_text(
        "Pulling save data from device...",
        base=helper.DARK_YELLOW,
    )
    try:
        adb_pull(
            get_package_name(game_version),
            "files/SAVE_DATA",
            helper.get_default_save_name(),
        )
    except ADBException as err:
        adb_err_handler(err)
    return helper.get_default_save_name()


def adb_push_save_data(game_version: str, path: str) -> None:
    """Push save data to device"""
    helper.colored_text(
        "Pushing save data to device...",
        base=helper.DARK_YELLOW,
    )
    try:
        adb_push(get_package_name(game_version), path, "files/SAVE_DATA")
    except ADBException as err:
        adb_err_handler(err)


def rerun_game(game_version: str) -> None:
    """Rerun game"""

    helper.colored_text(
        "Rerunning game...",
        base=helper.DARK_YELLOW,
    )
    try:
        adb_close_process(get_package_name(game_version))
        adb_run_process(get_package_name(game_version))
    except ADBException as err:
        adb_err_handler(err)


def adb_clear_save_data(game_version: str) -> None:
    """Clear save data"""

    try:
        adb_delete_file(get_package_name(game_version), "/files/*SAVE_DATA*")
        adb_delete_file(get_package_name(game_version), "/shared_prefs", "-r -f")
    except ADBException as err:
        adb_err_handler(err)


def get_package_name(game_version: str) -> str:
    """Get package name"""

    if game_version == "jp":
        game_version = ""
    return f"jp.co.ponos.battlecats{game_version}"
