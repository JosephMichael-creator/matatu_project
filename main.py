import pygame
import random
import sys
import os

# Game settings
WIDTH, HEIGHT = 600, 800
LANES = [150, 300, 450]
MATATU_WIDTH, MATATU_HEIGHT = 60, 120
OBSTACLE_WIDTH, OBSTACLE_HEIGHT = 60, 120
ZEBRA_HEIGHT = 30
FPS = 60

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Autonomous Matatu Simulator')
clock = pygame.time.Clock()

# Load images
ASSETS = os.path.join(os.path.dirname(__file__), 'assets')
MATATU_IMG = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, 'matatuu.png')), (MATATU_WIDTH, MATATU_HEIGHT))
CAR_IMGS = [pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, f'car{i}.png')), (OBSTACLE_WIDTH, OBSTACLE_HEIGHT)) for i in range(1,4)]
ROAD_IMG = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS, 'road.png')), (WIDTH, HEIGHT)) if os.path.exists(os.path.join(ASSETS, 'road.png')) else None

# Colors
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

class Matatu:
    def __init__(self):
        self.lane = 1
        self.x = LANES[self.lane] - MATATU_WIDTH // 2
        self.y = HEIGHT - MATATU_HEIGHT - 20
        self.speed = 8
        self.braking = False
    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.x = LANES[self.lane] - MATATU_WIDTH // 2
    def move_right(self):
        if self.lane < len(LANES) - 1:
            self.lane += 1
            self.x = LANES[self.lane] - MATATU_WIDTH // 2
    def brake(self):
        self.braking = True
    def release_brake(self):
        self.braking = False
    def update(self):
        pass
    def draw(self, surface):
        surface.blit(MATATU_IMG, (self.x, self.y))

