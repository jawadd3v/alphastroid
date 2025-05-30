import pygame
import math
import string
import random

# Initialize Pygame and setup display
pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Alphastroid")
clock = pygame.time.Clock()
FPS = 60

# Load and scale the nebula background image
nebula_layer = pygame.image.load("assets/redset-nebula.jpg")
nebula_layer = pygame.transform.scale(nebula_layer, (WIDTH, HEIGHT))

# Load and scale instruction visuals
wasd_and_arrow_keys = pygame.image.load("assets/wasdandarrowkeys.png")
wasd_and_arrow_keys = pygame.transform.scale(wasd_and_arrow_keys, (400, 120))
spacebar_key = pygame.image.load("assets/spacebarkey.png")
spacebar_key = pygame.transform.scale(spacebar_key, (200, 120))

# Constants for game mechanics
SHIP_TURN_SPEED = 180 # Degrees per second
SHIP_ACCELERATION = 250
FRICTION = 0.99
MAX_SPEED = 300
NUM_ASTEROIDS = 2
BULLET_LIFESPAN = 2
BULLET_COOLDOWN = 0.2
NUM_STARS = 75

# Game State Variables
game_state = "MENU"
ship_pos = [WIDTH // 2, HEIGHT // 2] # Initial ship position
ship_angle = 0 # Initial rotation angle of the ship
ship_velocity = [0, 0] # Initial velocity vector of the ship
ship_fragments = [] # Debris fragments after ship destruction
ship_alive = True # Boolean for ship life status
thrusting = False # Boolean indicating if the ship is accelerating
asteroids = [] # List to store asteroid objects
stars = [] # List to store background stars
bullets = [] # List of active bullets
bullet_timer = 0 # Time since last bullet was fired
lives = 3 # Number of remaining lives
invincible = False # Whether the ship is temporarily invincible
invincibility_timer = 0 # Timer for invincibility duration
respawn_timer = 0 # Timer for ship respawn
score = 0 # Current player score
current_wave = 1 # Current wave of asteroids
first_time_instructions_overlay = True # Boolean for instructions shown status

# ~~~ Functions ~~~

# Ship related functions
def draw_ship(surface, position, angle):
    '''
    Draws the ship on the screen with optional thrust effect.
    
    Arguments:
        surface: Pygame surface to draw the ship.
        position: Tuple/list of x, y coordinates.
        angle: Angle in degrees for ship rotation.
    '''
    if ship_alive and (not invincible or int(pygame.time.get_ticks() /150) % 2 == 0): # Create glitchy flicker effect when invincible using modulo
        ship_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 30) # Importing Comfortaa Font
        text = ship_font.render("A", True, (200, 200, 200)) # Render the ship as the letter "A"
        rotated_text = pygame.transform.rotate(text, -angle) # Rotate the text counterclockwise
        text_rect = rotated_text.get_rect(center = position) # Draw the ship to the screen
        surface.blit(rotated_text, text_rect)
        
        if thrusting:
            # If the ship is thrusting draw flame effects
            position = pygame.Vector2(position) # Convert position to Vector2 for vector math
            # Define the rear corners and the tip of the thrust flame relative to the ship 
            rear_left = position + pygame.Vector2(-5, 10).rotate(angle) # Rear left point after rotation
            rear_right = position + pygame.Vector2(5, 10).rotate(angle) # Rear right point after rotation
            thrust_tip = position + pygame.Vector2(0, 20).rotate(angle) # Tip of the thrust flame
            # Draw two flame lines simulating thrust from each rear corner to the tip
            pygame.draw.line(surface, (255, 100, 0), rear_left, thrust_tip, 2) # Left flame
            pygame.draw.line(surface, (255, 100, 0), rear_right, thrust_tip, 2) # Right flame

