import cv2
import threading
import time
import base64
from io import BytesIO
from PIL import Image

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class CameraManager:
    def __init__(self, tts=None):
        self.tts = tts
        self.cap = None
        self.is_running = False
        self.model = None
        self.detection_thread = None
        self.latest_objects = []
        self.frame = None
        
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO('yolov8n.pt')
                print("YOLO model loaded successfully")
            except Exception as e:
                print(f"YOLO model loading failed: {e}")
                self.model = None
        else:
            print("YOLO not available. Install with: pip install ultralytics")

    def start_camera(self):
        """Open camera connection"""
        if self.is_running:
            return "Kamera läuft bereits."
        
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                return "Kamera konnte nicht geöffnet werden."
            
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            return "Kamera gestartet. Sage 'Pixel, was siehst du?' um Objekte zu erkennen."
        except Exception as e:
            print(f"Camera start error: {e}")
            return f"Kamerafehler: {e}"

    def stop_camera(self):
        """Close camera connection"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        return "Kamera gestoppt."

    def _detection_loop(self):
        """Background loop for object detection"""
        while self.is_running:
            if self.cap and self.model:
                ret, frame = self.cap.read()
                if ret:
                    self.frame = frame.copy()
                    try:
                        results = self.model(frame, verbose=False)
                        self.latest_objects = []
                        for result in results:
                            for box in result.boxes:
                                cls = int(box.cls[0])
                                conf = float(box.conf[0])
                                name = self.model.names[cls]
                                if conf > 0.5:
                                    self.latest_objects.append(f"{name} ({int(conf*100)}%)")
                    except Exception as e:
                        print(f"Detection error: {e}")
            time.sleep(0.1)

    def get_detected_objects(self):
        """Return list of detected objects"""
        if not self.is_running:
            return []
        return self.latest_objects

    def describe_scene(self):
        """Generate a description of what's seen"""
        if not self.is_running:
            return "Die Kamera ist nicht aktiv. Sage 'Pixel, starte Kamera' um zu beginnen."
        
        objects = self.latest_objects
        if not objects:
            return "Ich sehe momentan nichts, was ich eindeutig erkennen kann."
        
        # Count objects by type
        from collections import Counter
        # Extract names without confidence
        names = [obj.split(' (')[0] for obj in objects]
        object_counts = Counter(names)
        
        # Translation dictionary for common YOLO objects (optional, but nice for German)
        translations = {
            "person": "Person",
            "cell phone": "Handy",
            "cup": "Tasse",
            "bottle": "Flasche",
            "laptop": "Laptop",
            "keyboard": "Tastatur",
            "mouse": "Maus",
            "book": "Buch",
            "chair": "Stuhl",
            "tv": "Fernseher"
        }
        
        summary_parts = []
        for name, count in object_counts.items():
            de_name = translations.get(name, name)
            if count == 1:
                summary_parts.append(f"ein {de_name}")
            else:
                summary_parts.append(f"{count} {de_name}-Objekte")
        
        if len(summary_parts) == 1:
            return f"Ich sehe {summary_parts[0]}."
        else:
            return "Ich sehe: " + ", ".join(summary_parts[:-1]) + " und " + summary_parts[-1] + "."

    def get_frame_base64(self):
        """Get current frame as base64 for web display"""
        if self.frame is None:
            return None
        
        _, buffer = cv2.imencode('.jpg', self.frame)
        return base64.b64encode(buffer).decode('utf-8')

    def capture_image(self, filename="capture.jpg"):
        """Capture and save current frame"""
        if self.frame is None:
            return "Kein Bild verfügbar."
        
        cv2.imwrite(filename, self.frame)
        return f"Bild gespeichert als {filename}"
