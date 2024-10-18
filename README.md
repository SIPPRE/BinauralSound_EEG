# Enophone Music Experiment

This project is designed to conduct experiments using the Enophone headset to record EEG signals while subjects listen to music. The program streams and records EEG data, displays it in real-time, and manages experimental protocols including displaying messages and playing songs.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Experiment Protocol](#experiment-protocol)
- [Data Saving](#data-saving)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Installation

To run this project, ensure you have the following dependencies installed:

- Python 3.7+
- BrainFlow
- PyQt5
- pyqtgraph
- pygame
- numpy
- pandas
- mne

You can install the required packages using the following command:

```bash
pip install -r requirements.txt
```

## Usage

To start the experiment, run the following command:

```bash
python binaural_experiment.py --mac-address <MAC_ADDRESS> --subject <SUBJECT_ID>
```

Replace `<MAC_ADDRESS>` with the MAC address of your Enophone headset and `<SUBJECT_ID>` with the identifier for the subject.

### Quitting the Program

You can quit the program at any time by pressing the `q` key (to be updated soon).

## Experiment Protocol

1. **Initial Relaxation with Eyes Closed (1 minute):**
   - The subject sits with eyes closed.
   - A message is displayed indicating the start and end of this period.
   - Marker 1 is inserted at the start and marker 2 at the end.

2. **Music Listening Session:**
   - The subject listens to a 30-second segment of a song.
   - A message indicating the song number is displayed.
   - Marker 3 is inserted at the start and marker 4 at the end.
   - After the song, the subject relaxes for 10 seconds before the next song.
   - Marker 1 is inserted at the start and marker 2 at the end of the relaxation period.
   - This process is repeated for 5 songs in total.

3. **End of Experiment:**
   - Marker 6 is inserted at the end of the experiment.

## Data Saving

Data is saved in two formats:

1. **CSV File:**
   - EEG data, timestamps, and markers are saved in a CSV file named `<SUBJECT_ID>_eeg_data.csv`.

2. **MNE FIF File:**
   - Data is also saved in MNE's FIF format for further analysis, named `<SUBJECT_ID>_eeg_data.raw.fif`.

## File Structure

```
.
├── binaural_experiment.py     # Main experiment script
├── enotools.py                # Utility functions for signal processing
├── requirements.txt           # Python package requirements
└── songs/                     # Directory containing song files
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

Developed by SIPPRE Group, Electrical & Computer Engineering Department, University of Peloponnese.
Contact: Koutras Athanasios - [koutras@uop.gr](mailto:koutras@uop.gr)
