# PyGUI Commander

PyGUI Commander is a Python-based automation tool designed to interact with Windsurf IDE's GUI elements. It currently focuses on automating test execution and result reporting through GUI interaction.

## Features

- Automatic window detection and switching
- Robust input box detection using template matching
- Support for both light and dark Windsurf themes
- Debug visualization for development
- Configurable through environment variables

## Prerequisites

- Python 3.x
- Linux environment with X11
- Windsurf IDE installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pygui-commander.git
cd pygui-commander
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```
PROJECT_PATH="path/to/your/project"
COMMAND="your test command"
```

## Usage

Run the main script:
```bash
python main.py
```

The tool will:
1. Find and switch to the Windsurf window
2. Locate the input box using template matching
3. Execute the specified command
4. Report results back through Windsurf's interface

## Development Guide

### Project Structure

```
pygui-commander/
├── main.py                 # Main entry point and window management
├── input_detection.py      # Input box detection logic
├── screenshots/            # Template and debug images
│   ├── input.png          # Light theme template
│   └── input_new.png      # Dark theme template
└── debug_screenshots/      # Debug output directory
```

### Input Box Detection

The tool uses template matching to detect Windsurf's input box. Two template images are used:
- `screenshots/input.png`: Light theme input box
- `screenshots/input_new.png`: Dark theme input box

Template matching parameters:
- Confidence threshold: 0.6 (60%)
- Search area: Right half of window
- Expected dimensions: ~533x43 pixels

### Adapting to Theme Changes

If Windsurf's theme or UI changes:

1. Take new screenshots of the input box:
   - Use any screenshot tool to capture ONLY the input box
   - Dimensions should be around 533x43 pixels
   - Save in PNG format

2. Update templates:
   - For light theme: Replace `screenshots/input.png`
   - For dark theme: Replace `screenshots/input_new.png`

3. Test detection:
```bash
python test_input_detection.py
```

4. Adjust confidence threshold if needed:
   - Open `input_detection.py`
   - Find `if max_val > 0.6:`
   - Adjust threshold value (0.0 to 1.0)

### Debug Mode

Enable debug mode to see detection process:
1. Set `debug=True` in `InputDetector` initialization
2. Check `debug_screenshots/` for output:
   - `1_grayscale.png`: Grayscale conversion
   - `2_detection.png`: Final detection result

### Contributing

1. Fork the repository
2. Create your feature branch:
```bash
git checkout -b feature/my-new-feature
```

3. Make your changes
4. Run tests:
```bash
python test_input_detection.py
```

5. Commit your changes:
```bash
git commit -am 'Add some feature'
```

6. Push to the branch:
```bash
git push origin feature/my-new-feature
```

7. Create a Pull Request

## Troubleshooting

### Input Box Not Detected

1. Check template images match current theme
2. Enable debug mode and check debug images
3. Try adjusting confidence threshold
4. Verify window is active and fully visible

### Window Switching Issues

1. Verify window titles in `main.py`
2. Check X11 window permissions
3. Ensure xdotool is installed

## License

[Your chosen license]

## Contributors

[List of contributors]