def create_fragments(position):
    '''
    Creates ship debris fragments upon destruction.
    
    Arguments:
        position: Position of the ship at time of destruction.
    
    Returns:
        A list of dictionaries representing fragments.
    '''
    x = position[0]
    y = position[1]
    fragments = [] # Create a list for fragments
    fragment_shapes = [
        {'offset_start': [0, 0], 'offset_end': [-8, 20]}, # Left fragment (angled left)
        {'offset_start': [0, 0], 'offset_end': [8, 20]}, # Right fragment (angled right)
        {'offset_start': [-5, 10], 'offset_end': [5, 10]}, # Center fragment (horizontal)
    ]
    
    for shape in fragment_shapes:
        # Randomly determine direction (angle in degrees) and speed for each fragment
        direction = random.uniform(0, 360)
        speed = random.uniform(20, 70)
        # Convert direction and speed into velocity components (vx, vy)
        vx = math.cos(math.radians(direction)) * speed
        vy = math.sin(math.radians(direction)) * speed
        # Append a dictionary with fragment data: start/end points, velocity, and transparency
        fragments.append({
            'start' : [x + shape['offset_start'][0], y + shape['offset_start'][1]],
            'end' : [x + shape['offset_end'][0], y + shape['offset_end'][1]],
            'vx': vx, 'vy': vy,
            'transparency': 255
        })
    return fragments

def depict_fragments(surface, dt):
    '''
    Updates and draws the ship fragments with frading transparency.
    
    Arguments:
        surface: Pygame surface to draw on.
        dt: Delta time since last frame.
    '''
    global ship_fragments
    fade_speed = 100 # Speed at which fragments fade out (alpha decrease per second)
    
    for fragment in ship_fragments[:]: # Iterate over a shallow copy of the fragments list
        # Update position of both start and end points of the fragment based on velocity and delta time
        fragment['start'][0] += fragment['vx'] * dt
        fragment['start'][1] += fragment['vy'] * dt
        fragment['end'][0] += fragment['vx'] * dt
        fragment['end'][1] += fragment['vy'] * dt
        
        # Reduce transparency to create fading effect
        fragment['transparency'] -= fade_speed * dt
        if fragment['transparency'] <= 0:
            # Remove fragment once it is fully transparent
            ship_fragments.remove(fragment)
            continue
        
        # Calculate current alpha value making sure its non-negative
        alpha = max(0, int(fragment['transparency']))
        color = (255, 255, 255, alpha)
        # Create a surface that supports transparency
        line_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line_surface, color,
            (int(fragment['start'][0]), int(fragment['start'][1])),
            (int(fragment['end'][0]), int(fragment['end'][1])), 3)
        surface.blit(line_surface, (0, 0)) # Draw the line onto the main surface

# Asteroid functions
def create_asteroids():
    '''
    Creates a new asteroid with randomized properties including position, velocity, size, rotation, and letter.
    Ensures it doesn't spawn too close to the player's ship.
    
    Returns:
        dict: Dictionary containing asteroid's position, velocity, size, rotation, and letter.
    '''
    global current_wave
    while True:
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        distance_x = abs(x - ship_pos[0])
        distance_y = abs(y - ship_pos[1])
        if distance_x > 100 or distance_y > 100:
            break # Avoid spawning too close to the ship
    
    # Generate random direction and scale speed with wave number     
    angle = random.uniform(0, 360)
    speed = random.uniform(50, 120)
    speed *= (1 + current_wave/10)
    # Calculate velocity components from angle and speed 
    vx = math.cos(math.radians(angle)) * speed
    vy = math.sin(math.radians(angle)) * speed
    # Random letter (excluding 'A'), size, and rotation parameters
    letter = random.choice(string.ascii_uppercase[1:]) # B to Z
    size = random.randint(20, 45)
    size *= (1 + current_wave/10)
    rotation_angle = random.uniform(0, 360)
    rotation_speed = random.uniform(-90, 90)
    
    # Return asteroid as a dictionary of properties
    return {
        'asteroid_position': [x, y],
        'asteroid_velocity': [vx, vy],
        'asteroid_letter': letter,
        'asteroid_size': size,
        'rotation_angle': rotation_angle,
        'rotation_speed': rotation_speed
    }

