import win32gui as win
import win32con as con
import time
import pyautogui as pgui
from PIL import ImageGrab
from ai import EasyOCR

def get_active_window():
    
    try:
        hwnd = win.GetForegroundWindow()
        if hwnd:
            return hwnd
        return None
    except Exception as e:
        print(f"Error getting active window: {e}")
        return None
    
def get_active_window_title():
    try:
        hwnd = win.GetForegroundWindow()
        if hwnd:
            return win.GetWindowText(hwnd)
        return None
    except Exception as e:
        print(f"Error getting active window title: {e}")
        return None
    
def do_screenshot():
    try:
        hwnd = win.GetForegroundWindow()
        if hwnd:
            rect = win.GetWindowRect(hwnd)
            x1, y1, x2, y2 = rect
            width = x2 - x1
            height = y2 - y1
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            return screenshot
    except:
        return None
    
def set_active_window_by_app_name(app_name):
    try:
        # First try exact match
        hwnd = win.FindWindow(None, app_name)
        if hwnd:
            win.SetForegroundWindow(hwnd)
            return True
            
        # If exact match fails, try partial match by enumerating windows
        def callback(hwnd, windows):
            if win.IsWindowVisible(hwnd):
                window_title = win.GetWindowText(hwnd)
                if app_name.lower() in window_title.lower():
                    windows.append(hwnd)
            return True
            
        windows = []
        win.EnumWindows(callback, windows)
        
        if windows:
            win.SetForegroundWindow(windows[0])
            return True
            
        return False
    except Exception as e:
        print(f"Error setting active window: {e}")
        return False

def minimize_window():
    try:
        hwnd = win.GetForegroundWindow()
        if hwnd and hwnd != 0:
            win.ShowWindow(hwnd, con.SW_MINIMIZE)
            return True
        return False
    except Exception as e:
        print(f"Error minimizing window: {e}")
        return False

def restore_window(hwnd):
    try:
        if hwnd and hwnd != 0:
            # Check if window is minimized
            if win.IsIconic(hwnd):
                win.ShowWindow(hwnd, con.SW_RESTORE)
                return True
            else:
                # Window already restored, nothing to do
                return True
        return False
    except Exception as e:
        print(f"Error restoring window: {e}")
        return False


def get_window_rect(hwnd):
    return win.GetWindowRect(hwnd)
def type_text(text):
    pgui.typewrite(text)

def mouse_to(x, y):
    pgui.moveTo(x, y)

def click(button):
    """
    button: 
        "left", "right", "middle"
    """
    pgui.click(button=button)

def press(key):
    pgui.press(key)

if __name__ == "__main__":
    ocr = EasyOCR(languages=["ru", "en"])
    print(get_active_window_title())
    set_active_window_by_app_name("Comet")
    time.sleep(1)
    wind = get_active_window()
    restore_window(wind)
    print(get_active_window_title())
    time.sleep(1)
    rect = get_window_rect(wind)
    print(rect)
    mouse_to(rect[0]+rect[2]//2, rect[1]+rect[3]//2)
    click("right")    
    do_screenshot().save("screenshot.png")
    for detection in ocr.extract_text_detailed("screenshot.png"):
        if "просмотр " in detection["text"].lower():
            tl = detection["position"]["top_left"]
            br = detection["position"]["bottom_right"]
            print(detection)
            center = (int(tl[0]) + (int(br[0]) - int(tl[0]))//2, int(tl[1]) + (int(br[1]) - int(tl[1]))//2)
            print(center)
            mouse_to(center[0], center[1])
            break
    click("left")
    # minimize_window()

    