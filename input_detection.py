#!/usr/bin/env python3

import cv2
import numpy as np
import pytesseract
import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
import pyautogui

@dataclass
class InputBox:
    """Represents a detected input box in the UI"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    text: str
    click_position: Tuple[int, int]

class InputDetector:
    """Detects input boxes in UI screenshots"""
    
    def __init__(self, debug: bool = False):
        """Initialize the detector
        
        Args:
            debug: If True, save debug images during detection
        """
        self.debug = debug
        self.debug_dir = "debug_screenshots"
        if debug:
            self._ensure_debug_dir()
        
        # Default coordinates for Cascade input area as fallback
        self.default_input_coords = (500, 500)
    
    def _ensure_debug_dir(self):
        """Ensure debug screenshots directory exists"""
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
    
    def _save_debug_image(self, image: np.ndarray, name: str):
        """Save an image for debugging
        
        Args:
            image: Image to save
            name: Name for the debug image
        """
        if not self.debug:
            return
            
        filepath = os.path.join(self.debug_dir, f"{name}.png")
        cv2.imwrite(filepath, image)
        print(f"Saved debug image: {name}.png")
    
    def find_input_box_by_placeholder(self, image: np.ndarray) -> Optional[InputBox]:
        """Find the input box containing placeholder text
        
        Args:
            image: Screenshot to search in
            
        Returns:
            InputBox if found, None otherwise
        """
        try:
            # Blur image to reduce noise
            blurred = cv2.GaussianBlur(image, (5, 5), 0)
            self._save_debug_image(blurred, 'blurred_input')
            
            # Convert to grayscale
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            
            # Threshold
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find rectangles that could be input boxes
            potential_inputs = []
            debug_img = image.copy()
            
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Input box should be wider than tall (aspect ratio > 3)
                if w > 3*h and w > 100:
                    # Extract ROI and OCR
                    roi = image[y:y+h, x:x+w]
                    text = pytesseract.image_to_string(roi).strip()
                    
                    if text:
                        print(f"Found input box with placeholder text: {text}")
                        potential_inputs.append((x, y, w, h, text))
                        
                        # Draw on debug image
                        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(debug_img, text, (x, y-5),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            if potential_inputs:
                # Select the input box with the longest text
                potential_inputs.sort(key=lambda x: len(x[4]), reverse=True)
                x, y, w, h, text = potential_inputs[0]
                
                # Calculate click position
                click_x = x + w//2
                click_y = y + h//2
                
                self._save_debug_image(debug_img, 'detected_input')
                print(f"Selected input box with text: {text}")
                
                return InputBox(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    confidence=100.0,  # No confidence score for this method
                    text=text,
                    click_position=(click_x, click_y)
                )
                
        except Exception as e:
            print(f"Error finding input box: {e}")
        
        return None
    
    def find_arrow_icon(self, image: np.ndarray, is_up_arrow: bool = False) -> Optional[Tuple[int, int]]:
        """Find arrow icon in image
        
        Args:
            image: Image to search in
            is_up_arrow: True to look for up arrow, False for down arrow
            
        Returns:
            Tuple of (x, y) coordinates if found, None otherwise
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Threshold
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                # Get bounding box
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Arrow should be roughly square
                if 0.8 < w/h < 1.2 and w > 10:
                    # Get center point
                    center_x = x + w//2
                    center_y = y + h//2
                    
                    return (center_x, center_y)
            
        except Exception as e:
            print(f"Error finding arrow icon: {e}")
        
        return None
    
    def find_input_box(self, image: np.ndarray) -> Optional[InputBox]:
        """Find Cascade's input box in the screenshot using template matching
        
        Args:
            image: Screenshot of the window
            
        Returns:
            InputBox object if found, None otherwise
        """
        try:
            height, width = image.shape[:2]
            
            # Load template images
            template1 = cv2.imread('screenshots/input.png')
            template2 = cv2.imread('screenshots/input_new.png')
            
            # Convert all to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template1_gray = cv2.cvtColor(template1, cv2.COLOR_BGR2GRAY)
            template2_gray = cv2.cvtColor(template2, cv2.COLOR_BGR2GRAY)
            
            if self.debug:
                self._save_debug_image(gray, "1_grayscale.png")
            
            # Only search in right half of image
            right_half = gray[:, width//2:]
            
            # Try matching both templates
            matches = []
            for i, template in enumerate([template1_gray, template2_gray]):
                # Match template
                result = cv2.matchTemplate(right_half, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # If good match found
                if max_val > 0.6:  # Adjust threshold as needed
                    x = max_loc[0]
                    y = max_loc[1]
                    w = template.shape[1]
                    h = template.shape[0]
                    
                    matches.append({
                        'x': x + width//2,  # Adjust for right half
                        'y': y,
                        'width': w,
                        'height': h,
                        'confidence': max_val,
                        'template_idx': i
                    })
                    
                    if self.debug:
                        print(f"Found match with template {i}:")
                        print(f"Position: ({x + width//2}, {y})")
                        print(f"Size: {w}x{h}")
                        print(f"Confidence: {max_val:.3f}")
            
            if not matches:
                if self.debug:
                    print("No input box matches found")
                return None
                
            # Use best match
            best_match = max(matches, key=lambda m: m['confidence'])
            
            # Calculate click position
            click_x = best_match['x'] + best_match['width']//2
            click_y = best_match['y'] + best_match['height']//2
            
            if self.debug:
                # Draw debug visualization
                debug_img = image.copy()
                cv2.rectangle(debug_img,
                            (best_match['x'], best_match['y']),
                            (best_match['x'] + best_match['width'],
                             best_match['y'] + best_match['height']),
                            (0, 255, 0), 2)
                cv2.circle(debug_img, (click_x, click_y), 5, (255, 0, 0), -1)
                self._save_debug_image(debug_img, "2_detection.png")
            
            return InputBox(
                x=best_match['x'],
                y=best_match['y'],
                width=best_match['width'],
                height=best_match['height'],
                confidence=best_match['confidence'],
                text="input_box",
                click_position=(click_x, click_y)
            )
            
        except Exception as e:
            print(f"Error finding input box: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_active_window_info(self):
        """Get the active window's info"""
        return pyautogui.getActiveWindow()

    def capture_window_screenshot(self, window_info):
        """Capture a screenshot of the given window"""
        return pyautogui.screenshot(region=window_info.box)

def main():
    """Test the input detection"""
    # Initialize detector with debug mode
    detector = InputDetector(debug=True)
    
    # Get screenshot from WindowController
    window_info = detector.get_active_window_info()
    if not window_info:
        print("Could not get window info")
        return
    
    screenshot = detector.capture_window_screenshot(window_info)
    if screenshot is None:
        print("Failed to capture screenshot")
        return
    
    # Convert screenshot to OpenCV image
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Find input box
    input_box = detector.find_input_box(frame)
    if input_box:
        print("\nDetected Input Box:")
        print(f"Position: ({input_box.x}, {input_box.y})")
        print(f"Size: {input_box.width}x{input_box.height}")
        print(f"Text: '{input_box.text}' (Confidence: {input_box.confidence:.0f}%)")
        print(f"Click Position: {input_box.click_position}")
    else:
        print("\nNo input box detected")

if __name__ == "__main__":
    main()
