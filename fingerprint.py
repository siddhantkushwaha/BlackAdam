import hashlib
from operator import itemgetter

import numpy as np
import matplotlib.mlab as mlab
from pydub import AudioSegment

from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import generate_binary_structure, iterate_structure, binary_erosion

IDX_FREQ_I = 0
IDX_TIME_J = 1
DEFAULT_FS = 44100
DEFAULT_WINDOW_SIZE = 4096
DEFAULT_OVERLAP_RATIO = 0.5
DEFAULT_FAN_VALUE = 15
DEFAULT_AMP_MIN = 10
PEAK_NEIGHBORHOOD_SIZE = 20
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200
PEAK_SORT = True
FINGERPRINT_REDUCTION = 20


def process(audio_segment: AudioSegment):
    data = np.frombuffer(audio_segment._data, np.int16)

    channels = []
    for chn in range(audio_segment.channels):
        channels.append(data[chn::audio_segment.channels])

    frame_rate = audio_segment.frame_rate

    result = set()
    for channel_num, channel in enumerate(channels):
        hashes = fingerprint(channel, frame_rate)
        result |= set(hashes)

    return result


def fingerprint(channel_samples, Fs=DEFAULT_FS, wsize=DEFAULT_WINDOW_SIZE, wratio=DEFAULT_OVERLAP_RATIO,
                fan_value=DEFAULT_FAN_VALUE, amp_min=DEFAULT_AMP_MIN):
    arr2d = mlab.specgram(
        channel_samples,
        NFFT=wsize,
        Fs=Fs,
        window=mlab.window_hanning,
        noverlap=int(wsize * wratio))[0]

    arr2d = 10 * np.log10(arr2d)
    arr2d[arr2d == -np.inf] = 0

    # find local maxima
    local_maxima = get_peaks(arr2d, amp_min=amp_min)

    # return hashes
    return generate_hashes(local_maxima, fan_value=fan_value)


def get_peaks(arr2d, amp_min=DEFAULT_AMP_MIN):
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)

    # find local maxima using our filter shape
    local_max = maximum_filter(arr2d, footprint=neighborhood) == arr2d
    background = (arr2d == 0)
    eroded_background = binary_erosion(background, structure=neighborhood, border_value=1)

    # Boolean mask of arr2D with True at peaks (Fixed deprecated boolean operator by changing '-' to '^')
    detected_peaks = local_max ^ eroded_background

    # extract peaks
    amps = arr2d[detected_peaks]
    j, i = np.where(detected_peaks)

    # filter peaks
    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = filter(lambda tup: tup[2] > amp_min, peaks)  # freq, time, amp

    # get indices for frequency and time
    frequency_idx = []
    time_idx = []
    for x in peaks_filtered:
        frequency_idx.append(x[1])
        time_idx.append(x[0])

    return list(zip(frequency_idx, time_idx))


def generate_hashes(peaks, fan_value=DEFAULT_FAN_VALUE):
    if PEAK_SORT:
        peaks = sorted(peaks, key=itemgetter(1))

    hashes = set()
    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if (i + j) < len(peaks):

                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]
                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]
                t_delta = t2 - t1

                if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                    hash_string = f'{freq1}_{freq2}_{t_delta}'
                    h = hashlib.sha1(hash_string.encode('utf-8'))
                    hashes.add((h.hexdigest()[0:FINGERPRINT_REDUCTION], t1))

    return hashes
