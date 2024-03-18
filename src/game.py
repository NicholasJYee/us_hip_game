import random
import time
import csv
import os
import copy
import pydicom
import numpy

from PIL import Image


class Game:
    def __init__(self):
        # Randomly select a pig, hip laterality, and bone status
        self.pig = random.choice([
            '10013'
        ])
        self.laterality = random.choice(['left', 'right'])
        self.image_location = random.choice([
            'data/dissect',
            'data/frac',
        ])
        self.status = self.image_location.split('/')[-1]
        # Assign image files that contain the text self.laterality and self.pig
        self.image_files = [filename for filename in os.listdir(self.image_location) if self.laterality in filename and self.pig in filename]
        
        # Initialize game board
        self.board = [['' for _ in range(5)] for _ in range(8)]
        self.current_position = {
            'row': random.randint(0, 7),
            'col': random.randint(0, 4),
            'probe_orientation': random.choice(['long', 'trans']),
            'probe_angle': 'neu'
        }
        self.actions = []
        
        self.last_action_time = time.time()

    def handle_keypress(self, key):
        # Save the previous position
        previous_position = copy.deepcopy(self.current_position)
        # Move the probe based on the key pressed
        if key == 'w':
            action = 'up'
            self.move('up')
        elif key == 'a':
            action = 'left'
            self.move('left')
        elif key == 's':
            action = 'down'
            self.move('down')
        elif key == 'd':
            action = 'right'
            self.move('right')
        elif key == 'q' or key == 'e':
            action = 'switch probe orientation'
            self.switch_probe_orientation()
        elif key == 'g':
            action = 'end game'
        else:
            action = key
        
        # Record the action and time taken given the previous image
        self.save(previous_position, action)
        
        # Return the image path based on the key pressed
        if key == 'w' or key == 'a' or key == 's' or key == 'd' or key == 'q' or key == 'e':
            image_path = self.get_current_image_path()
            return image_path
        else:
            return None
        
    def get_current_image_path(self):
        # Convert row and col to the corresponding grid number (starts from 1)
        grid_number = str((self.current_position['row'] * 5 + self.current_position['col'] + 1)).zfill(3)
        
        # Determine file name from the probe orientation then open the image
        for filename in self.image_files:
            if grid_number in filename and self.current_position['probe_orientation'] in filename and self.current_position['probe_angle'] in filename:
                return f'{self.image_location}/{filename}'
        return None

    def display_image(self):
        # Convert row and col to the corresponding grid number (starts from 1)
        grid_number = str((self.current_position['row'] * 5 + self.current_position['col'] + 1)).zfill(3)
        
        # Determine file name from the probe orientation then open the image
        for filename in self.image_files:
            if grid_number in filename and self.current_position['probe_orientation'] in filename and self.current_position['probe_angle'] in filename:
                # Open dicom file and display the image without opening a new application
                image_path = f'{self.image_location}/{filename}'
                ds = pydicom.dcmread(image_path)
                img = Image.fromarray(ds.pixel_array)
                img.show()
                break    
        
    def move(self, direction):
        if direction == 'up' and self.current_position['row'] > 0:
            self.current_position['row'] = self.current_position['row'] - 1
        elif direction == 'down' and self.current_position['row'] < 7:
            self.current_position['row'] = self.current_position['row'] + 1
        elif direction == 'left' and self.current_position['col'] > 0:
            self.current_position['col'] = self.current_position['col'] - 1
        elif direction == 'right' and self.current_position['col'] < 4:
            self.current_position['col'] = self.current_position['col'] + 1

    def save(self, previous_position, action):
        print(previous_position)
        self.actions.append((previous_position, action, time.time() - self.last_action_time))
        self.last_action_time = time.time()

    def switch_probe_orientation(self):
        if self.current_position['probe_orientation'] == 'long':
            self.current_position['probe_orientation'] = 'trans'
        elif self.current_position['probe_orientation'] == 'trans':
            self.current_position['probe_orientation'] = 'long'

    def end_game(self):
        is_fractured_guess = input('Is the bone fractured? (yes/no): ')
        confidence_level = int(input('Enter your confidence level (1 [guessing] -10 [very confident]): '))

        # Save csv in output/game folder
        output_folder = 'output/game/'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        filename = f'{output_folder}{self.name}_{self.status}_{is_fractured_guess}_{confidence_level}_{self.pig}_{self.laterality}_{time.strftime("%Y%m%d-%H%M%S")}.csv'
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Probe position','Action', 'Time'])
            writer.writerows(self.actions)

        print(f"Game ended. Actions and time taken saved to {filename}.")


if __name__ == '__main__':
    game = Game()
    game.start()