def init_asteroids():
    '''
    Initializes the asteroid list by appending new asteroids.
    '''
    for _ in range (NUM_ASTEROIDS):
        asteroids.append(create_asteroids())

def split_asteroid(parent):
    '''
    Splits a given asteroid into two smaller ones if it is large enough.
    
    Arguments:
        parent (dict): The asteroid to be split
    
    Returns:
        list: Two new smaller asteroids, or empty list if parent is too small
    '''
    new_asteroids = []
    new_size = 0
    
    # Determine new size based on parent asteroid's size
    if parent['asteroid_size'] >= 90:
        new_size = random.randint(30, 60)
    elif parent['asteroid_size'] >= 50:
        new_size = random.randint(30, 45)
    else:
        return []
    
    # Calculate parent's movement direction and speed
    parent_vx, parent_vy = parent['asteroid_velocity']
    parent_angle = math.degrees(math.atan2(parent_vy, parent_vx))
    parent_speed = math.hypot(parent_vx, parent_vy)
    
    # Create two new asteroids based on parent's motion with some variation
    for _ in range(2):
        angle_offset = random.uniform(-20, 20) # Slight angle deviation
        new_angle = parent_angle + angle_offset
        speed_factor = random.uniform(0.9, 1.1) # Slight speed variation
        new_speed = parent_speed * speed_factor
        vx = math.cos(math.radians(new_angle)) * new_speed
        vy = math.sin(math.radians(new_angle)) * new_speed
        letter = random.choice(string.ascii_uppercase[1:]) # B to Z
        
        # Append new smaller asteroid with position and new velocity and rotation
        new_asteroids.append({
            'asteroid_position': parent['asteroid_position'][:], # Copy position
            'asteroid_velocity': [vx, vy],
            'asteroid_letter': letter,
            'asteroid_size': new_size,
            'rotation_angle': random.uniform(0, 360),
            'rotation_speed': random.uniform(-90, 90)
        })
        
    return new_asteroids

def draw_asteroid(surface, asteroid):
    '''
    Draws an asteroid on the given surface with its associated properties.
    
    Arguments:
        surface: Pygame surface to draw the asteroid
        asteroid (dict): The asteroid properties dictionary
    '''
    
    font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), int(asteroid['asteroid_size'])) # Importing the Comfortaa Font
    text = font.render(asteroid['asteroid_letter'], True, (255, 255, 255)) # Set font size based on asteroid size
    rotated_text = pygame.transform.rotate(text, -asteroid['rotation_angle']) # Rotate text based on asteroid's rotation angle to simulate spinning
    # Determine position to draw the rotated text, centering it on the asteroid's position
    rect = rotated_text.get_rect(center = (int(asteroid['asteroid_position'][0]), int(asteroid['asteroid_position'][1])))
    surface.blit(rotated_text, rect) # Draw the final rotated letter image on the screen at the calculated position

# Bullet functions
def create_bullet():
    '''
    Creates a new bullet object starting from the ship's current position, moving it in the direction the ship is facing
    with a fixed speed and lifespan.
    
    Returns:
        list: Contains bullet's x and y position, velocity components vx and vy, and remanining lifespan
    '''
    
    bullet_angle = ship_angle - 90 # Adjust angle so bullet moves forward relative to ship's orientation
    bullet_speed = 400 # Speed at which bullets travels (pixels per second)
    x = ship_pos[0] # Initial bullet x-position (ship's x)
    y = ship_pos[1] # Initial bullet y-position (ship's y)
    # Calculate velocity components using trigonometry
    vx = math.cos(math.radians(bullet_angle)) * bullet_speed
    vy = math.sin(math.radians(bullet_angle)) * bullet_speed
    return ([x, y, vx, vy, BULLET_LIFESPAN])

