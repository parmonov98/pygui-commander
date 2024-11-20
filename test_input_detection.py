#!/usr/bin/env python3

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple
import os

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

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def save_debug_image(image, name):
    debug_dir = "debug_screenshots"
    ensure_dir(debug_dir)
    filepath = os.path.join(debug_dir, f"{name}.png")
    cv2.imwrite(filepath, image)
    print(f"Saved: {name}.png")

def find_input_box(image, debug=True):
    try:
        height, width = image.shape[:2]
        
        # Load template images
        template1 = cv2.imread('screenshots/input.png')
        template2 = cv2.imread('screenshots/input_new.png')
        
        # Convert all to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template1_gray = cv2.cvtColor(template1, cv2.COLOR_BGR2GRAY)
        template2_gray = cv2.cvtColor(template2, cv2.COLOR_BGR2GRAY)
        
        if debug:
            save_debug_image(gray, "1_grayscale")
        
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
                
                print(f"Found match with template {i}:")
                print(f"Position: ({x + width//2}, {y})")
                print(f"Size: {w}x{h}")
                print(f"Confidence: {max_val:.3f}")
        
        if not matches:
            print("No matches found")
            return None
            
        # Use best match
        best_match = max(matches, key=lambda m: m['confidence'])
        
        # Draw debug visualization
        debug_img = image.copy()
        cv2.rectangle(debug_img,
                     (best_match['x'], best_match['y']),
                     (best_match['x'] + best_match['width'],
                      best_match['y'] + best_match['height']),
                     (0, 255, 0), 2)
        
        # Calculate click position
        click_x = best_match['x'] + best_match['width']//2
        click_y = best_match['y'] + best_match['height']//2
        cv2.circle(debug_img, (click_x, click_y), 5, (255, 0, 0), -1)
        
        if debug:
            save_debug_image(debug_img, "2_detection")
        
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

def main():
    """Test input detection on a screenshot"""
    # Load the most recent screenshot
    screenshot_path = "screenshots/windsurf_full_shot_chat_started.png"
    if not os.path.exists(screenshot_path):
        print(f"Screenshot not found: {screenshot_path}")
        return
    
    print(f"Loading screenshot: {screenshot_path}")
    screenshot = cv2.imread(screenshot_path)
    if screenshot is None:
        print("Failed to load screenshot")
        return
    
    print(f"Screenshot size: {screenshot.shape}")
    input_box = find_input_box(screenshot)
    
    if input_box:
        print(f"Found input box:")
        print(f"Position: ({input_box.x}, {input_box.y})")
        print(f"Size: {input_box.width}x{input_box.height}")
        print(f"Click position: {input_box.click_position}")
    else:
        print("No input box found")

if __name__ == "__main__":
    main()
