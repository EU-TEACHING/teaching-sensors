import threading
from time import time
from vidgear.gears import WriteGear,VideoGear,CamGear,StreamGear

output_params = {
    "-preset:v": "veryfast",
    "-tune" : "zerolatency", 
    "-g": 60,
    "-sc_threshold": 0,
    "-bufsize": "2500",
    "-f": "flv",
    "-input_framerate":30
    }
stream_params = {"-input_framerate": 1,
                "-livestream": True ,
                "-f": "flv",
                "-flvflags" : 'no_duration_filesize'}

class VideoFeed:
    
    def __init__(self, rtmp_server=None, rtmp_topic=None, source=None, record=False):
        self.topic = rtmp_topic 
        self.stream = None                       
        if source is not None:            
            if 'camera_' in source:
                source = int(source.split('_'))
                self.stream = CamGear(source=source).start()
            else:
                self.stream = VideoGear(source=source).start()           
       
        self.rtmp_server = rtmp_server
        if rtmp_server is not None:
            self.stream_url = f'rtmp://{rtmp_server}/live/{rtmp_topic}'
            self.streamer =  StreamGear(output=self.stream_url, **stream_params)
        #if record:
            #self.writer = WriteGear(output_filename=self.stream_url,logging=True,**output_params)

    def __call__(self):
        thread = threading.Thread(target=self.start_streaming)
        thread.start()
        rmtp_report = {'topic': self.topic, 'body': f'rtmp://{self.rtmp_server}/live/{self.topic}'}  
        while True:
            yield rmtp_report  
            time.sleep(0.001)

    def push_frame(self,frame):
        #self.writer.write(frame)
        self.streamer.stream(frame)

    def get_frame(self):
        #method works only to push opencv frame to rtmp
        frame = self.stream.read()
        return frame
    
    def start_streaming(self):
        #method for continues stream from source
        while True:
            frame = self.stream.read()
            if frame is None:
                break
            self.push_frame(frame)
            
    def stop(self):
        if self.stream is not None:  
            self.stream.stop()
        if self.rtmp_server is not None: 
            #self.writer.close()
            self.streamer.terminate()
