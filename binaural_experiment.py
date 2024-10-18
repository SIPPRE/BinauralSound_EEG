"""
Title: Binaural Sound Experiment Using Enophones

Developed by: SIPPRE Group, Electrical & Computer Engineering Department, University of Peloponnese
Contact: Koutras Athanasios, koutras@uop.gr

License: 
This program is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).
You are free to:
    - Share: copy and redistribute the material in any medium or format
    - Adapt: remix, transform, and build upon the material for any purpose, even commercially.
Under the following terms:
    - Attribution: You must give appropriate credit, provide a link to the license, and indicate if changes were made. 
      You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
    - No additional restrictions: You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.
For more details, see https://creativecommons.org/licenses/by/4.0/

Description:
This script conducts a binaural experiment using Enophone headsets. 
It collects EEG data from the headsets, plays a series of songs with relaxation periods between them, 
and logs the data along with markers indicating the different stages of the experiment. 
All songs should be stored in a separate directory songs/ using filenames of type (song001.mp3, song002.mp3, ...).
Feel free to modify according to your preferences.
The data is saved both as a CSV file and in MNE FIF format.

Experiment Protocol:
1. The subject sits and relaxes with eyes closed for a predefined relaxation period (default: 5 seconds).
2. The subject listens to a song for a predefined duration (default: 15 seconds).
3. The subject relaxes again with eyes closed for a predefined pause period (default: 5 seconds).
4. Steps 2-3 are repeated for a predefined number of songs (default: 2 songs).
5. Markers are inserted at each stage to indicate the start and end of relaxation, start and end of songs, and the end of the experiment.

Markers Used:
- Marker 1: Start of relaxation
- Marker 3: Start of song
- Marker 5: Start of experiment
- Marker 6: End of experiment

Example of how to run the program:
    python binaural_experiment_withsave.py --mac-address <MAC_ADDRESS> --subject <SUBJECT_ID>

Arguments:
    --mac-address : The MAC address of the Enophone headset (optional for Windows, MAC - required for Linux)
    --subject     : The ID of the subject participating in the experiment (required)
"""

# Global Variables for Experiment Configuration

relax_duration = 30  # Duration for the relax period (seconds)
song_duration = 120  # Duration for each song (seconds)
pause_duration = 30  # Duration for the pause between songs (seconds)
num_songs = 5  # Number of songs in the experiment
song_directory = './songs'  # Directory where songs are stored
sleep_time = 0.5  # Delay to proceed from one state to the other in the experiment (no need to change this)

import sys
import time
import logging
import argparse
import os
import datetime
import csv
import numpy as np
import pandas as pd
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds, BrainFlowError
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5 import QtCore
import pyqtgraph as pg
import pygame
import enotools
from PyQt5.QtCore import QThread, pyqtSignal
import mne

logging.basicConfig(filename='experiment.log', level=logging.DEBUG) # change this accordingly to set the level of logging 

