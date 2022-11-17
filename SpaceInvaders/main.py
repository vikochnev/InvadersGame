# Обучающий проект, попытка скопировать игру Space Invaders
# by Baklush
# Игровой процесс: На поле есть гаубица игрока, враги - космические захватчики, и, возможно, бункеры, дающие игроку
# защиту, пока не уничтожены. Игрок может двигать гаубицу по оси Х и стрелять вертикальными снарядами, уничтожающими при
# попадании врага. Враги движутся в сторону по оси Х, и, когда один из кораблей достигает края экрана, все корабли
# меняют направление по оси Х на противоположное, а также сдвигаются вниз на заданное кол-во пикселей. Время от времени
# враги стреляют снарядами, разрушающими (при их наличии) бункеры, а также отнимающими у игрока 1 жизнь при попадании
# по гаубице. Если снаряд долетает до низу экрана, он уничтожается, не нанося вреда. Если у игрока осталось 0 жизней,
# или корабль врага достиг нижнего края экрана, игра проиграна. Если не осталось вражеских кораблей, уровень пройден, и
# игрок получает 1 жизнь. В зависимости от количества уничтоженных кораблей, скорость вражеской армады увеличивается.


from superwires import games, color
import random, gc

games.init(screen_width=1280, screen_height=720, fps=60)


class Collider(games.Sprite):
    """Базовый класс, родительский для других классов спрайтов, содержит общие функции"""

    def update(self):
        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                sprite.collision()

    def collision(self):
        """what does object do if collided"""

    def die(self):
        self.destroy()


class PlayerArtillery(Collider):
    """Гаубица игрока"""
    image = games.load_image("player_artillery.bmp")
    STEP = games.screen.fps / 10
    STARTING_HP = 3
    MISSILE_DELAY = games.screen.fps / 2

    def __init__(self, game):
        """Управление гаубицей игрока"""
        super(PlayerArtillery, self).__init__(image=PlayerArtillery.image, x=games.screen.width / 2
                                              , bottom=games.screen.height)
        self.game = game
        self.hit_points = self.STARTING_HP - 1
        self.missile_delay = self.MISSILE_DELAY

    def update(self):
        super(PlayerArtillery, self).update()

        if self.missile_delay > 0:
            self.missile_delay -= 1

        if games.keyboard.is_pressed(games.K_a):
            if self.left > 0:
                self.x -= PlayerArtillery.STEP
            else:
                self.left = 0
        if games.keyboard.is_pressed(games.K_d):
            if self.right < games.screen.width:
                self.x += PlayerArtillery.STEP
            else:
                self.right = games.screen.width
        if games.keyboard.is_pressed(games.K_SPACE):
            if self.missile_delay == 0:
                new_missile = PlayerMissile(self.x)
                games.screen.add(new_missile)
                self.missile_delay = self.MISSILE_DELAY

    def been_hit(self):
        self.hit_points -= 1
        self.game.hit_points_bar.value = "HP: " + str(self.hit_points)
        if self.hit_points <= 0:
            self.die()

    def die(self):
        super(PlayerArtillery, self).die()
        self.game.game_over()


class EnemyShip(Collider):
    """Корабли противников"""
    image = games.load_image("eship.bmp")
    Y_STEP = 25
    flying_right = True
    total = 0
    SPEED_INC = games.screen.fps / 300
    speed = 0
    MISSILE_DELAY = games.screen.fps

    def __init__(self, game, left, top):
        self.game = game
        if self.flying_right:
            self.dx = EnemyShip.speed
        else:
            self.dx = -EnemyShip.speed
        super(EnemyShip, self).__init__(image=EnemyShip.image, left=left, top=top)
        EnemyShip.total += 1
        self.missile_delay = random.randrange(EnemyShip.MISSILE_DELAY, EnemyShip.MISSILE_DELAY * (1 + EnemyShip.total))

    def update(self):
        """Задаёт поведение кораблей противника"""
        super(EnemyShip, self).update()

        # Обновляет скорость кораблей
        if EnemyShip.flying_right:
            self.dx = EnemyShip.speed
        else:
            self.dx = -EnemyShip.speed
        # Проверяет, должно ли измениться направление движения кораблей
        was_flying_right = self.flying_right
        # Проверяет, вышел ли корабль за пределы экрана, если да - меняет направление полета
        if self.right > games.screen.width:
            EnemyShip.flying_right = False
        if self.left < 0:
            EnemyShip.flying_right = True

        if was_flying_right != self.flying_right:
            # Заставляет все корабли поменять направление движения
            ships = []
            for object in gc.get_objects():
                if isinstance(object, EnemyShip):
                    ships.append(object)
            for ship in ships:
                ship.change_direction()

        # Заканчивает игру, если корабль противника опустился слишком низко
        if self.bottom >= self.game.LEVEL_BOTTOM:
            self.game.game_over()

        # Стрельба
        if self.missile_delay > 0:
            self.missile_delay -= 1
        if self.missile_delay == 0:
            new_enemy_missile = EnemyMissile(self.x, self.bottom)
            games.screen.add(new_enemy_missile)
            self.missile_delay = random.randrange(self.MISSILE_DELAY, self.MISSILE_DELAY * (1 + EnemyShip.total))

    def change_direction(self):
        """Меняет направление движение корабля и сдвигает его вниз"""
        if EnemyShip.flying_right:
            self.dx = self.speed
        else:
            self.dx = - self.speed
        self.y += self.Y_STEP

    def die(self):
        super(EnemyShip, self).die()
        EnemyShip.speed += EnemyShip.SPEED_INC  # Увеличивает скорость кораблей при смерти союзника
        EnemyShip.total -= 1
        if EnemyShip.total == 0:
            self.game.advance_level()


