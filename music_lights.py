__author__ = 'Sonali'

import wave
from mingus.extra import fft
import collections
from phue import Bridge
import time
import subprocess


notes_hues_dict = {'C': 824,
                   'C#': 3824,
                   'D': 7824,
                   'D#': 12824,
                   'E': 17824,
                   'F': 22824,
                   'F#': 27824,
                   'G': 39824,
                   'G#': 42824,
                   'A': 47824,
                   'A#': 51824,
                   'B': 57824
                    }

which_file = '/Users/Sonali/lm.wav' #raw_input('Type .wav file path: ')
number_of_lights = 3
hue_bridge_ip = '192.168.42.87'


def mono_only(wavfile):
    """
    Opens a .wav file and checks whether the file is mono or stereo. If stereo, the two channels are averaged
    into one, and a mono .wav file is returned.
    """
    open_wav = wave.open(wavfile, 'r')
    wav_channels = open_wav.getnchannels()
    file_mono = open_wav
    if wav_channels != 1:
        open_wav = wave.open(wavfile)
        wav_frames = open_wav.getnframes()
        wav_read = open_wav.readframes(wav_frames)
        wavpairs = zip(wav_read[::2], wav_read[1::2])
        wav_right = wavpairs[1::2]
        wav_left = wavpairs[0::2]
        #average_wav = (wav_left + wav_right) / 2
        file_mono = wav_left
    return file_mono


def wav_data(mono_wav):
    """
    Opens the mono .wav file and extracts data. Returns a tuple with a list of data, frequency and bits.
    """
    the_data = fft.data_from_file(mono_wav)
    return the_data


def wav_frames(wav_file):
    """
    Opens the mono .wav file and extracts data. Calculates and returns the number of seconds in the song.
    """
    wave_reading = wave.open(wav_file)
    samp_frames = wave_reading.getnframes()
    frame_rate = wave_reading.getframerate()
    seconds = samp_frames/frame_rate
    return seconds


def wav_len(wav_data, seconds):
    """
    Takes in the data from wav_data and the number of seconds in the song. Calculates size of chunk per second.
    """
    data_info, frequency, bits = wav_data
    data_length = len(data_info)
    chunk_size = 3 * data_length/seconds
    return chunk_size


def chunks(data_list, chunk_size):
    """
    Takes in list of data and size of chunks to separate list into chunks for each second of sound.
    """
    data_info, frequency, bits = data_list

    some_data_list = []
    for i in range(0, len(data_info), chunk_size):
        some_data_list.append(data_info[i:i+chunk_size])
    return some_data_list


def note_conversion(the_chunks):
    """
    Takes in the one-second chunks of data. For each chunk, frequency tables are created;
    all notes and their amplitudes are found and returned.
    """

    chunk_list = []
    for one_chunk in the_chunks[:]:
        the_freq = fft.find_frequencies(one_chunk)
        the_notes = fft.find_notes(the_freq)
        chunk_list.append(the_notes)
    return chunk_list


def notes_map(notes_list):
    """
    Takes in the list of notes and their amplitudes. Removes the octave associated with each note and combines
    each note from all octaves together. Creates and returns a dictionary with notes and amplitudes.
    """
    find_notes = []
    for each_list in notes_list:
        each_list.pop()
        key_map = {}
        for note, value in each_list[:]: #loop through the result list
            key_map[note.name] = key_map.get(note.name, 0) + value
        find_notes.append(key_map)
    return find_notes


def counter_for_note_map(notes_map):
    top_notes_list = []
    for dictionary in notes_map:
        top_notes = collections.Counter(dictionary).most_common(number_of_lights)
        top_notes_list.append(top_notes)
    return top_notes_list


def note_to_color(map_of_note_counter):
    command =  {'transitiontime' : 10, 'on' : True, 'sat' : 255, 'hue':57824}
    b.set_light(range(1, number_of_lights+1), command)
    b.set_light(range(1, number_of_lights+1), 'bri', 255)

    subprocess.Popen(('afplay', which_file))

    for one_note_map in map_of_note_counter:
        for index, (note, amp) in enumerate(one_note_map):
            light_color = notes_hues_dict[note]
            change_command = {'transitiontime': 28, 'hue': light_color}
            b.set_light(index + 1, change_command)
        time.sleep(2.9)
    off_command = {'transitiontime': 10, 'on': False}
    b.set_light(range(1, number_of_lights+1), off_command)


b = Bridge(hue_bridge_ip)

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
b.get_api()


new_file = mono_only(which_file)
file_data = wav_data(which_file)
file_time = wav_frames(which_file)
size_chunks = wav_len(file_data, file_time)
the_chunks = chunks(file_data, size_chunks)
find_notes = note_conversion(the_chunks)
map_of_notes = notes_map(find_notes)
map_of_note_counter = counter_for_note_map(map_of_notes)
turn_on_lights = note_to_color(map_of_note_counter)

