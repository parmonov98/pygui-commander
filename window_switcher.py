#!/usr/bin/env python3
import subprocess
import sys

def list_windows():
    """List all visible windows"""
    try:
        # Run wmctrl -l to get list of windows
        result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
        if result.stdout:
            windows = result.stdout.strip().split('\n')
            print("\nAvailable windows:")
            for i, window in enumerate(windows):
                # Split window info and get the title (everything after the third column)
                parts = window.split(None, 3)
                if len(parts) >= 4:
                    window_id, desktop, host, title = parts
                    print(f"{i}: {title}")
            return windows
        else:
            print("No windows found")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Error listing windows: {e}")
        return []

def switch_to_window(window_title):
    """Switch to a specific window by title"""
    try:
        # Use wmctrl to activate the window
        subprocess.run(['wmctrl', '-a', window_title], check=True)
        print(f"Switched to window: {window_title}")
    except subprocess.CalledProcessError as e:
        print(f"Error switching to window: {e}")

# Just list all windows immediately when script runs
print("Current Windows:")
windows = list_windows()

# If we have windows, allow switching
if windows:
    print("\nWould you like to switch to a specific window?")
    print("Enter the window number or part of the title (or press Enter to exit):")
    try:
        choice = input("> ")
        if choice.strip():
            # Try to use as index first
            try:
                index = int(choice)
                if 0 <= index < len(windows):
                    parts = windows[index].split(None, 3)
                    if len(parts) >= 4:
                        switch_to_window(parts[3])
            except ValueError:
                # If not a number, use as window title
                switch_to_window(choice)
    except (EOFError, KeyboardInterrupt):
        pass
