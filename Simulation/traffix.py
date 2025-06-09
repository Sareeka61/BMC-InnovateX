import random
import math
import time
import threading
import pygame
import sys
import os

# --- Configuration Constants ---
DEFAULT_RED_TIME = 150
DEFAULT_YELLOW_TIME = 5
DEFAULT_GREEN_TIME = 20
DEFAULT_MIN_GREEN_TIME = 5
DEFAULT_MAX_GREEN_TIME = 60
SIMULATION_DURATION = 200

# Average times for vehicles to pass the intersection
CAR_PASS_TIME = 2
BIKE_PASS_TIME = 1
AMBULANCE_PASS_TIME = 1.5
BUS_PASS_TIME = 2.5
TRUCK_PASS_TIME = 2.5

DETECTION_TIME = 5  # Red signal time at which cars will be detected for next green calculation

VEHICLE_SPEEDS = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'ambulance': 3, 'bike': 2.5}

# Gap between vehicles
STOPPING_GAP = 15
MOVING_GAP = 15

ROTATION_ANGLE = 3

# --- Pygame Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
EMERGENCY_RED = (200, 0, 0) # A distinct red for emergency override

# --- Pygame Screen Dimensions ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800

# --- Global Variables ---
traffic_signals = []
NUM_SIGNALS = 4
time_elapsed = 0
current_green_signal_index = 0
next_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
is_yellow_light_on = 0  # 0: off, 1: on

emergency_vehicles_detected = [] 
current_priority_signal_index = -1 

# Coordinates for vehicle starting positions
START_COORDS_X = {
    'right': [0, 0, 0],
    'down': [755, 727, 697],
    'left': [1400, 1400, 1400],
    'up': [602, 627, 657]
}
START_COORDS_Y = {
    'right': [348, 370, 398],
    'down': [0, 0, 0],
    'left': [498, 466, 436],
    'up': [800, 800, 800]
}

# Vehicle data structure: stores lists of vehicles for each lane and a count of crossed vehicles
vehicles = {
    'right': {0: [], 1: [], 2: [], 'crossed': 0},
    'down': {0: [], 1: [], 2: [], 'crossed': 0},
    'left': {0: [], 1: [], 2: [], 'crossed': 0},
    'up': {0: [], 1: [], 2: [], 'crossed': 0}
}

VEHICLE_TYPES = {0: 'car', 1: 'bus', 2: 'truck', 3: 'ambulance', 4: 'bike'}
DIRECTION_NAMES = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

# Coordinates of signal image, timer, and vehicle count on screen
SIGNAL_COORDS = [(530, 230), (810, 230), (810, 570), (530, 570)]
SIGNAL_TIMER_COORDS = [(530, 210), (810, 210), (810, 550), (530, 550)]
VEHICLE_COUNT_COORDS = [(480, 210), (880, 210), (880, 550), (480, 550)]
vehicle_count_display_texts = ["0", "0", "0", "0"]

# Coordinates of stop lines
STOP_LINES = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
DEFAULT_STOP_COORDS = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

# Dynamic stop coordinates for each lane (adjusted as vehicles accumulate)
current_stop_coords = {
    'right': [580, 580, 580],
    'down': [320, 320, 320],
    'left': [810, 810, 810],
    'up': [545, 545, 545]
}

# Midpoint coordinates for turning vehicles
MID_COORDS = {
    'right': {'x': 705, 'y': 445},
    'down': {'x': 695, 'y': 450},
    'left': {'x': 695, 'y': 425},
    'up': {'x': 695, 'y': 400}
}

pygame.init()
all_sprites = pygame.sprite.Group()

