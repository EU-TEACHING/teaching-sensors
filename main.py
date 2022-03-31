import os

from base.node import TEACHINGNode

def get_service_fn():
    service_type = os.getenv('SERVICE_TYPE')
    producer, consumer = True, False

    service_fns = []
    if service_type == 'GSR':
        from wearable.shimmer import ShimmerGSRPlus
        sampling_rate = int(os.getenv('SAMPLING_RATE', '64'))
        gsr = ShimmerGSRPlus(sampling_rate)
        gsr.connect()
        service_fns.append(gsr)

        if bool(os.getenv('PROCESS', 'False')):
            from wearable.shimmer import PPGtoHR
            ppg_to_hr = PPGtoHR(sampling_rate)
            service_fns.append(ppg_to_hr)

    if service_type == 'VIDEO':
        from video import VideoFeed
        rtmp_server = os.getenv('RTMP_SERVER')
        rtmp_topic = os.getenv('RTMP_TOPIC')
        video_source = os.getenv('VIDEO_SOURCE')
        v_feed = VideoFeed(rtmp_server, rtmp_topic, video_source)

        service_fns.append(v_feed)
    
    if service_type == 'CSV':
        from file import CSVFeed
        file_path = os.path(os.getenv('FILE_PATH'))
        transmit_rate = int(os.getenv('TRANSMIT_RATE'))
        csv_feed = CSVFeed(file_path, transmit_rate)
        
        service_fns.append(csv_feed)

    return service_fns, producer, consumer


if __name__ == '__main__':
    service_fns, producer, consumer = get_service_fn
    node = TEACHINGNode(service_fns, producer, consumer)
    node.build()
    node.start()
