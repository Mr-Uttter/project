from icecream import ic
from ursina import *
import random

# Initiate the game engine
app = Ursina()


class Player(Entity):
    def __init__(self):
        super().__init__(
            model="sphere",
            color=color.orange,
            scale=(0.75, 0.75, 0.75),
            position=(0, 3, 0),
            collider="box",
            name="player",
        )
        self.texture = "reflection_map_3"
        self.origin=(0,0.25,0)
        self.life = 100
        self.max_life = 100
        

        ic("Player created")

    def ball_rolling_effect(self):
        pass

    def move(self):
        speed = 5
        move_step = speed * time.dt

        if held_keys["w"]:  
            self.handle_movement(Vec3(0, 0, move_step), move_step)

        if held_keys["s"]:
            self.handle_movement(Vec3(0, 0, -move_step), move_step)

        if held_keys["a"]:
            self.handle_movement(Vec3(-move_step, 0, 0), move_step)

        if held_keys["d"]:
            self.handle_movement(Vec3(move_step, 0, 0), move_step)

        if held_keys["space"]:
            self.handle_movement(Vec3(0, move_step, 0), move_step)

        if held_keys["down arrow"]:
            self.handle_movement(Vec3(0, -move_step, 0), move_step)


    def handle_movement(self, movement, move_step):
        
        direction = movement.normalized()
        cast_thickness = .5
        hit_info = boxcast(
            origin=self.position,
            thickness=cast_thickness,
            direction=direction,
            distance=move_step + 0.3,
            ignore=(self,),
            debug=True,
        )

        hit = False
        
        if hit_info.hit:
            ic("Hit detected!")
            hit = self.player_collision(hit_info)
        if not hit:
            self.position += movement
            self.position += movement

        


    def player_collision(self, hit_info):
        """ Handles collision with entitys """
        if hit_info.entity.name == "stop":
            return True

        elif hit_info.entity.name == "hole":
            world.on_screen_text("Fell into hole!", c=color.red)
            self.position = (0, 2, 0)
            return True

        elif hit_info.entity.name == "health_pack":
            healthbar.gain_health(10)
            world.on_screen_text("Picked up health pack!", c=color.green)
            destroy(hit_info.entity)
            return False

        elif hit_info.entity.name == "spike":
            world.on_screen_text("Stepped on spike!", c=color.red)
            healthbar.take_damage(10)
            return False

        return False


class Healthbar(Entity):
    def __init__(self):
        self.healthbar_bg = Entity(
            model="quad",
            color=color.red,
            scale=(0.2, 0.01),
            position=(-0.85, 0.45),
            parent=camera.ui,
        )  # Red part of healthbar
        self.healthbar = duplicate(
            self.healthbar_bg, color=color.green, position=(-0.85, 0.45)
        )
        self.healthbar_bg.origin = (-0.5, 0)
        self.healthbar.origin = (-0.5, 0)
        self.health_text = Text(
            text="Health",
            scale=(1, 1),
            position=(-0.85, 0.49),
            color=color.black,
            parent=camera.ui,
        )

    def take_damage(self, amount):
        player.life -= amount

        if player.life < 0:
            player.life = 0
        self.update_healthbar()

    def gain_health(self, amount):
        player.life += amount

        if player.life < 0:
            player.life = 0
        self.update_healthbar()

    def update_healthbar(self):
        # Green part of healthbar update
        self.healthbar.scale_x = player.life / player.max_life * 0.2
        ic(f"Health: {player.life}%")