class TrafficSignal:
    def __init__(self, red_time, yellow_time, green_time, min_green, max_green):
        self.red = red_time
        self.yellow = yellow_time
        self.green = green_time
        self.minimum = min_green
        self.maximum = max_green
        self.signal_text = str(DEFAULT_GREEN_TIME)
        self.total_green_time = 0

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicle_class, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicle_class = vehicle_class
        self.speed = VEHICLE_SPEEDS[vehicle_class]
        self.direction_number = direction_number
        self.direction = direction
        self.x = START_COORDS_X[direction][lane]
        self.y = START_COORDS_Y[direction][lane]
        self.crossed_stop_line = 0
        self.will_turn = will_turn
        self.has_turned = 0
        self.rotation_angle = 0
        self.is_emergency = (vehicle_class == 'ambulance')

        vehicles[direction][lane].append(self)
        self.index_in_lane = len(vehicles[direction][lane]) - 1 # Initial index

        # Load vehicle image
        image_path = os.path.join("images", direction, f"{vehicle_class}.png")
        self.original_image = pygame.image.load(image_path)
        self.current_image = pygame.image.load(image_path)

        # Calculate initial stop coordinate for the vehicle
        if direction == 'right':
            if self.index_in_lane > 0 and vehicles[direction][lane][self.index_in_lane - 1].crossed_stop_line == 0:
                self.stop = vehicles[direction][lane][self.index_in_lane - 1].stop - \
                            vehicles[direction][lane][self.index_in_lane - 1].current_image.get_rect().width - STOPPING_GAP
            else:
                self.stop = DEFAULT_STOP_COORDS[direction]
            offset = self.current_image.get_rect().width + STOPPING_GAP
            START_COORDS_X[direction][lane] -= offset
            current_stop_coords[direction][lane] -= offset
        elif direction == 'left':
            if self.index_in_lane > 0 and vehicles[direction][lane][self.index_in_lane - 1].crossed_stop_line == 0:
                self.stop = vehicles[direction][lane][self.index_in_lane - 1].stop + \
                            vehicles[direction][lane][self.index_in_lane - 1].current_image.get_rect().width + STOPPING_GAP
            else:
                self.stop = DEFAULT_STOP_COORDS[direction]
            offset = self.current_image.get_rect().width + STOPPING_GAP
            START_COORDS_X[direction][lane] += offset
            current_stop_coords[direction][lane] += offset
        elif direction == 'down':
            if self.index_in_lane > 0 and vehicles[direction][lane][self.index_in_lane - 1].crossed_stop_line == 0:
                self.stop = vehicles[direction][lane][self.index_in_lane - 1].stop - \
                            vehicles[direction][lane][self.index_in_lane - 1].current_image.get_rect().height - STOPPING_GAP
            else:
                self.stop = DEFAULT_STOP_COORDS[direction]
            offset = self.current_image.get_rect().height + STOPPING_GAP
            START_COORDS_Y[direction][lane] -= offset
            current_stop_coords[direction][lane] -= offset
        elif direction == 'up':
            if self.index_in_lane > 0 and vehicles[direction][lane][self.index_in_lane - 1].crossed_stop_line == 0:
                self.stop = vehicles[direction][lane][self.index_in_lane - 1].stop + \
                            vehicles[direction][lane][self.index_in_lane - 1].current_image.get_rect().height + STOPPING_GAP
            else:
                self.stop = DEFAULT_STOP_COORDS[direction]
            offset = self.current_image.get_rect().height + STOPPING_GAP
            START_COORDS_Y[direction][lane] += offset
            current_stop_coords[direction][lane] += offset
        
        all_sprites.add(self)

    def remove_from_lane(self):
        all_sprites.remove(self)
        
        if self in vehicles[self.direction][self.lane]:
            vehicles[self.direction][self.lane].remove(self) 
        
        for i, veh in enumerate(vehicles[self.direction][self.lane]):
            veh.index_in_lane = i

    def move(self):
        global emergency_vehicles_detected, current_priority_signal_index
        
        if self.is_emergency and self.index_in_lane == 0 and self.crossed_stop_line == 0:
            if not any(v[1] == self for v in emergency_vehicles_detected):
                emergency_vehicles_detected.append((self.direction_number, self))
                emergency_vehicles_detected.sort(key=lambda x: x[1].x if x[1].direction == 'right' else \
                                                              x[1].y if x[1].direction == 'down' else \
                                                              -x[1].x if x[1].direction == 'left' else \
                                                              -x[1].y) 
                print(f"!!! EMERGENCY: Ambulance detected in {self.direction} lane. Adding to queue. Queue: {[DIRECTION_NAMES[sig] for sig, veh in emergency_vehicles_detected]}")
        
        # Determine if the vehicle should move based on its direction, stop line, and signal status
        can_move = False
        
        # Check if there are any vehicles currently crossing the intersection
        vehicles_crossing = False
        for direction in DIRECTION_NAMES.values():
            for lane in range(3):
                for vehicle in vehicles[direction][lane]:
                    if vehicle.crossed_stop_line == 1 and not vehicle.has_turned:
                        # Check if vehicle is still within intersection bounds
                        if (direction == 'right' and vehicle.x < 800) or \
                           (direction == 'left' and vehicle.x > 590) or \
                           (direction == 'down' and vehicle.y < 535) or \
                           (direction == 'up' and vehicle.y > 330):
                            vehicles_crossing = True
                            break
                if vehicles_crossing:
                    break
            if vehicles_crossing:
                break
        
        # Scenario 1: No emergency currently prioritized, normal traffic flow
        if current_priority_signal_index == -1:
            if self.direction_number == current_green_signal_index and is_yellow_light_on == 0:
                can_move = True 
            elif self.crossed_stop_line == 1: 
                can_move = True
            elif self.is_emergency and self.index_in_lane == 0 and not vehicles_crossing:
                can_move = True
                print(f"Ambulance in {self.direction} lane proceeding (clear intersection).")
            elif self.is_emergency:
                if self.index_in_lane == 0 or \
                   (self.index_in_lane > 0 and \
                    ((self.direction == 'right' and self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width + MOVING_GAP)) or \
                     (self.direction == 'left' and self.x < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width - MOVING_GAP)) or \
                     (self.direction == 'down' and self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height + MOVING_GAP)) or \
                     (self.direction == 'up' and self.y < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height - MOVING_GAP)))):
                   can_move = True
                   print(f"Ambulance in {self.direction} lane breaking red (no current explicit priority).")

        # Scenario 2: Emergency mode is active
        else:
            if self.direction_number == current_priority_signal_index:
                can_move = True
            elif self.is_emergency and self.index_in_lane == 0 and not vehicles_crossing:
                # Allow other ambulances to proceed if they're at the front and no vehicles are crossing
                can_move = True
                print(f"Ambulance in {self.direction} lane proceeding (clear intersection during priority).")
            elif self.is_emergency: 
                if self.index_in_lane == 0 or \
                   (self.index_in_lane > 0 and \
                    ((self.direction == 'right' and self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width + MOVING_GAP)) or \
                     (self.direction == 'left' and self.x < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width - MOVING_GAP)) or \
                     (self.direction == 'down' and self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height + MOVING_GAP)) or \
                     (self.direction == 'up' and self.y < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height - MOVING_GAP)))):
                   can_move = True
                   print(f"Ambulance in {self.direction} lane breaking red (another ambulance has explicit priority).")
            else:
                can_move = False # Other non-emergency vehicles must wait for current priority

        if self.direction == 'right':
            if self.crossed_stop_line == 0 and self.x + self.current_image.get_rect().width > STOP_LINES[self.direction]:
                self.crossed_stop_line = 1
                vehicles[self.direction]['crossed'] += 1
            
            if self.will_turn == 1:
                if self.crossed_stop_line == 0 or self.x + self.current_image.get_rect().width < MID_COORDS[self.direction]['x']:
                    if (can_move or (self.x + self.current_image.get_rect().width <= self.stop and self.crossed_stop_line == 0)) and \
                       (self.index_in_lane == 0 or self.x + self.current_image.get_rect().width < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - MOVING_GAP) or vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1):
                        self.x += self.speed
                else:
                    if self.has_turned == 0:
                        self.rotation_angle += ROTATION_ANGLE
                        self.current_image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                        self.x += 2
                        self.y += 1.8
                        if self.rotation_angle == 90:
                            self.has_turned = 1
                    else:
                        if (self.index_in_lane == 0 or self.y + self.current_image.get_rect().height < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - MOVING_GAP) or 
                            self.x + self.current_image.get_rect().width < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - MOVING_GAP)):
                            self.y += self.speed
            else: # Not turning
                if (can_move or (self.x + self.current_image.get_rect().width <= self.stop and self.crossed_stop_line == 0)) and \
                   (self.index_in_lane == 0 or self.x + self.current_image.get_rect().width < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - MOVING_GAP) or (vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1)):
                    self.x += self.speed
            
            # Check if vehicle has cleared the intersection
            if self.x > SCREEN_WIDTH + 100: # Slightly beyond screen width
                self.remove_from_lane()
                return # Stop processing this vehicle further

        elif self.direction == 'down':
            if self.crossed_stop_line == 0 and self.y + self.current_image.get_rect().height > STOP_LINES[self.direction]:
                self.crossed_stop_line = 1
                vehicles[self.direction]['crossed'] += 1

            if self.will_turn == 1:
                if self.crossed_stop_line == 0 or self.y + self.current_image.get_rect().height < MID_COORDS[self.direction]['y']:
                    if (can_move or (self.y + self.current_image.get_rect().height <= self.stop and self.crossed_stop_line == 0)) and \
                       (self.index_in_lane == 0 or self.y + self.current_image.get_rect().height < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - MOVING_GAP) or vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1):
                        self.y += self.speed
                else:
                    if self.has_turned == 0:
                        self.rotation_angle += ROTATION_ANGLE
                        self.current_image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                        self.x -= 2.5
                        self.y += 2
                        if self.rotation_angle == 90:
                            self.has_turned = 1
                    else:
                        if (self.index_in_lane == 0 or self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width + MOVING_GAP) or 
                            self.y < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - MOVING_GAP)):
                            self.x -= self.speed
            else: # Not turning
                if (can_move or (self.y + self.current_image.get_rect().height <= self.stop and self.crossed_stop_line == 0)) and \
                   (self.index_in_lane == 0 or self.y + self.current_image.get_rect().height < (vehicles[self.direction][self.lane][self.index_in_lane - 1].y - MOVING_GAP) or (vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1)):
                    self.y += self.speed

            if self.y > SCREEN_HEIGHT + 100: 
                self.remove_from_lane()
                return

        elif self.direction == 'left':
            if self.crossed_stop_line == 0 and self.x < STOP_LINES[self.direction]:
                self.crossed_stop_line = 1
                vehicles[self.direction]['crossed'] += 1

            if self.will_turn == 1:
                if self.crossed_stop_line == 0 or self.x > MID_COORDS[self.direction]['x']:
                    if (can_move or (self.x >= self.stop and self.crossed_stop_line == 0)) and \
                       (self.index_in_lane == 0 or self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width + MOVING_GAP) or vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1):
                        self.x -= self.speed
                else:
                    if self.has_turned == 0:
                        self.rotation_angle += ROTATION_ANGLE
                        self.current_image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                        self.x -= 1.8
                        self.y -= 2.5
                        if self.rotation_angle == 90:
                            self.has_turned = 1
                    else:
                        if (self.index_in_lane == 0 or self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height + MOVING_GAP) or 
                            self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + MOVING_GAP)):
                            self.y -= self.speed
            else: # Not turning
                if (can_move or (self.x >= self.stop and self.crossed_stop_line == 0)) and \
                   (self.index_in_lane == 0 or self.x > (vehicles[self.direction][self.lane][self.index_in_lane - 1].x + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width + MOVING_GAP) or (vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1)):
                    self.x -= self.speed

            # Check if vehicle has cleared the intersection
            if self.x + self.current_image.get_rect().width < -100: # Slightly beyond left edge
                self.remove_from_lane()
                return

        elif self.direction == 'up':
            if self.crossed_stop_line == 0 and self.y < STOP_LINES[self.direction]:
                self.crossed_stop_line = 1
                vehicles[self.direction]['crossed'] += 1
            
            if self.will_turn == 1:
                if self.crossed_stop_line == 0 or self.y > MID_COORDS[self.direction]['y']:
                    if (can_move or (self.y >= self.stop and self.crossed_stop_line == 0)) and \
                       (self.index_in_lane == 0 or self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height + MOVING_GAP) or vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1):
                        self.y -= self.speed
                else:
                    if self.has_turned == 0:
                        self.rotation_angle += ROTATION_ANGLE
                        self.current_image = pygame.transform.rotate(self.original_image, -self.rotation_angle)
                        self.x += 1
                        self.y -= 1
                        if self.rotation_angle == 90:
                            self.has_turned = 1
                    else:
                        if (self.index_in_lane == 0 or self.x < (vehicles[self.direction][self.lane][self.index_in_lane - 1].x - vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().width - MOVING_GAP) or 
                            self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + MOVING_GAP)):
                            self.x += self.speed
            else: # Not turning
                if (can_move or (self.y >= self.stop and self.crossed_stop_line == 0)) and \
                   (self.index_in_lane == 0 or self.y > (vehicles[self.direction][self.lane][self.index_in_lane - 1].y + vehicles[self.direction][self.lane][self.index_in_lane - 1].current_image.get_rect().height + MOVING_GAP) or (vehicles[self.direction][self.lane][self.index_in_lane - 1].has_turned == 1)):
                    self.y -= self.speed

            # Check if vehicle has cleared the intersection
            if self.y + self.current_image.get_rect().height < -100:
                self.remove_from_lane()
                return

