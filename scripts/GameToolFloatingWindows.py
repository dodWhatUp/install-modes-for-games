"""Place a nonmodal window beside the current pointer, inside its work area."""
import os


def popup_rectangle(pointer, size, area, gap=12, margin=8):
    px, py = pointer
    left, top, right, bottom = area
    width = min(size[0], max(1, right - left - margin * 2))
    height = min(size[1], max(1, bottom - top - margin * 2))
    x = px + gap if px + gap + width <= right - margin else px - gap - width
    y = py + gap if py + gap + height <= bottom - margin else py - gap - height
    x = max(left + margin, min(x, right - margin - width))
    y = max(top + margin, min(y, bottom - margin - height))
    return width, height, x, y


def work_area(window, pointer):
    if os.name == 'nt':
        # Read-only monitor queries, in this app's existing DPI context.
        import ctypes
        from ctypes import wintypes
        class MonitorInfo(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT),
                        ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        user.MonitorFromPoint.restype = wintypes.HANDLE
        user.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        user.GetMonitorInfoW.restype = wintypes.BOOL
        monitor = user.MonitorFromPoint(wintypes.POINT(*pointer), 2)
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(info)
        if monitor and user.GetMonitorInfoW(monitor, ctypes.byref(info)):
            rect = info.rcWork
            return rect.left, rect.top, rect.right, rect.bottom
    left, top = window.winfo_vrootx(), window.winfo_vrooty()
    return left, top, left + window.winfo_vrootwidth(), top + window.winfo_vrootheight()


def show_near_pointer(window, pointer=None, size=None):
    pointer = pointer if pointer is not None else window.winfo_pointerxy()
    window.update_idletasks()
    if size is None:
        size = (max(window.winfo_reqwidth(), window.winfo_width()),
                max(window.winfo_reqheight(), window.winfo_height()))
    area = work_area(window, pointer)
    if os.name == 'nt':
        # Reserve space for the native border/title outside Tk's client size.
        area = (area[0], area[1], area[2] - 8, area[3] - 36)
    width, height, x, y = popup_rectangle(pointer, size, area)
    # A literal plus preserves absolute negative coordinates on left-hand screens.
    window.geometry(f'{width}x{height}+{x}+{y}')
    window.deiconify()
    window.lift()
    window.focus_set()
    return width, height, x, y
