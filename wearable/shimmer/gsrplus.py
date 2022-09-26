import os
import neurokit2 as nk

from datetime import datetime

from base.communication.packet import DataPacket
from base.node import TEACHINGNode

from .utils.shimmer import Shimmer3
from .utils.shimmer_util import (
    SHIMMER_GSRplus, 
    BT_CONNECTED, 
    SENSOR_GSR, 
    SENSOR_INT_EXP_ADC_CH13, 
    GSR_SKIN_CONDUCTANCE
)


class ShimmerGSRPlus(object):

    COM_PORT = '/dev/ttyS0'
    TOPIC = 'sensor.gsr.value'

    def __init__(self) -> None:
        """Initializes the Shimmer GSR+ sensor device."""

        self._sampling_rate = int(os.environ['SAMPLING_RATE'])
        self._process = os.environ['PROCESS'].lower() == 'true'

        self._device = None
        self._build()

    @TEACHINGNode(produce=True, consume=False)
    def __call__(self):
        input_fn = self._stream() 
        if self._process:
            input_fn = gsr_process(input_fn, self._sampling_rate)
        
        for timestamp, reads in input_fn:
            dp = DataPacket(
                topic=ShimmerGSRPlus.TOPIC, 
                timestamp=timestamp, 
                body=[dict(zip(reads,t)) for t in zip(*reads.values())]
            )
            print(dp)
            yield dp

    def _stream(self):
        """This generator handles the stream of PPG, EDA and timestamp data from the Shimmer sensor.

        Raises:
            RuntimeError: raised when bluetooth is not connected

        Yields:
            Iterator[Tuple[int, Dict]]: a dictionary with timestamp, PPG and EDA data.
        """        
        if self._device.current_state == BT_CONNECTED:
            self._device.start_bt_streaming()
            print("Data streaming started.")
        else:
            raise RuntimeError("Bluetooth is not connected.")

        while True:
            n, packets = self._device.read_data_packet_extended(calibrated=True)
            if n > 0:
                timestamp = []
                reads = {'ppg': [], 'eda': []}
                for pkt in packets:

                    t, ppg, eda = pkt[2], pkt[3], pkt[4]

                    timestamp.append(datetime.fromtimestamp(t))
                    reads['ppg'].append(ppg)
                    reads['eda'].append(eda)

                    yield timestamp, reads

    def _build(self):
        print("Building the Shimmer GSR+ service...")
        self._device = Shimmer3(shimmer_type=SHIMMER_GSRplus, debug=True)
        self._connect()
        print("Done!")
    
    def _connect(self) -> bool:
        """This function handles the connection via bluetooth with the Shimmer sensor.

        Args:
            port (str, optional): a string with the device path (e.g., '/dev/ttyUSB0'), 
                otherwise an input from the user is requested. Defaults to None.

        Returns:
            bool: True if  connected successfully.
        """        

        # Starting connection with the port /dev/ttyS0
        if self._device.connect(com_port=ShimmerGSRPlus.COM_PORT):
            if not self._device.set_sampling_rate(self._sampling_rate):
                return False
            # After the connection we want to enable GSR and PPG
            if not self._device.set_enabled_sensors(SENSOR_GSR, SENSOR_INT_EXP_ADC_CH13):
                return False
            # Set the GSR measurement unit to Skin Conductance (micro Siemens)
            if not self._device.set_active_gsr_mu(GSR_SKIN_CONDUCTANCE):
                return False
            
            print(f"Shimmer GSR+ connected to {ShimmerGSRPlus.COM_PORT}.")
            self._device.print_object_properties()
            return True

        return False
    
    def _disconnect(self) -> bool:
        """Disconnects the Shimmer sensor.

        Returns:
            bool: True if disconnected successfully.
        """        
        if not self._device.current_state == BT_CONNECTED:
            self._device.disconnect(reset_obj_to_init=True)
            return True
        else:
            return False



def gsr_process(stream, sampling_rate: int = 64):
    """This generator processes the stream data from the Shimmer GSR+, aggregating samples for a seconds_per_return
    timespan and processing PPG to HR.

    Args:
        stream: the device stream function
        sampling_rate: the sampling rate of the Shimmer GSR+

    Yields:
        dict: a dictionary containing the timestamp, HR and EDA of the processed sample
    """
    min_threshold = int(os.getenv('WINDOW_SIZE', '20')) * sampling_rate
    ppg_buffer, eda_buffer = [], []
    for timestamp, reads in stream:
        ppg_buffer += reads['ppg']
        eda_buffer += reads['eda']
        offset = len(ppg_buffer) - min_threshold
        if offset > 0:
            print(offset, len(ppg_buffer))
            ppg_df, _ = nk.ppg_process(ppg_buffer, sampling_rate=sampling_rate)
            heart_rate = ppg_df['PPG_Rate'].values.tolist()

            eda_df, _ = nk.eda_process(eda_buffer, sampling_rate=sampling_rate)
            eda, eda_tonic, eda_phasic = \
                eda_df['EDA_Clean'].values.tolist(), \
                eda_df['EDA_Tonic'].values.tolist(), \
                eda_df['EDA_Phasic'].values.tolist()

            timestamp = timestamp[-offset:]
            to_publish = {
                'hr': heart_rate[-offset:],
                'eda': eda[-offset:],
                'eda_tonic': eda_tonic[-offset:],
                'eda_phasic': eda_phasic[-offset:]
            }

            ppg_buffer, eda_buffer = ppg_buffer[offset:], eda_buffer[offset:]
            assert len(ppg_buffer) == min_threshold

            yield timestamp, to_publish