def initialize_signals():
    """Initializes all traffic signals with default values."""
    ts1 = TrafficSignal(0, DEFAULT_YELLOW_TIME, DEFAULT_GREEN_TIME, DEFAULT_MIN_GREEN_TIME, DEFAULT_MAX_GREEN_TIME)
    traffic_signals.append(ts1)
    ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, DEFAULT_YELLOW_TIME, DEFAULT_GREEN_TIME, DEFAULT_MIN_GREEN_TIME, DEFAULT_MAX_GREEN_TIME)
    traffic_signals.append(ts2)
    ts3 = TrafficSignal(DEFAULT_RED_TIME, DEFAULT_YELLOW_TIME, DEFAULT_GREEN_TIME, DEFAULT_MIN_GREEN_TIME, DEFAULT_MAX_GREEN_TIME)
    traffic_signals.append(ts3)
    ts4 = TrafficSignal(DEFAULT_RED_TIME, DEFAULT_YELLOW_TIME, DEFAULT_GREEN_TIME, DEFAULT_MIN_GREEN_TIME, DEFAULT_MAX_GREEN_TIME)
    traffic_signals.append(ts4)
    run_signal_cycle()

def calculate_and_set_green_time():
    """Calculates and sets the green time for the next signal based on vehicle count."""
    num_cars, num_bikes, num_buses, num_trucks, num_ambulances = 0, 0, 0, 0, 0
    next_signal_direction = DIRECTION_NAMES[next_green_signal_index]

    # Count bikes in lane 0
    for vehicle in vehicles[next_signal_direction][0]:
        if vehicle.crossed_stop_line == 0:
            num_bikes += 1

    # Count other vehicles in lanes 1 and 2
    for lane_idx in range(1, 3):
        for vehicle in vehicles[next_signal_direction][lane_idx]:
            if vehicle.crossed_stop_line == 0:
                vclass = vehicle.vehicle_class
                if vclass == 'car':
                    num_cars += 1
                elif vclass == 'bus':
                    num_buses += 1
                elif vclass == 'truck':
                    num_trucks += 1
                elif vclass == 'ambulance':
                    num_ambulances += 1

    num_lanes = 2
    green_time = math.ceil(((num_cars * CAR_PASS_TIME) + (num_ambulances * AMBULANCE_PASS_TIME) +
                            (num_buses * BUS_PASS_TIME) + (num_trucks * TRUCK_PASS_TIME) +
                            (num_bikes * BIKE_PASS_TIME)) / (num_lanes + 1))

    if green_time < DEFAULT_MIN_GREEN_TIME:
        green_time = DEFAULT_MIN_GREEN_TIME
    elif green_time > DEFAULT_MAX_GREEN_TIME:
        green_time = DEFAULT_MAX_GREEN_TIME
    
    traffic_signals[next_green_signal_index].green = green_time
    print(f'Calculated Green Time for {next_signal_direction} signal: {green_time}')

