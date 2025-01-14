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
            position=(0, 5, 0),
            collider="box",
            name="player",
        )
        self.texture = "reflection_map_3"
        self.origin=(0,-1,0)
        self.life = 100
        self.max_life = 100
        

        ic("Player created")

    def ball_rolling_effect(self):
        pass

    def move(self):
        speed = 5
        move_step = speed * time.dt

        if held_keys["w"]:  # Framåt
            self.handle_movement(Vec3(0, -0.5, move_step))

        if held_keys["s"]:
            self.handle_movement(Vec3(0, -0.5, -move_step))

        if held_keys["a"]:
            self.handle_movement(Vec3(-move_step, -0.5, 0))

        if held_keys["d"]:
            self.handle_movement(Vec3(move_step, -0.5, 0))

        if held_keys["space"]:
            self.handle_movement(Vec3(0, move_step, 0))

        if held_keys["down arrow"]:
            self.handle_movement(Vec3(0, -move_step, 0))


    def handle_movement(self, movement):
        
        direction = movement.normalized()
        hit_info = raycast(
            origin=self.position,
            direction=direction,
            distance=movement.length() + 0.1,
            ignore=(self,),
            debug=True,
        )

        if not hit_info.hit:
            self.position.x += movement[0]
            self.position.z += movement[2]
        else:
            ic("Hit detected!")
            hit = self.player_collision(hit_info)
            if not hit:
                self.position.x += movement[0]
                self.position.z += movement[2]

        world.apply_gravity(hit_info)


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
        #self.create_holes()
        #self.create_spikes()
        #self.create_health_packs()

        ic("World created")


        self.level_data = {
            "walls": [(0, 1, 5), (1, 1, 5), (2, 1, 5), (-1, 1, 5)],  
            "health_packs": [(3, 0, -3), (-4, 0, 2)],
            "spikes": [(2, 0, 2), (-2, 0, -2)],
            "holes": [(0, -0.5, -5), (-3, -0.5, 4)],
            "enemies": [(5, 0, -3), (-5, 0, 3)],
        }
        self.load_level()
    def load_level(self,):
        """ Creates level from level data """
        for wall_pos in self.level_data.get("walls", []):
            Entity(
                model="cube",
                color=color.gray,
                texture="brick",
                position=wall_pos,
                scale=(1, self.wall_thickness, 1),
                collider="box",
                name="stop",
            )

        for health_pack_pos in self.level_data.get("health_packs", []):
            Entity(
                model="cube",
                color=color.green,
                position=health_pack_pos,
                scale=(1.5, 1.5, 1.5),
                name="health_pack",
                collider="box",
            )

        for spike_pos in self.level_data.get("spikes", []):
            Entity(
                model="cube",
                color=color.red,
                position=spike_pos,
                scale=(1.5, 1, 1.5),
                name="spike",
                collider="box",
            )

        for hole_pos in self.level_data.get("holes", []):
            Entity(
                model="cube",
                color=color.brown,
                position=hole_pos,
                scale=(2, 2, 2),
                name="hole",
                collider="box",
            )

        for enemy_pos in self.level_data.get("enemies", []):
            enemy = enemies.spawn_small_enemy(position=enemy_pos)
            enemies.enemy_entitys.append(enemy)


    def apply_gravity(self, hit_info):

        if not hit_info.hit:
            self.velocity_y -= world.gravity * time.dt
            self.y += self.velocity_y * time.dt
        else:
            self.velocity_y = 0  # Återställ hastigheten om spelaren är på marken
                


    def create_spikes(self):
        self.spike = Entity(
            model="cube",
            color=color.red,
            position=(5, 0, -3),
            scale=(1.5, 1, 1.5),
            name="spike",
            collider="box",
        )

        self.spikes = []

        for i in range(self.level):
            spike = duplicate(
                self.spike,
                position=(
                    random.randint(-self.height // 2, self.height // 2),
                    0,
                    random.randint(-self.width // 2, self.width // 2),
                ),
            )
            self.spikes.append(spike)
        ic("Spikes created")

    def create_health_packs(self):
        self.health_pack = Entity(
            model="cube",
            color=color.green,
            position=(5, 0, -3),
            scale=(1.5, 1.5, 1.5),
            name="health_pack",
            collider="box",
        )

        self.health_packs = []

        for i in range(self.level):
            health_pack = duplicate(
                self.health_pack,
                position=(
                    random.randint(-self.height // 2, self.height // 2),
                    0,
                    random.randint(-self.width // 2, self.width // 2),
                ),
            )
            self.health_packs.append(health_pack)
        ic("Health packs created")

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

    def create_holes(self):
        self.hole = Entity(
            model="cube",
            color=color.brown,
            position=(5, -0.5, -3),
            scale=(2, 2, 2),
            name="hole",
            collider="box",
        )

        self.holes = []

        for i in range(self.level):
            hole = duplicate(
                self.hole,
                position=(
                    random.randint(-self.height // 2, self.height // 2),
                    -0.5,
                    random.randint(-self.width // 2, self.width // 2),
                ),
            )
            self.holes.append(hole)
        ic("Obstacles created")

    def create_boundry_walls(
        self,
        width,
        height,
        wall_thickness=1,
        wall_color=color.gray,
        wall_texture="brick",
    ):
        walls = []

        self.ground = Entity(
            model="plane",
            color=color.green,
            position=(0, 0, 0),
            scale=(width, 0, height),
            texture="grass",
            name="grass",
            collider="box",
        )
        # Create boundry walls, top and bottom
        for x in range(-width // 2, width // 2 + 1):
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(x, 1, -height // 2),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(x, 1, height // 2),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(x, 2, -height // 2),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(x, 2, height // 2),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )

        # Create boundry walls, left and right
        for z in range(-height // 2, height // 2 + 1):
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(-width // 2, 1, z),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(width // 2, 1, z),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(-width // 2, 2, z),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
            )
            walls.append(
                Entity(
                    model="cube",
                    color=wall_color,
                    texture=wall_texture,
                    position=(width // 2, 2, z),
                    scale=(1, wall_thickness, 1),
                    collider="box",
                    name="stop",
                )
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
                ic("Enemy is None!")
                continue 
            
            if player is None:
                ic("Player is None!")
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
        player.move()
        game_camera.update_camera()
        if held_keys["l"]:
            healthbar.take_damage(1)
        if held_keys["k"]:
            healthbar.gain_health(1)
        #world.apply_gravity()
        enemies.enemy_move()

# Run the game part
if __name__ == "__main__":
    show_menu()  # Shows the menu first
    app.run()