def draw_bullets(surface):
    '''
    Draws all active bullets on the given surface as small yellow circles.
    
    Arguments:
        surface: Pygame surface to draw bullets on.
    '''
    for bullet in bullets:
        # Draw a circle at bullet's current position
        pygame.draw.circle(surface, (255, 255, 100), (int(bullet[0]), int(bullet[1])), 3)

# Star functions
def init_stars():
    '''
    Initializes the starfield by creating stars with randomized positions, brightness, twinkle speed, and parallax speed factor.
    Stars are stored as lists.
    '''
    for _ in range(NUM_STARS):
        x = random.randint(0, WIDTH) # Random horizontal position across the screen
        y = random.randint(0, HEIGHT) # Random vertival position across the screen
        brightness = random.randint(100, 255) # Star brightness (controlls how light/dark)
        twinkle_speed = random.choice([-1, 1]) * random.uniform(0.5, 2) # Twinkle speed determines how fast brightness changes, + or - for direction
        speed_factor = random.uniform(0.1, 1.0) # parallax speed
        stars.append([x, y, brightness, twinkle_speed, speed_factor]) # Add star with position, brightness, twinkle speed, and speed_factor

def draw_stars(surface):
    '''
    Updates and draws stars on the screen with a twinkling effect.
    
    Each star's brightness swings between 100 and 255 based on its twinkle speed. The star is rendered as a small circle with its current
    brightness as color.
    
    Arguments:
        surface: Pygame surface to draw the stars on.
    '''
    for star in stars:
        # Update star brightness on twinkle speed
        star[2] += star[3]
        # Reverse direction of twinkle if brightness hits upper limit
        if star[2] > 255:
            star[2] = 255
            star[3] *= -1 # Invert twinkle direction
        # Reverse direction of twinkle if brightness hits lower limit
        elif star[2] < 100:
            star[2] = 100
            star[3] *= -1
        
        # Create a grayscale color based on brightness
        color = (int (star[2]), int(star[2]), int(star[2]))
        # Draw the star as a 1 pixel radius circle at its position
        pygame.draw.circle(surface, color, (star[0], star[1]), 1)

def draw_main_menu(surface):
    '''
    Renders the main menu screen with a background, twinkling stars, the game title, and
    a prompt to start the game.
    
    Arguments:
        surface: Pygame surface to draw the menu on.
    '''
    
    surface.blit(nebula_layer, (0, 0)) # Draw the nebula background image
    draw_stars(surface) # Draw animated stars on top of the background
    
    title_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 50) # Importing Comfortaa Font with text size of 50
    prompt_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 25) # Importing Comfortaa Font with text size of 25
    title_text = title_font.render("ALPHASTROID", True, (255, 255, 255)) # Render game title text
    prompt_text = prompt_font.render("Press SPACE to Start", True, (255, 255, 255)) # Render prompt title text
    title_rect = title_text.get_rect(center=(WIDTH / 2, HEIGHT /2 - 40)) # Center game title on screen
    prompt_rect = prompt_text.get_rect(center=(WIDTH / 2, HEIGHT /2 + 40)) # Center prompt text on screen
    surface.blit(title_text, title_rect) # Draw the title on the surface
    surface.blit(prompt_text, prompt_rect) # Draw the prompt on the surface

def draw_score(surface):
    '''
    Displays the current score on the top left corner of the screen.
    
    Arguments:
        surface: Pygame surface to draw the score on.
    '''
    
    font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 25) # Importing Comfortaa Font
    score_text = f"Score: {score}" # Prepare score text string
    text = font.render(score_text, True, (255, 255, 255)) # Render score text in white color
    surface.blit(text, (10, 10)) # Draw score on the screen at position (10, 10)
    