def run_signal_cycle():
    """Manages the cyclic behavior of traffic signals, including emergency prioritization."""
    global current_green_signal_index, is_yellow_light_on, next_green_signal_index, \
           emergency_vehicles_detected, current_priority_signal_index

    # --- Emergency Prioritization Logic ---
    if len(emergency_vehicles_detected) > 0:
        if current_priority_signal_index == -1:
            emergency_vehicles_detected = [v for v in emergency_vehicles_detected if v[1].crossed_stop_line == 0]
            if len(emergency_vehicles_detected) > 0: 
                current_priority_signal_index = emergency_vehicles_detected[0][0]

                print(f"!!! EMERGENCY OVERRIDE: Granting green to signal {current_priority_signal_index + 1} ({DIRECTION_NAMES[current_priority_signal_index]}).")
                
                for i in range(NUM_SIGNALS):
                    if i != current_priority_signal_index:
                        traffic_signals[i].red = DEFAULT_RED_TIME 
                        traffic_signals[i].green = 0
                        traffic_signals[i].yellow = 0
                
                # Set emergency signal to green
                traffic_signals[current_priority_signal_index].green = DEFAULT_MAX_GREEN_TIME 
                traffic_signals[current_priority_signal_index].red = 0
                traffic_signals[current_priority_signal_index].yellow = 0
                is_yellow_light_on = 0 
                
                current_green_signal_index = current_priority_signal_index 
                next_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
            else: # Queue is empty, no emergency to prioritize
                current_priority_signal_index = -1 
                run_signal_cycle()
                return

        ambulance_passed = True
        if current_priority_signal_index != -1:
            direction_of_priority = DIRECTION_NAMES[current_priority_signal_index]
            
            prioritized_ambulance_obj = None
            for sig_idx, veh_obj in emergency_vehicles_detected:
                if sig_idx == current_priority_signal_index:
                    prioritized_ambulance_obj = veh_obj
                    break
            
            if prioritized_ambulance_obj and prioritized_ambulance_obj.crossed_stop_line == 0:
                ambulance_passed = False
        
        if ambulance_passed and current_priority_signal_index != -1: 
            print(f"Prioritized ambulance in {DIRECTION_NAMES[current_priority_signal_index]} lane passed.")
            
            emergency_vehicles_detected = [v for v in emergency_vehicles_detected if v[1].crossed_stop_line == 0]
            
            current_priority_signal_index = -1 # Reset priority

            if len(emergency_vehicles_detected) > 0:
                print("Proceeding to next emergency vehicle in queue.")
            else:
                print("No more emergency vehicles. Resuming normal traffic cycle.")
                
                for i in range(NUM_SIGNALS):
                    traffic_signals[i].green = DEFAULT_GREEN_TIME
                    traffic_signals[i].yellow = DEFAULT_YELLOW_TIME
                    traffic_signals[i].red = DEFAULT_RED_TIME
                current_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
                next_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
                traffic_signals[next_green_signal_index].red = traffic_signals[current_green_signal_index].yellow + traffic_signals[current_green_signal_index].green
        
        print_signal_status()
        update_signal_timers()
        time.sleep(1) 
        run_signal_cycle() 

    else: # No emergency vehicles detected or currently prioritized, go for Normal Signal Cycle
        while traffic_signals[current_green_signal_index].green > 0:
            print_signal_status()
            update_signal_timers()
            # Check for emergency during normal green
            if len(emergency_vehicles_detected) > 0:
                print("Emergency detected, interrupting normal cycle.")
                # Force current green to red instantly
                traffic_signals[current_green_signal_index].green = 0
                is_yellow_light_on = 0
                for i in range(NUM_SIGNALS): 
                    if i != current_green_signal_index:
                         traffic_signals[i].red = DEFAULT_RED_TIME
                break # Exit current green phase to handle emergency
            
            # Only trigger detection for next signal if not an emergency override
            if traffic_signals[(current_green_signal_index + 1) % NUM_SIGNALS].red == DETECTION_TIME:
                detection_thread = threading.Thread(name="detection", target=calculate_and_set_green_time)
                detection_thread.daemon = True
                detection_thread.start()
            
            time.sleep(1)
            traffic_signals[current_green_signal_index].green -= 1
        
        # Check if there are any vehicles waiting in the next signal's direction
        next_signal = (current_green_signal_index + 1) % NUM_SIGNALS
        next_direction = DIRECTION_NAMES[next_signal]
        has_vehicles_waiting = False
        
        for lane in range(3):
            for vehicle in vehicles[next_direction][lane]:
                if vehicle.crossed_stop_line == 0: 
                    has_vehicles_waiting = True
                    break
            if has_vehicles_waiting:
                break
        
        if not has_vehicles_waiting:
            print(f"Skipping {next_direction} signal as no vehicles are waiting.")
            current_green_signal_index = (next_signal + 1) % NUM_SIGNALS
            next_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
            traffic_signals[current_green_signal_index].green = DEFAULT_GREEN_TIME
            traffic_signals[current_green_signal_index].yellow = DEFAULT_YELLOW_TIME
            traffic_signals[current_green_signal_index].red = DEFAULT_RED_TIME
        else:
            # Normal transition to next signal
            is_yellow_light_on = 1
            traffic_signals[current_green_signal_index].yellow = DEFAULT_YELLOW_TIME
            traffic_signals[current_green_signal_index].green = 0
            
            while traffic_signals[current_green_signal_index].yellow > 0:
                print_signal_status()
                update_signal_timers()
                time.sleep(1)
                traffic_signals[current_green_signal_index].yellow -= 1
            
            is_yellow_light_on = 0
            traffic_signals[current_green_signal_index].red = DEFAULT_RED_TIME
            current_green_signal_index = next_green_signal_index
            next_green_signal_index = (current_green_signal_index + 1) % NUM_SIGNALS
            traffic_signals[current_green_signal_index].green = DEFAULT_GREEN_TIME
        
        run_signal_cycle()