class Obstacle:
    def __init__(self, kind):
        self.kind = kind
        self.lane = random.randint(0, len(LANES)-1)
        self.x = LANES[self.lane] - OBSTACLE_WIDTH // 2
        self.y = -OBSTACLE_HEIGHT if kind == 'vehicle' else -ZEBRA_HEIGHT
        self.speed = 8
        if kind == 'vehicle':
            self.img = random.choice(CAR_IMGS)
        else:
            self.img = None
    def update(self):
        self.y += self.speed
    def draw(self, surface):
        if self.kind == 'vehicle' and self.img:
            surface.blit(self.img, (self.x, self.y))
        elif self.kind == 'zebra':
            # Draw a wide yellow base across all lanes
            zebra_x = LANES[0] - OBSTACLE_WIDTH // 2
            zebra_width = (LANES[-1] - LANES[0]) + OBSTACLE_WIDTH
            pygame.draw.rect(surface, YELLOW, (zebra_x, self.y, zebra_width, ZEBRA_HEIGHT))
            # Draw white stripes
            num_stripes = 7
            stripe_width = zebra_width // num_stripes
            for i in range(num_stripes):
                if i % 2 == 0:
                    pygame.draw.rect(surface, WHITE, (zebra_x + i * stripe_width, self.y, stripe_width, ZEBRA_HEIGHT))

    def get_rect(self):
        if self.kind == 'vehicle':
            return pygame.Rect(self.x, self.y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
        else:
            return pygame.Rect(self.x, self.y, OBSTACLE_WIDTH, ZEBRA_HEIGHT)

def main():
    matatu = Matatu()
    obstacles = []
    score = 0
    running = True
    spawn_timer = 0
    zebra_timer = 0
    ZEBRA_INTERVAL = 30 * FPS  # 30 seconds
    font = pygame.font.SysFont(None, 36)
    # For scrolling effect
    road_scroll = 0
    road_speed = 8
    zebra_waiting = False
    zebra_wait_timer = 0
    ZEBRA_STOP_TIME = 5 * FPS  # 5 seconds
    matatu_y_saved = None
    while running:
        # Draw scrolling road background if available
        if ROAD_IMG:
            road_scroll = (road_scroll + road_speed) % HEIGHT
            screen.blit(ROAD_IMG, (0, road_scroll - HEIGHT))
            screen.blit(ROAD_IMG, (0, road_scroll))
        else:
            screen.fill(GRAY)
            # Draw scrolling lane lines
            lane_line_height = 40
            lane_gap = 60
            road_scroll = (road_scroll + road_speed) % (lane_line_height + lane_gap)
            for lane_x in LANES:
                y = -lane_line_height + road_scroll
                while y < HEIGHT:
                    pygame.draw.rect(screen, WHITE, (lane_x - 5, y, 10, lane_line_height))
                    y += lane_line_height + lane_gap
        # Event handling (keep quit event only)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # Spawn obstacles
        spawn_timer += 1
        zebra_timer += 1
        # Regular vehicles
        if spawn_timer > 60:
            kind = 'vehicle'
            obstacles.append(Obstacle(kind))
            spawn_timer = 0
        # Timed zebra crossing
        if zebra_timer > ZEBRA_INTERVAL:
            obstacles.append(Obstacle('zebra'))
            zebra_timer = 0
        # Update obstacles
        for obs in obstacles:
            # If zebra_waiting, obstacles and road keep moving, but matatu stays in place
            if zebra_waiting:
                obs.speed = 8
            else:
                obs.speed = 2 if matatu.braking else 8
            obs.update()
        # Remove off-screen obstacles
        obstacles = [obs for obs in obstacles if obs.y < HEIGHT]
        # Autonomous obstacle avoidance
        matatu_rect = pygame.Rect(matatu.x, matatu.y, MATATU_WIDTH, MATATU_HEIGHT)
        # Find closest obstacle in matatu's lane ahead
        closest = None
        zebra_ahead = None
        for obs in obstacles:
            if obs.lane == matatu.lane and obs.y + (OBSTACLE_HEIGHT if obs.kind == 'vehicle' else ZEBRA_HEIGHT) > 0:
                if obs.y < matatu.y:
                    if closest is None or obs.y > closest.y:
                        closest = obs
                if obs.kind == 'zebra' and obs.y < matatu.y:
                    if zebra_ahead is None or obs.y > zebra_ahead.y:
                        zebra_ahead = obs
        # If zebra crossing is close ahead, brake and stop for 5 seconds
        if zebra_waiting:
            matatu.brake()
            zebra_wait_timer += 1
            if zebra_wait_timer >= ZEBRA_STOP_TIME:
                zebra_waiting = False
                zebra_wait_timer = 0
        elif zebra_ahead and (matatu.y - zebra_ahead.y) < 30:
            zebra_waiting = True
            matatu.brake()
            zebra_wait_timer = 0
            # Move zebra crossing out of the way after stopping
            zebra_ahead.y = HEIGHT + 100
        # Otherwise, avoid vehicles as before
        elif closest and (matatu.y - closest.y) < 200:
            left_lane = matatu.lane - 1
            right_lane = matatu.lane + 1
            safe_left = left_lane >= 0 and not any(o.lane == left_lane and abs(o.y - matatu.y) < 150 for o in obstacles)
            safe_right = right_lane < len(LANES) and not any(o.lane == right_lane and abs(o.y - matatu.y) < 150 for o in obstacles)
            if safe_left:
                matatu.move_left()
            elif safe_right:
                matatu.move_right()
            else:
                matatu.brake()
        else:
            matatu.release_brake()
        # Collision detection
        for obs in obstacles:
            if matatu_rect.colliderect(obs.get_rect()):
                running = False
        # Draw everything
        # Freeze matatu position during zebra crossing stop
        if zebra_waiting:
            if matatu_y_saved is None:
                matatu_y_saved = matatu.y
            matatu.draw(screen)
            for obs in obstacles:
                obs.draw(screen)
        else:
            matatu_y_saved = None
            matatu.draw(screen)
            for obs in obstacles:
                obs.draw(screen)
        # Score
        score += 1
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        pygame.display.flip()
        clock.tick(FPS)
    # Game over
    game_over_text = font.render('Game Over!', True, RED)
    screen.blit(game_over_text, (WIDTH//2 - 100, HEIGHT//2))
    pygame.display.flip()
    pygame.time.wait(2000)
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
