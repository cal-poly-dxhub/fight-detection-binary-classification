# import cv2
# cap = cv2.VideoCapture("rtsp://192.168.1.61:554/live1.sdp")

# while(cap.isOpened()):
#     ret, frame = cap.read()
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(20) & 0xFF == ord('q'):
#         break
# cap.release()
# cv2.destroyAllWindows()

# ####
import cv2

# Replace the URL with your camera's RTSP stream URL
rtsp_url = "rtsp://192.168.1.61:554/live1.sdp"

# Create a VideoCapture object to connect to the camera
#cap = cv2.VideoCapture(rtsp_url)

# Check if the camera is connected
if not cap.isOpened():
    print("Failed to connect to camera")
else:
    # Loop to read frames from the camera
    while True:
        ret, frame = cap.read()
        if ret:
            # Display the frame
            cv2.imshow("Camera Feed", frame)
            
            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            # Failed to read frame from the camera
            print("Failed to read frame from camerqa")
            break

# Release the VideoCapture object and destroy the OpenCV window
cap.release()
cv2.destroyAllWindows()