class EnemyMissile(Collider):
    """Класс, задающие снаряды, выпускаемые противником"""
    image = games.load_image("emissile.bmp")
    VELOCITY = 3

    def __init__(self, ship_x, ship_y):
        super(EnemyMissile, self).__init__(image=EnemyMissile.image, x=ship_x, top=ship_y + 2
                                           , dy=self.VELOCITY)

    def update(self):
        super(EnemyMissile, self).update()

        # уничтожить снаряд при достижении края экрана
        if self.bottom > games.screen.height:
            self.die()

    def collision(self):
        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                if isinstance(sprite, PlayerArtillery):
                    sprite.been_hit()
                    self.die()


class PlayerMissile(Collider):
    """Класс, задающий снаряды, выпускаемые игроком"""
    image = games.load_image("pmissile.bmp")
    VELOCITY = games.screen.fps / 8

    def __init__(self, player_x):
        super(PlayerMissile, self).__init__(image=PlayerMissile.image, x=player_x, y=games.screen.height - 60
                                            , dy=-self.VELOCITY)

    def update(self):
        super(PlayerMissile, self).update()

        # уничтожить снаряд при достижении края экрана
        if self.top < 0:
            self.die()

    def collision(self):
        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                if isinstance(sprite, EnemyShip):
                    sprite.die()
                    self.die()


class Game:
    """Основной класс, отвечает за запуск и основные процессы игры"""
    BASE_ENEMY_SPEED = games.screen.fps / 30
    BUFFER_X = 50
    BUFFER_Y = 30
    START_X = 50
    START_Y = 50
    LEVEL_BOTTOM = 600

    def __init__(self):
        """Инициализировать объект игры"""
        self.is_game_over = False
        self.level = 0
        self.player = PlayerArtillery(game=self)
        games.screen.add(self.player)
        # отобразить здоровье
        self.hit_points_bar = games.Text(value="HP: " + str(self.player.hit_points),
                                         size=30,
                                         color=color.white,
                                         top=5,
                                         right=games.screen.width - 10,
                                         is_collideable=False)
        games.screen.add(self.hit_points_bar)

    def play(self):
        """Основной процесс игры"""
        background = games.load_image("background.jpg", transparent=False)
        games.screen.background = background
        self.advance_level()

        games.screen.mainloop()

    def create_foes(self, in_row=1, columns=1):
        for j in range(columns):
            for i in range(in_row):
                self.enemy_ship = EnemyShip(game=self,
                                            left=self.START_X + (EnemyShip.image.get_width() + self.BUFFER_X) * i
                                            , top=self.START_Y + (EnemyShip.image.get_height() + self.BUFFER_Y) * j)
                games.screen.add(self.enemy_ship)

    def advance_level(self):
        EnemyShip.flying_right = True  # Меняет направление движения вражеских кораблей на Вправо
        EnemyShip.speed = self.BASE_ENEMY_SPEED  # Устанавливает начальную скорость движения вражеских кораблей

        self.player.hit_points += 1  # Прибавляет игроку 1 жизнь
        self.hit_points_bar.value = "HP: " + str(self.player.hit_points)
        # Уничтожает снаряды
        for object in gc.get_objects():
            if isinstance(object, PlayerMissile) or isinstance(object, EnemyMissile):
                object.destroy()

        self.create_foes(7, 4)

    def game_over(self):
        """Проигрыш, конец игры"""
        self.end()
        self.is_game_over = True

    def end(self):
        """Высвечивает сообщение конца игры"""
        if self.is_game_over == False:
            end_message = games.Message(value="Game Over",
                                        size=90,
                                        color=color.red,
                                        x=games.screen.width / 2,
                                        y=games.screen.height / 2,
                                        lifetime=5 * games.screen.fps,
                                        after_death=games.screen.quit,
                                        is_collideable=False)
            games.screen.add(end_message)


def main():
    spaceInvaders = Game()
    spaceInvaders.play()


main()
