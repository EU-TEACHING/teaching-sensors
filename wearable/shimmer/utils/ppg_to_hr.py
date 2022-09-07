import neurokit2 as nk


class PPGtoHR(object):

    def __init__(self, sampling_rate: int=64):
        """This object processes the stream data from the Shimmer GSR+, aggregating samples for a seconds_per_return
        timespan and processing PPG to HR.

        Args:
            sampling_rate: the sampling rate of the device
        """

        self._sampling_rate = sampling_rate
        self._min_threshold =  5 * sampling_rate

    def __call__(self, stream):
        """This generator processes the stream data from the Shimmer GSR+, aggregating samples for a seconds_per_return
        timespan and processing PPG to HR.

        Args:
            stream: the device stream function

        Yields:
            dict: a dictionary containing the timestamp, HR and EDA of the processed sample
        """
        ppg_buffer = []
        
        for n, reads in stream:
            if n > 0:
                ppg_buffer += reads['ppg']

            offset = len(ppg_buffer) - self._min_threshold
            if offset > 0:
                ppg_df, _ = nk.ppg_process(ppg_buffer, sampling_rate=self._sampling_rate)
                to_publish = {
                    'timestamp': reads['timestamp'][-offset:],
                    'hr': ppg_df['PPG_Rate'].values.tolist()[-offset:],
                    'eda': reads['eda'][-offset:]
                }

                ppg_buffer = ppg_buffer[offset:]
                assert len(ppg_buffer) == self._min_threshold
                yield to_publish