class World(Entity):
    def __init__(self):
        super().__init__()
        self.level = 4
        self.wall_size = 1
        self.wall_thickness = 1
        self.wall_level = 10
        self.width = 30
        self.height = 30
        self.gravity = 9.8
        self.velocity_y = 0
        self.create_boundry_walls(self.width, self.height)
        #self.create_holes()            # Randomly creates holes, for testing
        #self.create_spikes()           # Randomly creates spikes, for testing
        #self.create_health_packs()     # Randomly creates health packs, for testing

        ic("World created")

        self.levels = [
            {
                "Level one"
                "walls": [
                    (x, 1, z)
                    for x in range(-14, 15, 3)
                    for z in range(-14, 15, 3)
                    if (x + z) % 2 == 0
                ],
                "health_packs": [(0, 1, -10), (-10, 1, 10)],
                "spikes": [(3, 1, 3), (-3, 1, -3), (6, 1, -6)],
                "holes": [(0, -0.5, 5), (-5, -0.5, -5)],
                "enemies": [(-10, 1, -10), (10, 1, 10)],
                "player_start": (0, 3, 0),
                "width": 30,
                "height": 30,
            },
            {
                # Level two
                "walls": [],
                "health_packs": [(5, 1, -5)],
                "spikes": [(0, 1, z) for z in range(-14, 15, 4)],
                "holes": [(-5, -0.5, z) for z in range(-14, 15, 8)],
                "enemies": [(-10, 1, -10), (0, 1, -10), (10, 1, 10)],
                "player_start": (-10, 3, -12),
                "width": 30,
                "height": 30,
            },
            {
                # Level three
                "walls": [
                    (x, 1, z)
                    for x, z in [
                        (-10, -10), (-10, -9), (-10, -8), (-9, -8), (-8, -8), (-8, -7), (-8, -6),
                        (-7, -6), (-6, -6), (-6, -5), (-6, -4), (-5, -4), (-4, -4),
                    ]
                ],
                "health_packs": [(-4, 1, -4)],
                "spikes": [(0, 1, 0)],
                "holes": [],
                "enemies": [(4, 1, 4)],
                "player_start": (-10, 3, -11),
                "width": 30,
                "height": 30,
            }
        ]

        self.load_level()


    def load_level(self, level_index=2):
        """Laddar en specifik bana baserat på index."""
        if level_index < 0 or level_index >= len(self.levels):
            print("Level index out of range!")
            return

        level = self.levels[level_index]

        # Destroy old level
        destroy(self.ground)
        for e in self.children:
            destroy(e)

        # Load objects and borders
        self.width = level["width"]
        self.height = level["height"]
        self.create_boundry_walls(self.width, self.height)

        
        player.position = level["player_start"]

        
        for wall_pos in level.get("walls", []):
            Entity(
                model="cube",
                color=color.gray,
                texture="brick",
                position=wall_pos,
                scale=(1, self.wall_thickness, 1),
                collider="box",
                name="stop",
            )

        for health_pack_pos in level.get("health_packs", []):
            Entity(
                model="cube",
                color=color.green,
                position=health_pack_pos,
                scale=(1.5, 1.5, 1.5),
                name="health_pack",
                collider="box",
            )

        for spike_pos in level.get("spikes", []):
            Entity(
                model="cube",
                color=color.red,
                position=spike_pos,
                scale=(1.5, 1, 1.5),
                name="spike",
                collider="box",
            )

        for hole_pos in level.get("holes", []):
            Entity(
                model="cube",
                color=color.brown,
                position=hole_pos,
                scale=(2, 2, 2),
                name="hole",
                collider="box",
            )

        for enemy_pos in level.get("enemies", []):
            enemy = enemies.spawn_small_enemy(position=enemy_pos)
            enemies.enemy_entitys.append(enemy)


    def apply_gravity(self,):
        falling = raycast(
            direction=Vec3(0,-1,0),
            distance=0.5,
            origin=(player.position),
            ignore=(player,),
            debug=True,
            color=color.red,
        )

        ic(self.velocity_y)
        if not falling.hit:
            self.velocity_y -= self.gravity * time.dt
            player.position = (player.position.x, player.position.y + self.velocity_y * time.dt, player.position.z)
            ic(player.position.y)
        else:
            self.velocity_y = 0
            player.y = falling.world_point.y + 0.4  # +0.5 to land on ground, not partly inside
            ic(player.y)
                

    def on_screen_text(self, message, position=(0, 0.45), origin=(0, 0), scale=2, c=color.black):
        if not hasattr(self, 'texts'):
            self.texts = []

        # Adjust position for new messages
        if self.texts:
            last_text = self.texts[-1]
            position = (last_text.position[0], last_text.position[1] - 0.1)

        # Create text
        new_text = Text(text=message, position=position, origin=origin, scale=scale, color=c)

        # Remove text
        invoke(self.remove_text, new_text, delay=2)

    def remove_text(self, text_obj):
        if text_obj in self.texts:
            self.texts.remove(text_obj)
        destroy(text_obj)


    def create_boundry_walls(
        self,
        width,
        height,
        wall_thickness=1,
        wall_color=color.gray,
        wall_texture="brick",
    ):

        self.ground = Entity(
            model="cube",
            color=color.green,
            position=(0, 0.25, 0),
            scale=(width, 0, height),
            texture="grass",
            name="grass",
            collider="box",
        )

        wall_positions = []

        for x in range(-width // 2, width // 2 + 1):
            for y in (1, 2): 
                wall_positions.append((x, y, -height // 2)) 
                wall_positions.append((x, y, height // 2))  

        
        for z in range(-height // 2, height // 2 + 1):
            for y in (1, 2):  
                wall_positions.append((-width // 2, y, z))  
                wall_positions.append((width // 2, y, z))  

        
        for pos in wall_positions:
            Entity(
                model="cube",
                color=wall_color,
                texture=wall_texture,
                position=pos,
                scale=(1, wall_thickness, 1),
                collider="box",
                name="stop",
            )


class Enemies(Entity):
    def __init__(self):
        super().__init__()
        self.enemy_entitys = []
        

    def spawn_small_enemy(self, position=(5,0,2), color=color.azure, health=50, damage= 8, speed=2, attack_range=8, attack_speed=0.3):
        enemy = Entity(
            model="cube", 
            scale=(1, 2, 1), 
            collider="box"
        )
        # Enemy attributes
        enemy.position = position
        enemy.color = color
        enemy.health = health
        enemy.damage = damage
        enemy.speed = speed
        enemy.attack_range = attack_range  
        enemy.attack_speed = attack_speed
        enemy.enabled = True

        self.enemy_entitys.append(enemy)
        ic(f"Spawned {len(self.enemy_entitys)} enemies")


    def enemy_move(self):
        for enemy in self.enemy_entitys:
            if enemy is None:
                continue 
            
            if player is None:
                continue 
            
            # Calculate distance to player
            distance_to_player = distance(player.position, enemy.position)

            if distance_to_player <= enemy.attack_range:
                enemy.look_at(player)  # Look at player

                if distance_to_player > 1:  # If enemy within range, but to far, walk towards player
                    direction = (player.position - enemy.position).normalized()
                    enemy.position += direction * enemy.speed * time.dt

                else:  # Enemy attack if within range
                    invoke(healthbar.take_damage, enemy.damage, delay=enemy.attack_speed)
                    world.on_screen_text("You have been attacked!", color.red)



class GameCamera:
    def __init__(self, target):
        self.target = target 
        ic("Camera initialized")

    def update_camera(self):
        # Camera Position
        camera.position = lerp(
            camera.position,
            (self.target.x, self.target.y + 20, self.target.z - 20),
            0.1,
        )
        camera.look_at(self.target)


# Game/Menu variables
loaded_entity = {}
screen = None
game_started = False  # Flag if game is running
player = None

def start_game():
    """ Hide the main menu and start game """
    global screen, player, game_started
    game_started = True  # Flag if game is running
    instanciate()
    # Destroy menu
    if screen:
        destroy(screen)

    print("Game started!")

def show_menu():
    """ Main Menu """
    global screen
    screen = Entity(parent=camera.ui)

    # Create menybuttons
    Button("Play", parent=screen, scale=(0.2, 0.1), y=0.1, on_click=start_game)
    # HighScoreButton that show top 10 
    # "settings" for choosing diffuculty, pherhaps easy, medium and hard?
    Button("Quit", parent=screen, scale=(0.2, 0.1), y=-0.1, on_click=application.quit)

def instanciate():
    global player, world, healthbar, game_camera, enemies
    if game_started:      
        player = Player()
        healthbar = Healthbar()
        game_camera = GameCamera(player)
        enemies = Enemies()
        world = World()


def update():
    if game_started:
        world.apply_gravity()
        player.move()
        game_camera.update_camera()
        if held_keys["l"]:
            healthbar.take_damage(1)
        if held_keys["k"]:
            healthbar.gain_health(1)

        enemies.enemy_move()

# Run the game part
if __name__ == "__main__":
    show_menu()  # Shows the menu first
    app.run()




# Todo:
# Create highscore button
# Create highscore savefile
# Create point system?
# Limit height for player jumps
# Better levels, dynamic level rotation, harder the further you go
# Add defence for player, gun? Shield?
# Sounds?
# Add a goal, collect x and get to goal?
# Add gates
# Perhaps fix graphical attributes to make more appealing?
#
# Add some more comments as I go? 
# Clean code from "IC" prints
# 
