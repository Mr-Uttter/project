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
            scale=(0.5, 0.5, 0.5),
            position=(0, 8, 0),
            collider="box",
            name="player",
        )
        self.texture = "reflection_map_3"
        self.life = 100
        self.max_life = 100
        self.velocity_y = 0

        ic("Player created")

    def ball_rolling_effect(self):

        pass

    def move(self):
        speed = 5
        move_step = speed * time.dt
        directions = {
            "w": (0, 0, move_step),
            "s": (0, 0, -move_step),
            "a": (-move_step, 0, 0),
            "d": (move_step, 0, 0),
            "space": (0, move_step, 0),
            "down arrow": (0, -move_step, 0),
        }

        for key, movement in directions.items():
            if held_keys[key]:
                # Kontrollera rörelseriktningen med raycast
                direction = Vec3(movement[0], movement[1], movement[2]).normalized()
                hit_info = raycast(
                    origin=self.position,
                    direction=direction,
                    distance=move_step + 0.1,
                    ignore=(self,),
                    debug=True,
                )

                if hit_info.hit:
                    ic("Hit detected!")
                    hit = self.player_collision(hit_info)
                    if not hit:
                        self.x += movement[0]
                        self.y += movement[1]
                        self.z += movement[2]

    def player_collision(self, hit_info):
        """Hanterar kollisioner och returnerar True om rörelsen ska blockeras."""
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
        )  # Bakgrund för healthbar
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
        # Uppdatera healthbarens gröna del baserat på liv
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

        self.create_boundry_walls(self.width, self.height)
        #self.create_holes()
        #self.create_spikes()
        #self.create_health_packs()

        ic("World created")


        self.level_data = {
            "walls": [(0, 1, 5), (1, 1, 5), (2, 1, 5), (-1, 1, 5)],  # Positioner för väggar
            "health_packs": [(3, 0, -3), (-4, 0, 2)],               # Positioner för healthpacks
            "spikes": [(2, 0, 2), (-2, 0, -2)],                    # Positioner för spikar
            "holes": [(0, -0.5, -5), (-3, -0.5, 4)],               # Positioner för hål
            "enemies": [(5, 0, -3), (-5, 0, 3)],                   # Positioner för fiender
        }
        self.load_level()
    def load_level(self,):
        """Laddar ett definierat self.level_data och skapar objekten."""
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


    def apply_gravity(self):
        gravity_info = raycast(
            origin=player.position,
            direction=(0, -1, 0),
            distance=0.5,
            ignore=(player,),
            color=color.red,
            debug=True,
        )
        if not gravity_info.hit or gravity_info.entity.name == "hole":
            player.velocity_y -= self.gravity * time.dt
            player.y += player.velocity_y * time.dt  # Ensure time.dt is applied here
        else:
            player.velocity_y = 0  # Reset velocity when hitting the ground
            


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

        # Justera position för nya meddelanden
        if self.texts:
            last_text = self.texts[-1]
            position = (last_text.position[0], last_text.position[1] - 0.1)

        # Skapa textobjektet
        new_text = Text(text=message, position=position, origin=origin, scale=scale, color=c)

        # Ta bort text efter en fördröjning
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
        # Skapa väggar längs X-axeln (övre och nedre kanten)
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

        # Skapa väggar längs Z-axeln (vänster och höger kant)
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
        # Tilldela egenskaper till fienden
        enemy.position = position
        enemy.color = color
        enemy.health = health
        enemy.damage = damage
        enemy.speed = speed
        enemy.attack_range = attack_range  # Fiendens egna attack_range
        enemy.attack_speed = attack_speed
        enemy.enabled = True

        # Lägg till fienden i listan
        self.enemy_entitys.append(enemy)
        ic(f"Spawned {len(self.enemy_entitys)} enemies")


    def enemy_move(self):
        for enemy in self.enemy_entitys:
            if enemy is None:
                ic("Enemy is None!")
                continue  # Hoppa över den här fienden om den är None
            
            if player is None:
                ic("Player is None!")
                continue  # Hoppa över om spelaren inte är definierad
            
            # Räkna ut avståndet mellan spelaren och fienden
            distance_to_player = distance(player.position, enemy.position)

            # Om fienden är inom attack_range, utför attack
            if distance_to_player <= enemy.attack_range:
                enemy.look_at(player)  # Fienden tittar på spelaren

                if distance_to_player > 1:  # Om fienden inte är för nära, rör sig mot spelaren
                    direction = (player.position - enemy.position).normalized()
                    enemy.position += direction * enemy.speed * time.dt

                else:  # Attackera om fienden är tillräckligt nära
                    invoke(healthbar.take_damage, enemy.damage, delay=enemy.attack_speed)
                    world.on_screen_text("You have been attacked!", color.red)



class GameCamera:
    def __init__(self, target):
        self.target = target  # Spelaren som kameran ska följa
        ic("Camera initialized")

    def update_camera(self):
        # Interpolera kamerans position
        camera.position = lerp(
            camera.position,
            (self.target.x, self.target.y + 20, self.target.z - 20),
            0.1,
        )
        camera.look_at(self.target)


# Variabler för spelet och menyn
loaded_entity = {}
screen = None
game_started = False  # Håller koll på om spelet startat
player = None

def start_game():
    """Startar spelet genom att skapa spelobjekt och dölja menyn."""
    global screen, player, game_started
    game_started = True  # Indikerar att spelet är igång
    instanciate()
    # Ta bort menyn
    if screen:
        destroy(screen)

    print("Game started!")

def show_menu():
    """Visar huvudmenyn."""
    global screen
    screen = Entity(parent=camera.ui)

    # Skapa menyknappar
    Button("Play", parent=screen, scale=(0.2, 0.1), y=0.1, on_click=start_game)
    Button("Quit", parent=screen, scale=(0.2, 0.1), y=-0.1, on_click=application.quit)

def instanciate():
    global player, world, healthbar, game_camera, enemies
    if game_started:      
        player = Player()
        healthbar = Healthbar()
        game_camera = GameCamera(player)
        enemies = Enemies()
        world = World()


#def update():
    if game_started:
        game_camera.update_camera()
        if held_keys["l"]:
            healthbar.take_damage(1)
        if held_keys["k"]:
            healthbar.gain_health(1)
        player.move()
        world.apply_gravity()
        enemies.enemy_move()

# Kör spelet
if __name__ == "__main__":
    show_menu()  # Visa menyn först
    app.run()