def print_signal_status():                                                                                                                  
    print(f"--- Simulation Time: {time_elapsed}s --- Emergency Priority: {'ON' if current_priority_signal_index != -1 else 'OFF'} ---")
    if current_priority_signal_index != -1:
        print(f"  Current Priority Signal: {DIRECTION_NAMES[current_priority_signal_index]}")
        print(f"  Emergency Queue: {[DIRECTION_NAMES[sig] for sig, veh in emergency_vehicles_detected if veh.crossed_stop_line == 0]}") # Only show uncrossed in queue
    print()
    for i in range(NUM_SIGNALS):
        if i == current_green_signal_index and current_priority_signal_index == -1: # Normal Green
            if is_yellow_light_on == 0:
                print(f" GREEN TS{i+1} ({DIRECTION_NAMES[i]}) -> r:{traffic_signals[i].red} y:{traffic_signals[i].yellow} g:{traffic_signals[i].green}")
            else:
                print(f"YELLOW TS{i+1} ({DIRECTION_NAMES[i]}) -> r:{traffic_signals[i].red} y:{traffic_signals[i].yellow} g:{traffic_signals[i].green}")
        elif i == current_priority_signal_index and current_priority_signal_index != -1: # Emergency Green
             print(f"EMERGENCY TS{i+1} ({DIRECTION_NAMES[i]}) -> r:{traffic_signals[i].red} y:{traffic_signals[i].yellow} g:{traffic_signals[i].green}")
        else: # Red
            print(f"    RED TS{i+1} ({DIRECTION_NAMES[i]}) -> r:{traffic_signals[i].red} y:{traffic_signals[i].yellow} g:{traffic_signals[i].green}")
    print()