class Graph(QWidget):
    def __init__(self, board_shim, subject_id):
        super().__init__()
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.subject_id = subject_id  # Store the subject ID
        self.exg_channels = BoardShim.get_eeg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 10
        self.num_points = self.window_size * self.sampling_rate
        self.plot_names = ['Quality A2', 'Quality A1', 'Quality C4', 'Quality C3']
        self.mains = None
        self.initUI()
        self.show()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.update_speed_ms)


    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Live Enophone Data')

        layout = QVBoxLayout()
        self.plot_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.plot_widget)

        self.start_button = QPushButton('Start Experiment', self)
        self.start_button.clicked.connect(self.start_experiment)
        layout.addWidget(self.start_button)

        self.setLayout(layout)
        self._init_timeseries()

        self.showFullScreen()

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        self.legends = list()

        for i in range(len(self.exg_channels)):
            p = self.plot_widget.addPlot(row=i, col=0)
            legend = p.addLegend(brush='k')
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            p.setYRange(-100, 100, padding=0)
            if i == 0:
                p.setTitle('Live Enophone Data')
            self.plots.append(p)
            curve = p.plot(name=self.plot_names[i])
            self.curves.append(curve)
            self.legends.append(legend)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)

        if data.shape[1] > 3 * self.sampling_rate:
            if self.mains is None:
                self.mains = enotools.detect_mains(data)
            quality = enotools.quality(data)
            data = enotools.referencing(data, mode='mastoid')
            data = enotools.signal_filtering(data, filter_cut=250, bandpass_range=[3, 40], bandstop_range=self.mains)

            for count, channel in enumerate(self.exg_channels):
                name = self.plot_names[count] + ': ' + str(quality[count])
                self.curves[count].setData(data[channel].tolist())
                self.legends[count].getLabel(self.curves[count]).setText(name)
                if quality[count] >= 99:
                    self.legends[count].setLabelTextColor('g')
                elif quality[count] >= 95:
                    self.legends[count].setLabelTextColor('y')
                else:
                    self.legends[count].setLabelTextColor('r')

            # Save data to CSV (chunks of data - no need to do it now, this is for saving on the fly)
            #board_id = self.board_shim.get_board_id()
            #timestamps = data[BoardShim.get_timestamp_channel(board_id)]
            #markers = data[BoardShim.get_marker_channel(board_id)].astype(int)
            #human_readable_timestamps = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f') for ts in timestamps]
            #eeg_data = [data[channel] for channel in self.exg_channels]
            #combined_data = zip(timestamps, human_readable_timestamps, *eeg_data, markers)

            #for row in combined_data:
            #    self.csv_writer.writerow(row)
            #    #logging.debug(f"Row written to CSV: {row}")

            #self.csv_file.flush()

    def start_experiment(self):
        self.timer.stop()
        self.close()
        self.experiment_window = ExperimentWindow(self.board_shim, self.subject_id)
        self.experiment_window.show()
        self.experiment_window.run_experiment()

    def closeEvent(self, event):
        #self.csv_file.close() #only if saving real time  chunks of data
        super().closeEvent(event)

class ExperimentWorker(QThread):
    finished = pyqtSignal()
    update_message = pyqtSignal(str, int)

    def __init__(self, board_shim, relax_duration, song_duration, pause_duration, num_songs, sleep_time, song_directory):
        super().__init__()
        self.board_shim = board_shim
        self.relax_duration = relax_duration
        self.song_duration = song_duration
        self.pause_duration = pause_duration
        self.num_songs = num_songs
        self.sleep_time = sleep_time
        self.song_directory = song_directory

    def run(self):
        try:
  
            self.board_shim.insert_marker(5)  # Start of experiment
            logging.debug("Inserted marker 5 (Start of experiment)")
            time.sleep(sleep_time)
            
            self.update_message.emit("Relax with eyes closed", relax_duration)
            self.board_shim.insert_marker(1)
            logging.debug("Inserted marker 1 (Start of relaxation)")
            time.sleep(relax_duration)
            time.sleep(sleep_time)

            #self.board_shim.insert_marker(2)
            #logging.debug("Inserted marker 2 (End of relaxation)")
            #time.sleep(sleep_time)
            
            for i in range(num_songs):
                song_path = f'{song_directory}/song{i + 1:03d}.mp3'
                if not os.path.exists(song_path):
                    raise FileNotFoundError(f"Song file not found: {song_path}")

                self.update_message.emit(f"Song {i + 1}", song_duration)
                self.board_shim.insert_marker(3)
                logging.debug(f"Inserted marker 3 (Start of song {i + 1})")
                
                self.play_song(song_path, song_duration)
                #self.board_shim.insert_marker(4)
                #logging.debug(f"Inserted marker 4 (End of song {i + 1})")
                time.sleep(sleep_time)

                self.update_message.emit("Relax", pause_duration)
                self.board_shim.insert_marker(1)
                logging.debug("Inserted marker 1 (Start of relaxation)")
                time.sleep(pause_duration)
                time.sleep(sleep_time)
                #self.board_shim.insert_marker(2)
                #logging.debug("Inserted marker 2 (End of relaxation)")

        except Exception as e:
            logging.error(f"Error in experiment: {e}")
        finally:
            self.update_message.emit("Experiment Complete", 5)
            self.finished.emit()

    def play_song(self, song_path, duration):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()
            time.sleep(duration)
            pygame.mixer.music.stop()
        except Exception as e:
            logging.error(f"Error playing song: {e}")



