import os
import time
from PIL import Image
from base.node import TEACHINGNode
from base.communication.packet import DataPacket

class CameraFeed:
    
    def __init__(self):
        self.img_path = "/app/storage/current_img.jpg"
        self._output_topic = os.environ['OUTPUT_TOPIC']
        self._capture_delay = float(os.environ['CAPTURE_DELAY'])
        self._build()

    @TEACHINGNode(produce=True, consume=False)
    def __call__(self):

        while True:

            ### create still image from camera and load it
            # os.system("libcamera-still -n -o {} --vflip --hflip".format(self.img_path))
            #
            while True:
                if not os.path.exists(self.img_path):
                    print("path does not exists!")
                    time.sleep(0.1)
                else:
                    break
            img = Image.open(self.img_path)
            print("Picture captured!")
            ### send package
            yield DataPacket(topic=self._output_topic, body={'img': img})

            ### add delay
            time.sleep(self._capture_delay)

    def _build(self):

        print("Starting RPI Camera Module Service...")
        pass
