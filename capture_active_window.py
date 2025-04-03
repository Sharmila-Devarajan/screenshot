import tkinter as tk
from tkinter import ttk, scrolledtext
import pyautogui
import time
import os
import platform
import tempfile
import threading
import base64
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime
import json
import uuid

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ES Screenshot Tool")
        self.root.geometry("1024x768")
        self.root.resizable(True, True)

        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.payload_file = os.path.join(self.script_dir, "payload.json")

        self.setup_icon()
        
        self.root.configure(bg="#f0f0f0")
        
        self.screenshots = []
        self.is_capturing = False
        self.status_message = ""
        self.status_type = "info"
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"es_screenshots_{self.timestamp}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.create_main_layout()
        self.create_floating_button()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


    def save_payload_to_file(self, payload):
        """Save the payload to a JSON file in the script directory"""
        try:
            with open(self.payload_file, 'w') as f:
                json.dump(payload, f, indent=2)
            self.update_status(f"Payload saved to {self.payload_file}", "success")
        except Exception as e:
            self.update_status(f"Error saving payload: {str(e)}", "error")


    def setup_icon(self):
        try:
            icon = Image.new('RGB', (16, 16), color='blue')
            photo = ImageTk.PhotoImage(icon)
            self.root.iconphoto(False, photo)
        except Exception:
            pass
    
    def create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            main_frame, 
            text="ES Screenshot Tool", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        instruction_frame = ttk.LabelFrame(main_frame, text="Instructions", padding=10)
        instruction_frame.pack(fill=tk.X, pady=(0, 10))
        
        instructions = """
1. Press the floating button to capture screenshots
2. The app will take a screenshot of the current active window only (excluding this tool)
3. For multiple windows, press the button, then switch windows, then press it again
4. All screenshots are saved automatically
        """
        
        instruction_label = ttk.Label(
            instruction_frame, 
            text=instructions, 
            justify=tk.LEFT,
            wraplength=760
        )
        instruction_label.pack(fill=tk.X)
        
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="Ready to capture screenshots. Press the button.",
            foreground="#0066cc",
            background="#e6f0ff",
            padding=10
        )
        self.status_label.pack(fill=tk.X)
        
        screenshots_frame = ttk.LabelFrame(main_frame, text="Captured Screenshots", padding=10)
        screenshots_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas_frame = ttk.Frame(screenshots_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#ffffff")
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.screenshots_container = ttk.Frame(self.canvas)
        self.screenshots_container_id = self.canvas.create_window(
            (0, 0), 
            window=self.screenshots_container, 
            anchor=tk.NW,
            width=self.canvas.winfo_width()
        )
        
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.screenshots_container.bind("<Configure>", self.on_frame_configure)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        open_folder_button = ttk.Button(
            button_frame,
            text="Open Screenshots Folder",
            command=self.open_screenshots_folder
        )
        open_folder_button.pack(side=tk.RIGHT)
    
    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.screenshots_container_id, width=event.width)
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def create_floating_button(self):
        self.button_window = tk.Toplevel(self.root)
        self.button_window.overrideredirect(True)
        self.button_window.attributes('-topmost', True)
        
        self.button_window.attributes('-transparentcolor', '#f0f0f0')
        
        button_frame = tk.Frame(self.button_window, bg="#f0f0f0")
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        try:
            image_path = "capture.png"
            if os.path.exists(image_path):
                original_img = Image.open(image_path)
                button_size = 40
                button_img = original_img.resize((button_size, button_size), Image.LANCZOS)
                self.button_photo = ImageTk.PhotoImage(button_img)
                
                capture_button = tk.Button(
                    button_frame,
                    image=self.button_photo,
                    bg="#0066ff",
                    relief=tk.RAISED,
                    command=self.handle_capture
                )
            else:
                capture_button = tk.Button(
                    button_frame,
                    text="ES",
                    font=("Arial", 14, "bold"),
                    bg="#0066ff",
                    fg="white",
                    width=3,
                    height=1,
                    relief=tk.RAISED,
                    command=self.handle_capture
                )
        except Exception as e:
            capture_button = tk.Button(
                button_frame,
                text="ES",
                font=("Arial", 14, "bold"),
                bg="#0066ff",
                fg="white",
                width=3,
                height=1,
                relief=tk.RAISED,
                command=self.handle_capture
            )
        
        capture_button.pack(padx=5, pady=5)
        
        self.position_floating_button()
        
        capture_button.bind("<ButtonPress-1>", self.start_move)
        capture_button.bind("<ButtonRelease-1>", self.stop_move)
        capture_button.bind("<B1-Motion>", self.do_move)
    
    def position_floating_button(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        button_width = 60
        button_height = 60
        
        x_position = screen_width - button_width - 40
        y_position = screen_height - button_height - 40
        
        self.button_window.geometry(f"{button_width}x{button_height}+{x_position}+{y_position}")
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    
    def stop_move(self, event):
        self.x = None
        self.y = None
    
    def do_move(self, event):
        if self.is_capturing:
            return
            
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.button_window.winfo_x() + deltax
        y = self.button_window.winfo_y() + deltay
        self.button_window.geometry(f"+{x}+{y}")
    
    def handle_capture(self):
        if self.is_capturing:
            return
            
        capture_thread = threading.Thread(target=self.capture_active_window)
        capture_thread.daemon = True
        capture_thread.start()
    
    def get_window_info(self):
        system = platform.system()
        
        if system == 'Windows':
            try:
                import ctypes
                from ctypes.wintypes import RECT
                
                user32 = ctypes.windll.user32
                foreground_window = user32.GetForegroundWindow()
                
                length = user32.GetWindowTextLengthW(foreground_window)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(foreground_window, buff, length + 1)
                title = buff.value
                
                rect = RECT()
                user32.GetWindowRect(foreground_window, ctypes.byref(rect))
                bounds = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
                
                return title, bounds
            except Exception as e:
                return f"Window_{datetime.now().strftime('%H%M%S')}", None
        
        elif system == 'Darwin':  # macOS
            try:
                import subprocess
                
                title_cmd = """osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'"""
                title = subprocess.check_output(title_cmd, shell=True).decode('utf-8').strip()
                
                bounds_script = """
                osascript -e '
                tell application "System Events"
                    set frontApp to first application process whose frontmost is true
                    set frontAppName to name of frontApp
                    tell process frontAppName
                        set appWindow to first window
                        set {x, y} to position of appWindow
                        set {width, height} to size of appWindow
                        return x & "," & y & "," & width & "," & height
                    end tell
                end tell
                '
                """
                
                result = subprocess.check_output(bounds_script, shell=True).decode('utf-8').strip()
                bounds = [int(val) for val in result.split(',')]
                return title, tuple(bounds)
            except Exception as e:
                return f"Window_{datetime.now().strftime('%H%M%S')}", None
        
        elif system == 'Linux':
            try:
                import subprocess
                
                win_id_cmd = ["xdotool", "getactivewindow"]
                win_id = subprocess.check_output(win_id_cmd).decode('utf-8').strip()
                
                name_cmd = ["xdotool", "getwindowname", win_id]
                title = subprocess.check_output(name_cmd).decode('utf-8').strip()
                
                geo_cmd = ["xdotool", "getwindowgeometry", win_id]
                geo_output = subprocess.check_output(geo_cmd).decode('utf-8')
                
                pos_line = [line for line in geo_output.split('\n') if "Position" in line][0]
                pos_parts = pos_line.split(":")[1].strip().split(",")
                x = int(pos_parts[0])
                y = int(pos_parts[1])
                
                size_line = [line for line in geo_output.split('\n') if "Geometry" in line][0]
                size_parts = size_line.split(":")[1].strip().split("x")
                width = int(size_parts[0])
                height = int(size_parts[1])
                
                return title, (x, y, width, height)
            except Exception as e:
                return f"Window_{datetime.now().strftime('%H%M%S')}", None
        
        return f"Window_{datetime.now().strftime('%H%M%S')}", None
    
    def capture_active_window(self):
        self.is_capturing = True
        
        try:
            self.root.withdraw()
            self.button_window.withdraw()
            
            time.sleep(0.5)
            
            window_title, window_bounds = self.get_window_info()
            
            if "ES Screenshot Tool" in window_title or not window_title:
                self.root.deiconify()
                self.button_window.deiconify()
                self.update_status("No active window detected or captured our own app", "info")
                self.is_capturing = False
                return
            
            if window_bounds:
                x, y, width, height = window_bounds
                
                if width <= 0 or height <= 0:
                    self.root.deiconify()
                    self.button_window.deiconify()
                    self.update_status("Invalid window dimensions detected", "error")
                    self.is_capturing = False
                    return
                
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                capture_type = "active window"
            else:
                if platform.system() == 'Windows':
                    try:
                        import win32gui
                        import win32ui
                        from ctypes import windll
                        from PIL import Image
                        
                        hwnd = win32gui.GetForegroundWindow()
                        
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        width = right - left
                        height = bottom - top
                        
                        hwndDC = win32gui.GetWindowDC(hwnd)
                        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                        saveDC = mfcDC.CreateCompatibleDC()
                        
                        saveBitMap = win32ui.CreateBitmap()
                        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
                        
                        saveDC.SelectObject(saveBitMap)
                        
                        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
                        
                        bmpinfo = saveBitMap.GetInfo()
                        bmpstr = saveBitMap.GetBitmapBits(True)
                        screenshot = Image.frombuffer(
                            'RGB',
                            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                            bmpstr, 'raw', 'BGRX', 0, 1)
                        
                        win32gui.DeleteObject(saveBitMap.GetHandle())
                        saveDC.DeleteDC()
                        mfcDC.DeleteDC()
                        win32gui.ReleaseDC(hwnd, hwndDC)
                        
                        capture_type = "active window"
                    except Exception:
                        screenshot = pyautogui.screenshot()
                        capture_type = "full screen (fallback)"
                else:
                    screenshot = pyautogui.screenshot()
                    capture_type = "full screen (fallback)"
            
            self.root.deiconify()
            self.button_window.deiconify()
            
            sanitized_title = ''.join(c for c in window_title if c.isalnum() or c in ' -_')[:30]
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"screenshot_{timestamp}_{sanitized_title}.png"
            file_path = os.path.join(self.temp_dir, filename)
            screenshot.save(file_path)
            
            # Convert screenshot to base64
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str_raw = base64.b64encode(buffered.getvalue()).decode()
            
            # Add data URI prefix to base64 string
            img_str = f"data:image/png;base64,{img_str_raw}"
            
            # Create JSON payload with the base64 image
            session_id = str(uuid.uuid4())
            payload_json = {
                "session_id": session_id,
                "user_message": {
                    "type": "image",
                    "image": [img_str],
                },
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "get only the Inspector's Notes and Engine description from this image",
                        "attachments": [
                            {
                                "type": "file",
                                "base64String": [img_str]
                            }
                        ]
                    }
                ]
            }
            
            # Print the payload_json to terminal
            print(json.dumps(payload_json))

            self.save_payload_to_file(payload_json)
            
            # Add to screenshots list (at the beginning)
            self.screenshots.insert(0, {
                "image": screenshot,
                "title": window_title,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "path": file_path,
                "base64": img_str,
                "payload_json": payload_json
            })
            
            # Clear existing screenshots from UI
            for widget in self.screenshots_container.winfo_children():
                widget.destroy()
            
            # Update the UI with all screenshots (newest first)
            for i in range(len(self.screenshots)):
                self.add_screenshot_to_ui(i)
            
            self.update_status(f"Captured {capture_type}: {window_title}", "success")
        
        except Exception as e:
            self.update_status(f"Error capturing screenshot: {str(e)}", "error")
        
        finally:
            self.is_capturing = False
    
    def update_status(self, message, status_type="info"):
        self.status_message = message
        self.status_type = status_type
        
        if status_type == "success":
            bg_color = "#d4edda"
            fg_color = "#155724"
        elif status_type == "error":
            bg_color = "#f8d7da"
            fg_color = "#721c24"
        else:  # info
            bg_color = "#e6f0ff"
            fg_color = "#0066cc"
        
        self.status_label.configure(
            text=message,
            background=bg_color,
            foreground=fg_color
        )
    
    def add_screenshot_to_ui(self, index):
        screenshot_data = self.screenshots[index]
        
        frame = ttk.Frame(self.screenshots_container)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame,
            text=f"{screenshot_data['title']} - {screenshot_data['timestamp']}",
            font=("Arial", 10, "bold")
        )
        title_label.pack(side=tk.LEFT, pady=5)
        
        open_button = ttk.Button(
            header_frame,
            text="Open",
            command=lambda path=screenshot_data['path']: self.open_screenshot(path)
        )
        open_button.pack(side=tk.RIGHT, padx=5)
        
        img = screenshot_data['image']
        
        max_width = 600
        width, height = img.size
        ratio = min(max_width / width, 1.0)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        thumbnail = img.resize((new_width, new_height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(thumbnail)
        
        screenshot_data['photo'] = photo
        
        image_label = ttk.Label(frame, image=photo)
        image_label.image = photo
        image_label.pack(pady=5)
        
        self.on_frame_configure(None)
    
    def open_screenshot(self, path):
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':  # macOS
                import subprocess
                subprocess.call(['open', path])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', path])
        except Exception as e:
            self.update_status(f"Error opening file: {str(e)}", "error")
    
    def open_screenshots_folder(self):
        try:
            if platform.system() == 'Windows':
                os.startfile(self.temp_dir)
            elif platform.system() == 'Darwin':  # macOS
                import subprocess
                subprocess.call(['open', self.temp_dir])
            else:  # Linux
                import subprocess
                subprocess.call(['xdg-open', self.temp_dir])
        except Exception as e:
            self.update_status(f"Error opening folder: {str(e)}", "error")
    
    def on_close(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()