class ExperimentWindow(QWidget):
    def __init__(self, board_shim, subject_id):
        super().__init__()
        self.board_shim = board_shim
        self.subject_id = subject_id
        self.initUI()

        self.worker = ExperimentWorker(board_shim, relax_duration, song_duration, pause_duration, num_songs, sleep_time, song_directory)
        self.worker.update_message.connect(self.show_message)
        self.worker.finished.connect(self.experiment_finished)

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Experimental Protocol')

        layout = QVBoxLayout()
        self.label = QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("font: 40pt;")  # Define font size for the messages
        layout.addWidget(self.label)

        self.setLayout(layout)
        self.showFullScreen()  # Make the window full screen

    def show_message(self, message, duration):
        self.label.setText(message)
        QtCore.QTimer.singleShot(duration * 1000, self.clear_message)

    def clear_message(self):
        self.label.setText("")

    def run_experiment(self):
        self.worker.start()

    def experiment_finished(self):
        self.board_shim.insert_marker(6)  # End of experiment
        logging.debug("Inserted marker 6 (End of experiment)")
        time.sleep(sleep_time)

        self.close()
        board_id = self.board_shim.get_board_id()
        data = self.board_shim.get_board_data()  # Get all data - the experiment has ended

        #should pre-process the data before storing them
        mains = enotools.detect_mains(data)
        data = enotools.referencing(data, mode='mastoid')
        data = enotools.signal_filtering(data, filter_cut=250, bandpass_range=[0.1, 45], bandstop_range=mains)

        # Log the marker values
        markers = data[BoardShim.get_marker_channel(board_id)]
        logging.debug(f"Markers retrieved: {markers}")

        # Save final data to CSV to use later in any analysis program of choice 
        timestamps = data[BoardShim.get_timestamp_channel(board_id)]
        markers = data[BoardShim.get_marker_channel(board_id)].astype(int)
        human_readable_timestamps = [datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f') for ts in timestamps]
        eeg_data = [data[channel] for channel in BoardShim.get_eeg_channels(board_id)]
        combined_data = zip(timestamps, human_readable_timestamps, *eeg_data, markers)

        output_csv_filename = f'{self.subject_id}_eeg_data.csv'
        output_fif_filename = f'{self.subject_id}_eeg_data.raw.fif'
        
        with open(output_csv_filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            header = ['Unix Timestamp', 'Human Readable Timestamp'] + [f'EEG Channel {ch}' for ch in BoardShim.get_eeg_channels(board_id)] + ['Marker']
            csv_writer.writerow(header)
            for row in combined_data:
                csv_writer.writerow(row)
                #logging.debug(f"Final row written to CSV: {row}")

        logging.info("Experiment finished and data saved to <subjectID>_eeg_data.csv")

        # this is to construct the MNE data format since it is the nicest analysis software!!
        # Get EEG and Marker Channel Data
        eeg_channels = BoardShim.get_eeg_channels(board_id)
        stim_channel = BoardShim.get_marker_channel(board_id)
        mne_eeg_data = data[eeg_channels, :] / 1000000 #brainflow data are uV, MNE wants that in V
        marker_data = data[stim_channel, :]

        # Combine EEG and Marker Data
        combined_data = np.vstack([mne_eeg_data, marker_data])

        # Create Channel Types and Names
        ch_types = ['eeg'] * len(eeg_channels) + ['stim']
        ch_names = BoardShim.get_eeg_names(board_id) + ['stim']

        # Create MNE Info Object
        sfreq = BoardShim.get_sampling_rate(board_id)
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)

        # Create RawArray Object
        raw = mne.io.RawArray(combined_data, info)

        # Save to FIF File
        raw.save(output_fif_filename, overwrite=True)

def main():
    BoardShim.enable_dev_board_logger()

    # Configure BrainFlow logging to redirect to a file so as not to overwhelm the console
    BoardShim.set_log_file('brainflow.log')
    BoardShim.set_log_level(LogLevels.LEVEL_INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='F4:0E:11:75:94:24')
    parser.add_argument('--subject', type=str, help='subject ID', required=True) 
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.mac_address = args.mac_address

    try:
        board_shim = BoardShim(BoardIds.ENOPHONE_BOARD, params)

        # Prepare session and start data streaming
        board_shim.prepare_session()
        board_shim.start_stream()

        # Create a single QApplication instance
        app = QApplication(sys.argv)

        # Start Graph window
        graph = Graph(board_shim, args.subject)
        graph.show()

        # Run the application
        app.exec_()  # Here's the correction: use app.exec_()

        # Stop the stream and release the session when the graph window is closed
        board_shim.stop_stream()
        board_shim.release_session()
    
    except BrainFlowError as e:
        print(f"\n\nError: Unable to start streaming session. Please check if the Enophone headset is connected and try again.\nTechnical details: {e}\n\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