def draw_wave(surface):
    '''
    Displays the current wave number on the screen just below the score.
    
    Arguments:
        surface: Pygame surface to draw the score on.
    '''
    font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 25) # Importing Comfortaa Font
    lives_text = f"Wave: {current_wave}" # Prepares waves text string
    text = font.render(lives_text, True, (255, 255, 255)) # Render score in white color
    surface.blit(text, (10, 40)) # Draw score on the screen at position (10, 10)

def draw_lives(surface):
    '''
    Displays the player's remaining lives on the screen using the letter 'A' as a visual symbol.
    
    Arguments:
        surface: Pygame surface to draw the lives on.
    '''
    font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 25) # Importing Comfortaa Font
    lives_quantity = "A " * lives # Calculating amount of A's based on lives
    lives_text = f"Lives: {lives_quantity}" # Preparing lives text string
    text = font.render(lives_text, True, (255, 255, 255)) # Render score in white color
    surface.blit(text, (10, 70)) # Draw score on the screen at position (10, 70)

def draw_GAMEOVER(surface):
    '''
    Displays the "Game Over" screen with a rede title and a prompt to restart the game.
    
    Arguments:
        surface: Pygame surface to draw the game over message on.
    '''
    gameover_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 55) # Importing Comfortaa Font
    gameover_text = gameover_font.render("GAME OVER", True, (178, 31, 31)) # Render score in darker red color
    gameover_rect = gameover_text.get_rect(center=(WIDTH / 2, HEIGHT / 2)) # Centering Game over text
    
    playagain_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 15) # Importing Comfortaa Font
    playagain_text = playagain_font.render("Press SPACE to return to Main Menu", True, (255, 255, 255)) # Render score in white color
    playagain_rect = playagain_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 40)) # Centering play again text

    surface.blit(gameover_text, gameover_rect) # Draw game over message on surface
    surface.blit(playagain_text, playagain_rect) # Draw play again message on surface

def draw_instructions(surface):
    '''
    Displays instructions based on how to move and shoot.
    
    Arguments:
        surface: Pygame surface to draw the instructions on
    '''
    instruction_font = pygame.font.Font(("assets/Comfortaa-Regular.ttf"), 16) # Importing Comfortaa Font
    instruction_text = instruction_font.render("Use WASD or Arrow Keys to move. Use Spacebar to shoot", True, (255, 255, 255)) # Render instructions in white color
    instruction_text_rect = instruction_text.get_rect(center=(WIDTH / 2, HEIGHT - 25)) # Positioning instruction text
    surface.blit(instruction_text, instruction_text_rect) # Draw instruction text on surface
    
    surface.blit(wasd_and_arrow_keys, (0, 225)) # Draw wasdandarrowkeys image on surface
    surface.blit(spacebar_key, (400, 245)) # Draw spacebarkey image on surface