def update_signal_timers():
    """Updates the timers of the traffic signals each second."""
    global current_priority_signal_index
    
    if current_priority_signal_index != -1:
        traffic_signals[current_priority_signal_index].green = max(0, traffic_signals[current_priority_signal_index].green - 1)
        
        for i in range(NUM_SIGNALS):
            if i != current_priority_signal_index:
                traffic_signals[i].red = max(0, traffic_signals[i].red)
    else: 
        for i in range(NUM_SIGNALS):
            if i == current_green_signal_index:
                if is_yellow_light_on == 0:
                    traffic_signals[i].green -= 1
                    traffic_signals[i].total_green_time += 1
                else:
                    traffic_signals[i].yellow -= 1
            else:
                traffic_signals[i].red -= 1

def generate_vehicles():
    """Generates vehicles randomly and adds them to the simulation."""
    while True:
        vehicle_type_num = random.randint(1, 50)
        if vehicle_type_num == 3: 
            vehicle_class = 'ambulance'
            lane_number = random.randint(1, 2)
        elif vehicle_type_num == 4:  
            vehicle_class = 'bike'
            lane_number = 0
        else:
            vehicle_class = random.choice(['car', 'bus', 'truck'])
            lane_number = random.randint(1, 2)
        
        will_turn = 0
        if lane_number == 2:
            if random.randint(0, 4) <= 2:
                will_turn = 1
            else:
                will_turn = 0
        
        temp_direction = random.randint(0, 999)
        direction_number = 0
        direction_thresholds = [400, 800, 900, 1000]
        if temp_direction < direction_thresholds[0]:
            direction_number = 0  # Right
        elif temp_direction < direction_thresholds[1]:
            direction_number = 1  # Down
        elif temp_direction < direction_thresholds[2]:
            direction_number = 2  # Left
        elif temp_direction < direction_thresholds[3]:
            direction_number = 3  # Up
        
        Vehicle(lane_number, vehicle_class, direction_number, DIRECTION_NAMES[direction_number], will_turn)
        time.sleep(3)

