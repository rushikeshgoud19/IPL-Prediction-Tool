import cv2
import numpy as np
from ultralytics import YOLO

class CricketVisionTracker:
    def __init__(self, model_path='yolov8n.pt'):
        # Initialize YOLOv8 (using nano for speed, you can upgrade to pose/custom models)
        self.model = YOLO(model_path)
        # Class indices might vary, typically person=0, sports ball=32 in COCO
        self.PERSON_CLASS = 0
        self.BALL_CLASS = 32
        
        self.ball_trajectory = []
        self.release_point = None

    def process_stream(self, stream_url):
        # For testing, you can use an MP4 file path instead of URL
        cap = cv2.VideoCapture(stream_url)
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            # Run YOLOv8 inference
            results = self.model(frame, classes=[self.PERSON_CLASS, self.BALL_CLASS], conf=0.25)
            
            # Extract boxes
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    xyxy = box.xyxy[0].cpu().numpy()
                    
                    # Draw Bounding Boxes
                    if cls == self.PERSON_CLASS:
                        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 0, 0), 2)
                        cv2.putText(frame, "Batter/Bowler", (int(xyxy[0]), int(xyxy[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    elif cls == self.BALL_CLASS:
                        # Ball tracking
                        center_x = int((xyxy[0] + xyxy[2]) / 2)
                        center_y = int((xyxy[1] + xyxy[3]) / 2)
                        self.ball_trajectory.append((center_x, center_y))
                        
                        cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 0, 255), 2)
                        
                        # If this is the start of trajectory, mark as release point
                        if len(self.ball_trajectory) == 5: # Arbitrary heuristic for release
                            self.release_point = (center_x, center_y)
            
            # Delivery classification logic based on release and pitch bounce coordinates
            delivery_type = self.classify_delivery()
            if delivery_type:
                cv2.putText(frame, f"Delivery: {delivery_type}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("IPL Live Feed Analysis", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

    def classify_delivery(self):
        if not self.release_point or len(self.ball_trajectory) < 15:
            return None
        
        # Heuristic: Analyze the vertical drop (y-coordinate change) to determine type
        y_coords = [pt[1] for pt in self.ball_trajectory]
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        bounce_depth = max_y - self.release_point[1]
        
        if bounce_depth > 200:
            return "Yorker"
        elif bounce_depth < 50:
            return "Bouncer"
        else:
            return "Good Length"

if __name__ == "__main__":
    print("Starting Vision Pipeline...")
    tracker = CricketVisionTracker()
    # Replace with your actual stream URL or test video file
    # tracker.process_stream("http://example.com/live_stream.m3u8")
    print("Uncomment tracker.process_stream() to run with a video source.")
