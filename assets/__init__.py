# assets/__init__.py

import base64
from PyQt6.QtGui import QPixmap, QIcon
from .dashboardIco import DASHBOARDICON
from .appicon import APPICON
from .appiconpng import APPICONPNG
from .dashboardimg import DASHBOARDIMG
from .membersimg import MEMBERSIMG
from .eyeIcon import EYE
from. conference import CONFERANCE
from .ethics import ETHICS
from .cogwheel import COGWHEEL
from .analytics import ANALYTICS
from .user import USER
_IMAGES_REGISTRY = {
    "appicon": APPICON,
    "appiconpng": APPICONPNG,
    "dashboardimg": DASHBOARDIMG,
    "dashboard_icon": DASHBOARDICON,
    "memberimg":MEMBERSIMG,
    "eye_icon":EYE,
    "conferance":CONFERANCE,
    "ethics":ETHICS,
    "cogwheel":COGWHEEL,
    "analytics":ANALYTICS,
    "user": USER
}

def get_pixmap(image_name: str) -> QPixmap:

    if image_name not in _IMAGES_REGISTRY:
        print(f"Warning: Image '{image_name}' not found in registry!")
        return QPixmap()
        
    base64_str = _IMAGES_REGISTRY[image_name]
    image_bytes = base64.b64decode(base64_str)
    
    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)
    return pixmap

def get_icon(image_name: str) -> QIcon:
    pixmap = get_pixmap(image_name)
    return QIcon(pixmap)