def manage_simulation_time():
    """Manages the overall simulation time and outputs statistics at the end."""
    global time_elapsed
    while True:
        time_elapsed += 1
        time.sleep(1)
        if time_elapsed == SIMULATION_DURATION:
            total_vehicles_passed = 0
            print('\n--- Simulation Summary ---')
            print('Lane-wise Vehicle Counts:')
            for i in range(NUM_SIGNALS):
                crossed_count = vehicles[DIRECTION_NAMES[i]]['crossed']
                print(f'  Lane {i+1} ({DIRECTION_NAMES[i]}): {crossed_count} vehicles')
                total_vehicles_passed += crossed_count
            print(f'Total vehicles passed: {total_vehicles_passed}')
            print(f'Total time passed: {time_elapsed} seconds')
            if time_elapsed > 0:
                print(f'Vehicles passed per unit time: {total_vehicles_passed / float(time_elapsed):.2f}')
            os._exit(0)

class TrafficSimulationApp:
    """Main application class for the traffic simulation."""
    def __init__(self):
        pygame.display.set_caption("Traffic Simulation")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background = pygame.image.load('images/mod_int.png')
        
        self.red_signal_img = pygame.image.load('images/signals/red.png')
        self.yellow_signal_img = pygame.image.load('images/signals/yellow.png')
        self.green_signal_img = pygame.image.load('images/signals/green.png')
        self.font = pygame.font.Font(None, 30)

        self._start_threads()
        self._run_game_loop()

    def _start_threads(self):
        """Starts the necessary simulation threads."""
        simulation_time_thread = threading.Thread(name="simulationTime", target=manage_simulation_time)
        simulation_time_thread.daemon = True
        simulation_time_thread.start()

        initialization_thread = threading.Thread(name="initialization", target=initialize_signals)
        initialization_thread.daemon = True
        initialization_thread.start()

        vehicle_generation_thread = threading.Thread(name="generateVehicles", target=generate_vehicles)
        vehicle_generation_thread.daemon = True
        vehicle_generation_thread.start()

    def _run_game_loop(self):
        """Main Pygame event loop and rendering."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.screen.blit(self.background, (0, 0))

            self._draw_signals_and_timers()
            self._draw_vehicles()
            self._display_elapsed_time()

            pygame.display.update()

    def _draw_signals_and_timers(self):
        """Draws traffic signals, their timers, and vehicle counts on the screen."""
        for i in range(NUM_SIGNALS):
            signal_img_to_draw = None
            
            # Prioritize emergency signal display
            if current_priority_signal_index != -1 and i == current_priority_signal_index:
                traffic_signals[i].signal_text = "EMERGENCY"
                signal_img_to_draw = self.green_signal_img
            elif i == current_green_signal_index and current_priority_signal_index == -1: # Normal Green/Yellow
                if is_yellow_light_on == 1:
                    traffic_signals[i].signal_text = str(traffic_signals[i].yellow) if traffic_signals[i].yellow > 0 else "STOP"
                    signal_img_to_draw = self.yellow_signal_img
                else:
                    traffic_signals[i].signal_text = str(traffic_signals[i].green) if traffic_signals[i].green > 0 else "SLOW"
                    signal_img_to_draw = self.green_signal_img
            else: # Red (either normal red or emergency-induced red)
                traffic_signals[i].signal_text = "---"
                signal_img_to_draw = self.red_signal_img
                
                # If emergency is active, signals not getting priority are red for traffic, but ambulances can still proceed
                if current_priority_signal_index != -1 and i != current_priority_signal_index:
                    traffic_signals[i].signal_text = "STOP" # Or "EMERGENCY RED"
                    
                elif traffic_signals[i].red <= 10 and traffic_signals[i].red > 0:
                    traffic_signals[i].signal_text = str(traffic_signals[i].red)
                elif traffic_signals[i].red == 0:
                    traffic_signals[i].signal_text = "GO"
            
            self.screen.blit(signal_img_to_draw, SIGNAL_COORDS[i])

            # Render signal timer
            signal_timer_surface = self.font.render(str(traffic_signals[i].signal_text), True, WHITE, BLACK)
            self.screen.blit(signal_timer_surface, SIGNAL_TIMER_COORDS[i])

            # Render vehicle count
            display_count = vehicles[DIRECTION_NAMES[i]]['crossed']
            vehicle_count_surface = self.font.render(str(display_count), True, BLACK, WHITE)
            self.screen.blit(vehicle_count_surface, VEHICLE_COUNT_COORDS[i])

    def _draw_vehicles(self):
        """Draws all vehicles currently in the simulation and updates their positions."""
        for vehicle in list(all_sprites): 
            if vehicle.alive(): 
                self.screen.blit(vehicle.current_image, (vehicle.x, vehicle.y))
                vehicle.move()

    def _display_elapsed_time(self):
        """Displays the elapsed simulation time on the screen."""
        time_elapsed_surface = self.font.render(f"Total Time Passed: {time_elapsed}", True, BLACK, WHITE)
        self.screen.blit(time_elapsed_surface, (1100, 50))

if __name__ == "__main__":
    TrafficSimulationApp()