def reset_game():
    '''
    Resets the game state to initial conditions. This is called when resetting the game.
    
    Globals Modified:
        ship_pos (list): Ship's position reset to center
        ship_velocity (list): Ship's velocity reset to zero.
        ship_alive (bool): Whether the ship is active.
        invincibility (bool): If the ship is currently invincible after respawn
        lives (int): Reset to 3
        invincibility_timer (int): Timer for invincibility duration
        respawn_timer (int): Timer for respawn duration
        score (int): Resets to 0
        current_wave (int): Resets to 1
        
    '''
    global ship_alive, invincible, invincibility_timer, ship_pos, ship_velocity, ship_fragments, bullets, asteroids
    global score, lives, current_wave
    # Reset ship position and velocity
    ship_pos = [WIDTH // 2, HEIGHT // 2] 
    ship_velocity = [0, 0]
    # Clear ship fragments and set alive status
    ship_alive = True
    invincible = False
    ship_fragments.clear()
    # Clear all bullets and asteroids from the screen
    bullets.clear()
    asteroids.clear()
    # Reset lives and timers
    lives = 3
    invincibility_timer = 0
    respawn_timer = 0
    # Reset score and wave
    score = 0
    current_wave = 1
    # Reinitialize stars and asteroids for a fresh start
    init_stars()
    init_asteroids()

# ~~~ Main Loop ~~~~
running = True
while running:
    # Control frame rate and calculate delta time in seconds for frame independent movement
    dt = clock.tick(FPS) / 1000 # Delta time in seconds
    
    # Handle events such as key presses
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False # This will exit the main loop and close the game
        elif event.type == pygame.KEYDOWN:
            if game_state == "MENU":
                # Start the game from the main menu
                if event.key == pygame.K_SPACE:
                    reset_game()
                    game_state = "PLAYING"
                    instruction_timer = 1 # Set a timer for input upon starting game
            elif game_state == "GAMEOVER":
                # Return to main menu from game over screen
                draw_GAMEOVER(screen)
                if event.key == pygame.K_SPACE:
                    game_state = "MENU"
    
    # Get the current state of all keys for continous input handling
    pressed_keys = pygame.key.get_pressed()
    
    if game_state == "MENU":
        draw_main_menu(screen) # Display main menu screen
    
    elif game_state == "PLAYING":
        # Ship respawning
        if not ship_alive:
            respawn_timer -= dt
            if lives > 0:
                # Respawn ship if lives are left and timer expires
                if respawn_timer <= 0:
                    ship_alive = True
                    invincible = True
                    invincibility_timer = 2 # 2 seconds of invincibility
                    ship_angle = 0
                    ship_pos = [WIDTH / 2, HEIGHT / 2]
                    ship_velocity = [0, 0]
            else:
                # Transition to GAMEOVER if no lives remain
                if respawn_timer <= 0:
                    game_state = "GAMEOVER"
            
        # Invincibility logic
        if invincible:
            invincibility_timer -= dt
            if invincibility_timer <= 0:
                invincible = False

        if instruction_timer > 0:
            instruction_timer -= dt
        
        # Disable instructions after any control key is pressed
        if first_time_instructions_overlay and instruction_timer <= 0 and (
            pressed_keys[pygame.K_w] or pressed_keys[pygame.K_a] or pressed_keys[pygame.K_s] or pressed_keys[pygame.K_d] or
            pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_RIGHT] or
            pressed_keys[pygame.K_SPACE]
        ):
            first_time_instructions_overlay = False                
        
        thrusting = False # Track whether ship is accelerating
    
        if ship_alive:
            # Rotate ship
            if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
                ship_angle -= SHIP_TURN_SPEED * dt
            if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
                ship_angle += SHIP_TURN_SPEED * dt
            
            # Apply thrust in direction the ship is facing
            if pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w]:
                ship_angle_shifted = ship_angle - 90
                ship_velocity[0] += math.cos(math.radians(ship_angle_shifted)) * SHIP_ACCELERATION * dt
                ship_velocity[1] += math.sin(math.radians(ship_angle_shifted)) * SHIP_ACCELERATION * dt
                thrusting = True
                
            # Fire a bullet if space is pressed and cooldown has expired
            if pressed_keys[pygame.K_SPACE] and bullet_timer <= 0:
                bullets.append(create_bullet())
                bullet_timer = BULLET_COOLDOWN
            
        # Ship physics
        # Apply friction to slow the ship over time making the game more controllable
        ship_velocity[0] *= FRICTION
        ship_velocity[1] *= FRICTION
        
        # Cap ship speed to MAX_SPEED using vector normalization (scaling to a magnitude of 1)
        speed = math.hypot(ship_velocity[0], ship_velocity[1]) # Calculate speed using pythagorean theorem
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            ship_velocity[0] *= scale
            ship_velocity[1] *= scale
        
        # Update ship position and wrap around screen edges
        ship_pos[0] = (ship_pos[0] + ship_velocity[0] * dt) % WIDTH
        ship_pos[1] = (ship_pos[1] + ship_velocity[1] * dt) % HEIGHT
        
        # Check for ship asteroid collision
        if ship_alive and not invincible:
            for asteroid in asteroids:
                dx = ship_pos[0] - asteroid['asteroid_position'][0]
                dy = ship_pos[1] - asteroid['asteroid_position'][1]
                distance = math.hypot(dx, dy)
                if distance < asteroid['asteroid_size'] / 2:
                    # Destroy ship and reduce life
                    lives -= 1
                    ship_fragments.extend(create_fragments(ship_pos))
                    ship_alive = False
                    respawn_timer = 1.5 # Delay before respawning
                    break
            
        # Update asteroid position and wrap around screen edges
        for asteroid in asteroids:
            asteroid['asteroid_position'][0] = (asteroid['asteroid_position'][0] + asteroid['asteroid_velocity'][0] * dt) % WIDTH
            asteroid['asteroid_position'][1] = (asteroid['asteroid_position'][1] + asteroid['asteroid_velocity'][1] * dt) % HEIGHT
            asteroid['rotation_angle'] += asteroid['rotation_speed'] * dt
            asteroid['rotation_angle'] %= 360
        
        # Update bullets
        bullet_timer -= dt
        if bullet_timer < 0:
            bullet_timer = 0 # Prevent negative cooldowns
            
        for bullet in bullets[:]: # Use a slice to safely modify list while iterating
            # Update bullet position using its velocity and delta time
            bullet[0] += bullet[2] * dt
            bullet[1] += bullet[3] * dt
            bullet[4] -= dt # Crease the bullet's lifespan
            if bullet[4] <= 0:
                bullets.remove(bullet) # Remove expired bullet
        
        # Check for bullet asteroid collision
        for bullet in bullets[:]: # Again using a slice for a safe removal
            for asteroid in asteroids[:]:
                # Compute distance between bullet and asteroid center
                dx = bullet[0] - asteroid['asteroid_position'][0]
                dy = bullet[1] - asteroid['asteroid_position'][1]
                distance = math.hypot(dx, dy)
                
                # If bullet hits the asteroid (distance less than radius)
                if distance < asteroid['asteroid_size'] / 2:
                    bullets.remove(bullet) # Destroy bullet
                    asteroids.remove(asteroid) # Destroy asteroid
                    score += 100 # Add to player's score
                    
                    # Create smaller asteroids if this one can split
                    children = split_asteroid(asteroid) 
                    asteroids.extend(children) # Add new smaller asteroids
                    break # Bullet can only hit one asteroid
        
        # If all asteroids have been destroyed, start a new wave
        if len(asteroids) == 0:
            current_wave += 1 # Increase wave number
            # Spawn more asteroids with each wave (increasing difficulty)
            for _ in range(NUM_ASTEROIDS + current_wave): 
                asteroids.append(create_asteroids())
                
        # Update stars for parallax based on ship movement and its parallax layer depth
        for star in stars:
            star[0] -= ship_velocity[0] * star[4] * dt
            star[1] -= ship_velocity[1] * star[4] * dt
            # Draw stars around the screen for seamless infinite field
            star[0] %= WIDTH
            star[1] %= HEIGHT
        
        # Drawing
        screen.blit(nebula_layer, (0, 0)) # Draw nebula space background
        if first_time_instructions_overlay:
            draw_instructions(screen) # Draw instructions
        draw_stars(screen) # Dra dynamic parallax stars on top of background
        draw_ship(screen, ship_pos, ship_angle) # Draw the player ship
        for asteroid in asteroids: # Draw all asteroids currently on screen
            draw_asteroid(screen, asteroid)
        depict_fragments(screen, dt) # Draw debris fragments from destroyed ship
        draw_bullets(screen) # Draw all bullets
        draw_score(screen) # Draw score
        draw_lives(screen) # Draw lives
        draw_wave(screen) # Draw wave number
    
    elif game_state == "GAMEOVER":
        # If the game is over, display the "GAME OVER" screen
        draw_GAMEOVER(screen)

    # Update display surface to the screen
    pygame.display.update()

pygame.quit()