import cv2
import numpy as np
import os
import random

# Video settings
WIDTH, HEIGHT = 1280, 720
FPS = 25
DURATION = 10  # seconds
TOTAL_FRAMES = FPS * DURATION
SAMPLES_DIR = 'samples'

if not os.path.exists(SAMPLES_DIR):
    os.makedirs(SAMPLES_DIR)

def draw_person(frame, x, y):
    """Draw a basic silhouette that YOLO might recognize as a person."""
    # Head
    cv2.circle(frame, (int(x), int(y - 20)), 10, (50, 50, 50), -1)
    # Body (Oval)
    cv2.ellipse(frame, (int(x), int(y + 10)), (15, 30), 0, 0, 360, (70, 70, 70), -1)

def generate_video(filename, crowd_size, speed_range, jitter=2, scenario='normal'):
    print(f"Generating {filename}...")
    path = os.path.join(SAMPLES_DIR, filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, FPS, (WIDTH, HEIGHT))

    # Initialize crowd
    people = []
    for _ in range(crowd_size):
        if scenario == 'bottleneck':
            # Start from all sides except bottom
            side = random.choice(['top', 'left', 'right'])
            if side == 'top':
                x, y = random.uniform(0, WIDTH), random.uniform(0, HEIGHT//2)
            elif side == 'left':
                x, y = random.uniform(0, WIDTH//2), random.uniform(0, HEIGHT)
            else:
                x, y = random.uniform(WIDTH//2, WIDTH), random.uniform(0, HEIGHT)
        else:
            x = random.uniform(50, WIDTH - 50)
            y = random.uniform(50, HEIGHT - 50)
            
        vx = random.uniform(*speed_range) * random.choice([-1, 1])
        vy = random.uniform(*speed_range) * random.choice([-1, 1])
        people.append({'x': x, 'y': y, 'vx': vx, 'vy': vy})

    for f in range(TOTAL_FRAMES):
        frame = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 200 # Light gray background
        
        # Add some "floor" texture/lines for context
        for i in range(0, HEIGHT, 100):
            cv2.line(frame, (0, i), (WIDTH, i), (180, 180, 180), 1)
        for i in range(0, WIDTH, 100):
            cv2.line(frame, (i, 0), (i, HEIGHT), (180, 180, 180), 1)

        # Draw "Exit" for bottleneck
        if scenario == 'bottleneck':
            exit_x, exit_y = WIDTH // 2, HEIGHT - 20
            cv2.rectangle(frame, (exit_x - 50, exit_y - 30), (exit_x + 50, exit_y), (0, 100, 0), -1)
            cv2.putText(frame, "EXIT", (exit_x - 30, exit_y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 0), 2)

        for p in people:
            # Movement logic
            if scenario == 'bottleneck':
                # Move towards exit
                dx = (WIDTH // 2) - p['x']
                dy = (HEIGHT - 20) - p['y']
                dist = np.sqrt(dx**2 + dy**2)
                if dist > 5:
                    p['vx'] = (dx / dist) * random.uniform(*speed_range)
                    p['vy'] = (dy / dist) * random.uniform(*speed_range)
                else:
                    # Reset person to top if they reached exit
                    p['x'] = random.uniform(0, WIDTH)
                    p['y'] = random.uniform(0, 100)
            elif scenario == 'panic':
                # Rapid changes in direction
                if random.random() < 0.1:
                    p['vx'] = random.uniform(*speed_range) * random.choice([-1, 1])
                    p['vy'] = random.uniform(*speed_range) * random.choice([-1, 1])
            else:
                # Normal/High Density - mostly linear with jitter
                pass

            p['x'] += p['vx'] + random.uniform(-jitter, jitter)
            p['y'] += p['vy'] + random.uniform(-jitter, jitter)

            # Bounce off walls (except bottleneck exit)
            if scenario != 'bottleneck':
                if p['x'] < 20 or p['x'] > WIDTH - 20: p['vx'] *= -1
                if p['y'] < 20 or p['y'] > HEIGHT - 20: p['vy'] *= -1
            
            draw_person(frame, p['x'], p['y'])

        out.write(frame)

    out.release()
    print(f"Done: {filename}")

if __name__ == "__main__":
    # Scenario 1: Normal Flow (25 people, moderate speed)
    generate_video("normal_flow.mp4", crowd_size=25, speed_range=(2, 4), scenario='normal')
    
    # Scenario 2: High Density (100 people, slow speed)
    generate_video("high_density.mp4", crowd_size=100, speed_range=(0.5, 1.5), jitter=0.5, scenario='high_density')
    
    # Scenario 3: Panic (40 people, high speed, high jitter)
    generate_video("panic.mp4", crowd_size=40, speed_range=(8, 15), jitter=5, scenario='panic')
    
    # Scenario 4: Bottleneck (60 people, converging to exit)
    generate_video("bottleneck.mp4", crowd_size=60, speed_range=(3, 6), scenario='bottleneck')
