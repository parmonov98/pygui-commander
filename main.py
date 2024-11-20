#!/usr/bin/env python3
import pyautogui
import subprocess
import time
import sys
from PIL import Image
import pytesseract
import os
import cv2
import numpy as np
import pyperclip
from dotenv import load_dotenv
from input_detection import InputDetector

# Load environment variables
load_dotenv()

# Safety pause between actions
pyautogui.PAUSE = 0.5
# Fail-safe: move mouse to upper-left corner to stop
pyautogui.FAILSAFE = True

class WindowController:
    def __init__(self):
        """Initialize window controller"""
        # Frontend project directory from .env
        self.project_dir = os.path.expanduser(os.getenv('PROJECT_PATH'))
        self.command = os.getenv('COMMAND')
        
        if not os.path.exists(self.project_dir):
            print(f"Warning: Project directory does not exist: {self.project_dir}")
            print("Please make sure the directory exists before running tests")
        
        # Directory for saving debug screenshots
        self.screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        print(f"Screenshots directory: {self.screenshots_dir}")
        
        # Window titles to look for
        self.windsurf_titles = ["Windsurf", "xatp13.frontend2", "Cascade", "VSCodium"]
        self.terminal_titles = ["Terminal", "ubuntu@"]
        self.browser_titles = ["Chrome", "Firefox"]
        
        # Window IDs
        self.windows = {
            'windsurf': None,
            'terminal': None,
            'browser': None
        }
        
        # Focus lock for window switching
        self.focus_lock = {
            'enabled': False,
            'window_id': None,
            'window_type': None,
            'last_check': 0
        }
        
        # Timing configurations
        self.window_switch_delay = 1.0
        self.action_delay = 0.3
        self.command_delay = 1.5
        self.focus_check_interval = 0.5  # How often to check focus
        
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = True  # Move mouse to upper-left corner to abort
        pyautogui.PAUSE = 0.1  # Add small delay between PyAutoGUI commands
        
        # Initialize input detector
        self.input_detector = InputDetector(debug=True)
        
        # Initialize window positions
        self.update_window_positions()
        
        self.debug = True

    def _normalize_window_id(self, window_id):
        """Normalize window ID to decimal format"""
        try:
            # Convert from hex (0x...) to decimal
            if isinstance(window_id, str) and window_id.startswith('0x'):
                return str(int(window_id, 16))
            return str(window_id)
        except Exception as e:
            print(f"Error normalizing window ID: {e}")
            return str(window_id)

    def check_terminal_health(self):
        """Check if terminal is healthy and responding"""
        self.update_window_positions()
        
        if 'terminal' in self.windows:
            try:
                # Try to activate terminal window to check if it's responsive
                result = subprocess.run(['wmctrl', '-i', '-a', self.windows['terminal']], 
                                     check=True, capture_output=True)
                return True
            except subprocess.CalledProcessError:
                print("Terminal window not responding")
                self.windows.pop('terminal', None)
        else:
            print("No terminal window found")
        return False

    def enable_focus_lock(self, window_type):
        """Enable focus lock for a specific window"""
        window_id = self.windows.get(window_type)
        if window_id:
            self.focus_lock = {
                'enabled': True,
                'window_id': window_id,
                'window_type': window_type,
                'last_check': time.time()
            }
            print(f"Focus lock enabled for {window_type} window")
            return True
        return False

    def disable_focus_lock(self):
        """Disable focus lock"""
        self.focus_lock = {
            'enabled': False,
            'window_id': None,
            'window_type': None,
            'last_check': 0
        }
        print("Focus lock disabled")

    def check_and_restore_focus(self):
        """Check if focus has been lost and restore it if necessary"""
        try:
            if not self.focus_lock['enabled']:
                return True
                
            # Only check periodically to avoid too frequent checks
            current_time = time.time()
            if current_time - self.focus_lock['last_check'] < self.focus_check_interval:
                return True
                
            self.focus_lock['last_check'] = current_time
            
            # Get current active window
            active_window = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True
            )
            
            if active_window.returncode == 0:
                active_id = self._normalize_window_id(active_window.stdout.strip())
                locked_id = self._normalize_window_id(self.focus_lock['window_id'])
                
                if active_id != locked_id:
                    print(f"Focus lost from {self.focus_lock['window_type']} window, restoring...")
                    return self.switch_to_window(self.focus_lock['window_type'])
                    
            return True
            
        except Exception as e:
            print(f"Error checking focus: {e}")
            return False

    def switch_to_window(self, window_type):
        """Switch to a specific window"""
        try:
            window_id = self.windows.get(window_type)
            if not window_id:
                print(f"No {window_type} window ID found")
                return False
                
            print(f"Switching to {window_type} window (ID: {window_id})")
            
            # First, make sure window is not minimized
            subprocess.run(['wmctrl', '-i', '-r', window_id, '-b', 'remove,hidden,shaded'])
            time.sleep(0.5)  # Wait for unminimize
            
            # Then activate it using both wmctrl and xdotool for better reliability
            subprocess.run(['wmctrl', '-i', '-a', window_id])
            normalized_id = self._normalize_window_id(window_id)
            subprocess.run(['xdotool', 'windowactivate', normalized_id])
            time.sleep(self.window_switch_delay)  # Use configured delay
            
            # Verify the switch was successful by checking active window
            active_window = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True
            )
            
            if active_window.returncode == 0:
                active_id = self._normalize_window_id(active_window.stdout.strip())
                if active_id == normalized_id:
                    print(f"Successfully switched to {window_type} window")
                    # Enable focus lock for windsurf windows
                    if window_type == 'windsurf':
                        self.enable_focus_lock(window_type)
                    return True
            
            # If verification failed, try one more time with xdotool
            print(f"First switch attempt failed, trying again...")
            subprocess.run(['xdotool', 'windowactivate', normalized_id])
            time.sleep(self.window_switch_delay)
            
            active_window = subprocess.run(
                ['xdotool', 'getactivewindow'],
                capture_output=True,
                text=True
            )
            
            if active_window.returncode == 0:
                active_id = self._normalize_window_id(active_window.stdout.strip())
                if active_id == normalized_id:
                    print(f"Successfully switched to {window_type} window on second attempt")
                    # Enable focus lock for windsurf windows
                    if window_type == 'windsurf':
                        self.enable_focus_lock(window_type)
                    return True
            
            print(f"Failed to switch to {window_type} window after retries")
            print(f"Expected window ID: {normalized_id}")
            print(f"Active window ID: {self._normalize_window_id(active_window.stdout.strip()) if active_window.returncode == 0 else 'unknown'}")
            return False
            
        except Exception as e:
            print(f"Error switching to {window_type} window: {e}")
            return False

    def update_window_positions(self):
        """Update stored window positions"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error getting window list")
                return
                
            # Reset all window IDs
            for window_type in self.windows:
                self.windows[window_type] = None
                
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id, desktop, host, title = parts
                    
                    # Check Windsurf windows
                    if any(wt.lower() in title.lower() for wt in self.windsurf_titles):
                        print(f"Found Windsurf window: {title}")
                        self.windows['windsurf'] = window_id
                    # Check Terminal windows
                    elif any(tt.lower() in title.lower() for tt in self.terminal_titles):
                        print(f"Found Terminal window: {title}")
                        self.windows['terminal'] = window_id
                    # Check Browser windows
                    elif any(bt.lower() in title.lower() for bt in self.browser_titles):
                        print(f"Found Browser window: {title}")
                        self.windows['browser'] = window_id
                        
            print(f"Updated window IDs: {self.windows}")
                        
        except Exception as e:
            print(f"Error updating window positions: {e}")

    def list_windsurf_windows(self):
        """List all Windsurf windows and let user choose one"""
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error getting window list")
                return False

            windsurf_windows = {}
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id, desktop, host, title = parts
                    # Include any window that has "Windsurf" in the title
                    if "Windsurf" in title:
                        normalized_id = self._normalize_window_id(window_id)
                        windsurf_windows[window_id] = {
                            'title': title,
                            'normalized_id': normalized_id
                        }
        
            if not windsurf_windows:
                print("No Windsurf windows found")
                return False
            
            print("\nAvailable Windsurf windows:")
            for i, (wid, info) in enumerate(windsurf_windows.items(), 1):
                print(f"{i}. {info['title']} (ID: {wid} -> {info['normalized_id']})")
            
            while True:
                try:
                    choice = input("\nChoose Windsurf window number (or 'q' to quit): ").strip()
                    if choice.lower() == 'q':
                        return False
                    if choice.lower() == 'r':
                        print("\nRefreshing window list...")
                        return self.list_windsurf_windows()
                    
                    idx = int(choice)
                    if 1 <= idx <= len(windsurf_windows):
                        chosen_id = list(windsurf_windows.keys())[idx-1]
                        chosen_info = windsurf_windows[chosen_id]
                        self.windows['windsurf'] = chosen_id
                        print(f"\nSelected: {chosen_info['title']}")
                        print(f"Window ID: {chosen_id} (normalized: {chosen_info['normalized_id']})")
                        
                        # Try switching to the window immediately to verify
                        if self.switch_to_window('windsurf'):
                            print("Successfully switched to window")
                            return True
                        else:
                            print("Failed to switch to selected window")
                            return False
                    else:
                        print("Invalid choice, try again or 'q' to quit, 'r' to refresh")
                except ValueError:
                    print("Please enter a number, 'q' to quit, or 'r' to refresh")
                
        except Exception as e:
            print(f"Error listing Windsurf windows: {e}")
            return False

    def select_windsurf_window(self):
        """Select a Windsurf window to control"""
        print("\nSelect a Windsurf window to control")
        print("'q' to quit, 'r' to refresh window list")
        return self.list_windsurf_windows()

    def find_cascade_input(self):
        """Find and click Cascade's input"""
        try:
            # Make sure we're switched to the Windsurf window
            if not self.switch_to_window('windsurf'):
                print("Could not switch to Windsurf window")
                return False
                
            # Add a delay to ensure window is active
            time.sleep(self.window_switch_delay)
            
            # Take screenshot
            screenshot = self.capture_window_screenshot(None)  # We don't need window_info anymore
            if screenshot is None:
                print("Failed to capture screenshot")
                return False
            
            # Find Cascade's input
            input_box = self.input_detector.find_input_box(screenshot)
            if not input_box:
                print("Could not find Cascade input")
                return False

            # Draw rectangle around detected input box for debugging
            debug_frame = screenshot.copy()
            cv2.rectangle(debug_frame, 
                         (input_box.x, input_box.y), 
                         (input_box.x + input_box.width, input_box.y + input_box.height), 
                         (0, 255, 0), 2)
            
            # Save debug image
            debug_path = self.save_debug_image(debug_frame, 'detected_input')
            print(f"Saved debug screenshot to: {debug_path}")
            
            # Click the input field
            x, y = input_box.click_position
            pyautogui.click(x, y)
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"Error finding Cascade input: {e}")
            return False

    def paste_to_cascade(self, text):
        """Paste text to Cascade's input"""
        try:
            # First switch to the Windsurf window
            if not self.switch_to_window('windsurf'):
                print("Could not switch to Windsurf window")
                return False

            time.sleep(self.window_switch_delay)  # Wait for window to be active
                
            if not self.find_cascade_input():
                print("Could not find input box")
                return False
            
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Paste using keyboard shortcut
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # Press enter
            pyautogui.press('enter')
            return True
            
        except Exception as e:
            print(f"Error pasting to Cascade: {e}")
            return False

    def get_active_window_info(self):
        """Get the active window's info"""
        try:
            # First get the window ID
            result = subprocess.run(['xdotool', 'search', '--name', 'windsurf'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error finding Windsurf window")
                return None
                
            window_ids = result.stdout.strip().split('\n')
            if not window_ids:
                print("No Windsurf window found")
                return None
                
            # Use the last window ID (most recently created)
            window_id = window_ids[-1]
            
            # Get window geometry
            result = subprocess.run(['xdotool', 'getwindowgeometry', window_id], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error getting window geometry")
                return None
                
            # Parse the geometry output
            # Example output:
            # Window 123456789 (windsurf):
            #   Position: 100,200 (screen: 0)
            #   Geometry: 800x600
            output = result.stdout.strip()
            
            # Extract position and size using regex
            import re
            pos_match = re.search(r'Position: (\d+),(\d+)', output)
            size_match = re.search(r'Geometry: (\d+)x(\d+)', output)
            
            if pos_match and size_match:
                x = int(pos_match.group(1))
                y = int(pos_match.group(2))
                width = int(size_match.group(1))
                height = int(size_match.group(2))
                return (x, y, width, height)
            
            print("Could not parse window geometry")
            return None
            
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None

    def capture_window_screenshot(self, window_id: str, filename: str) -> bool:
        """Capture a screenshot of a specific window
        
        Args:
            window_id: X window ID
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure screenshots directory exists
            if not os.path.exists(self.screenshots_dir):
                os.makedirs(self.screenshots_dir)
            
            # Full path to screenshot
            screenshot_path = os.path.join(self.screenshots_dir, filename)
            
            # Try to capture with import command
            result = subprocess.run(
                ['import', '-window', window_id, screenshot_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error capturing window: {result.stderr}")
                return False
            
            # Verify the screenshot was created and is valid
            if not os.path.exists(screenshot_path):
                print(f"Screenshot file not created: {screenshot_path}")
                return False
            
            # Try to read with cv2 to verify it's valid
            img = cv2.imread(screenshot_path)
            if img is None:
                print(f"Failed to read screenshot with OpenCV: {screenshot_path}")
                return False
            
            if self.debug:
                print(f"Screenshot captured successfully: {screenshot_path}")
                print(f"Image size: {img.shape}")
            
            return True
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return False

    def save_debug_image(self, image, name):
        """Save debug image to screenshots directory"""
        try:
            filename = os.path.join(self.screenshots_dir, f"{name}.png")
            cv2.imwrite(filename, image)
            print(f"Saved debug image: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving debug image: {e}")
            return None

    def run_command_in_terminal(self):
        """Run the command specified in .env file in a new terminal"""
        try:
            # Temporarily disable focus lock while running command
            was_locked = self.focus_lock['enabled']
            locked_type = self.focus_lock['window_type']
            self.disable_focus_lock()
            
            # Open new terminal
            subprocess.Popen(['gnome-terminal', '--', 'bash'], cwd=self.project_dir)
            time.sleep(2)  # Wait for terminal to open

            # Type cd command to navigate to project directory
            pyautogui.write(f'cd {self.project_dir}')
            pyautogui.press('enter')
            time.sleep(0.5)

            # Type and execute the command
            pyautogui.write(self.command)
            pyautogui.press('enter')
            time.sleep(5)  # Wait for command to complete

            # Get clipboard content (output should be there due to xclip in the command)
            output = pyperclip.paste()
            print("\nCommand Output:")
            print("-" * 50)
            print(output)
            print("-" * 50)

            # Close terminal
            pyautogui.write('exit')
            pyautogui.press('enter')
            
            # Restore focus lock if it was enabled
            if was_locked:
                time.sleep(1)  # Wait for terminal to close
                self.enable_focus_lock(locked_type)
                self.switch_to_window(locked_type)
            
            return True
        except Exception as e:
            print(f"Error running command in terminal: {e}")
            return False

    def run_test_and_report(self):
        """Complete workflow: run test in terminal and report to Windsurf"""
        try:
            print("\nStarting test workflow...")
            
            # Run command and get output
            if not self.run_command_in_terminal():
                print("Failed to run command")
                return False
            
            try:
                # Get clipboard content
                output = pyperclip.paste()
                if not output:
                    print("No output in clipboard")
                    return False
                    
                print("\nTest output captured:")
                print("-" * 50)
                print(output)
                print("-" * 50)
                
                # Switch back to the selected Windsurf window
                if not self.switch_to_window('windsurf'):
                    print("Could not switch to Windsurf window")
                    return False
                
                print("Waiting for window switch...")
                time.sleep(self.window_switch_delay)
                
                # Check focus periodically
                self.check_and_restore_focus()
                
                # Take screenshot of Windsurf window
                if not self.capture_window_screenshot(
                    self.windows['windsurf'],
                    "windsurf_full_shot.png"
                ):
                    print("Failed to capture window screenshot")
                    return False
                
                screenshot_path = os.path.join(self.screenshots_dir, "windsurf_full_shot.png")
                screenshot = cv2.imread(screenshot_path)
                if screenshot is None:
                    print("Failed to read screenshot")
                    return False
                
                print(f"Screenshot captured successfully, size: {screenshot.shape}")
                
                # Find Cascade input
                input_box = self.input_detector.find_input_box(screenshot)
                if not input_box:
                    print("Could not find Cascade input")
                    return False
                
                print(f"Found input box at: {input_box.click_position}")
                
                # Click the input field
                x, y = input_box.click_position
                pyautogui.click(x, y)
                time.sleep(0.5)
                
                # Check focus again before pasting
                self.check_and_restore_focus()
                
                # Paste the output
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                
                # Check focus one last time before pressing enter
                self.check_and_restore_focus()
                
                # Press enter
                pyautogui.press('enter')
                print("Successfully reported test results")
                return True
                
            except Exception as e:
                print(f"Error in test workflow: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            print(f"Error in test workflow: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def run(self):
        """Main run loop"""
        try:
            print("\nStarting window selection...")
            if not self.select_windsurf_window():
                print("Window selection failed or cancelled")
                return
                
            print("\nStarting test workflow...")
            if self.run_test_and_report():
                print("Test workflow completed successfully")
            else:
                print("Test workflow failed")
                
        except Exception as e:
            print(f"Error in run loop: {e}")

    def check_for_approval(self):
        """Check if there's an approval button and click it"""
        try:
            # Get window info
            window_info = self.get_active_window_info()
            if not window_info:
                print("Could not get window info")
                return False
            
            # Take screenshot
            screenshot = self.capture_window_screenshot(None)  # We don't need window_info anymore
            if screenshot is None:
                print("Failed to capture screenshot")
                return False
            
            # Look for "Approve" or "Run" text in screenshot
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            
            if "Approve" in text or "Run" in text:
                print("Found approval button")
                # TODO: Click approval button
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking for approval: {e}")
            return False

if __name__ == "__main__":
    controller = WindowController()
    controller.run()
