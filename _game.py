import pygame
import tmx
import re


class Coin(pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super(Coin, self).__init__(*groups)
        self.direction = 1
        self.image = pygame.image.load('graphics/coin.png')
        self.rect = pygame.rect.Rect(location, self.image.get_size())

    def update(self, dt, game):
        if self.rect.colliderect(game.player.rect):
            game.player.score = game.player.score + 1
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super(Enemy, self).__init__(*groups)
        self.direction = 1
        self.image = pygame.image.load('graphics/spider-left.png')
        self.image_left = self.image
        self.image_right = pygame.image.load('graphics/spider-right.png')
        self.rect = pygame.rect.Rect(location, self.image.get_size())

    def update(self, dt, game):
        self.rect.x += self.direction * 100 * dt
        for cell in game.tilemap.layers['triggers'].collide(self.rect, 'reverse'):
            if self.direction > 0:
                self.image = self.image_left
                self.rect.right = cell.left
            else:
                self.image = self.image_right
                self.rect.left = cell.right
            self.direction *= -1
            break
        if self.rect.colliderect(game.player.rect):
            game.player.is_dead = True


class Bullet(pygame.sprite.Sprite):
    image = pygame.image.load('graphics/bullet.png')

    def __init__(self, location, direction, *groups):
        super().__init__(*groups)
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.direction = direction
        self.lifespan = 1

    def update(self, dt, game):
        self.lifespan -= dt
        if self.lifespan < 0:
            self.kill()
            return
        self.rect.x += self.direction * 400 * dt
        if pygame.sprite.spritecollide(self, game.enemies, True):
            game.player.score = game.player.score + 2
            self.kill()
        if pygame.sprite.spritecollide(self, game.coins, True):
            self.kill()
        new = self.rect
        for cell in game.tilemap.layers['triggers'].collide(new, 'blocker'):
            self.kill()
        for cell in game.tilemap.layers['triggers'].collide(new, 'coin'):
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, location, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load('graphics/nplayer-right.png')
        self.right_image = self.image
        self.left_image = pygame.image.load('graphics/nplayer-left.png')
        self.rect = pygame.rect.Rect(location, self.image.get_size())
        self.resting = False
        self.dy = 0
        self.is_dead = False
        self.direction = 1
        self.gun_cooldown = 0
        self.score = 0

    def update(self, dt, game):
        last = self.rect.copy()
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.rect.x -= 300 * dt
            self.image = self.left_image
            self.direction = -1
        if key[pygame.K_RIGHT]:
            self.rect.x += 300 * dt
            self.image = self.right_image
            self.direction = 1
        if key[pygame.K_DOWN] and not self.gun_cooldown:
            if self.direction > 0:
                Bullet(self.rect.midright, 1, game.sprites)
            else:
                Bullet(self.rect.midleft, -1, game.sprites)
            self.gun_cooldown = 1
        self.gun_cooldown = max(0, self.gun_cooldown - dt)
        if self.resting and key[pygame.K_SPACE]:
            self.dy = -500
        self.dy = min(400, self.dy + 40)
        self.rect.y += self.dy * dt
        new = self.rect
        self.resting = False
        for cell in game.tilemap.layers['triggers'].collide(new, 'blocker'):
            blockers = cell['blocker']
            if 'l' in blockers and last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if 'r' in blockers and last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if 't' in blockers and last.bottom <= cell.top and new.bottom > cell.top:
                self.resting = True
                new.bottom = cell.top
                self.dy = 0
            if 'b' in blockers and last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0
        if self.is_dead is True:
            self.image = pygame.image.load('graphics/player-right.png')
            #self.direction = 0
        game.tilemap.set_focus(new.x, new.y)


class Game():
    def main(self, screen):
        clock = pygame.time.Clock()
        background = pygame.image.load('graphics/background960-512.png')
        self.tilemap = tmx.load('tilemap.tmx', screen.get_size())
        self.sprites = tmx.SpriteLayer()
        start_cell = self.tilemap.layers['triggers'].find('player')[0]
        self.player = Player((start_cell.px, start_cell.py), self.sprites)

        self.tilemap.layers.append(self.sprites)
        self.enemies = tmx.SpriteLayer()
        self.coins = tmx.SpriteLayer()
        for enemy in self.tilemap.layers['triggers'].find('enemy'):
            Enemy((enemy.px, enemy.py), self.enemies)
        for coin in self.tilemap.layers['triggers'].find('coin'):
            Coin((coin.px, coin.py), self.coins)
        self.tilemap.layers.append(self.enemies)
        self.tilemap.layers.append(self.coins)
        foreground = self.tilemap.layers['foreground']
        self.tilemap.layers.append(foreground)

        x = 0
        while x < 1250:
            dt = clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            self.tilemap.update(dt / 1000., self)
            screen.blit(background, (0, 0))
            self.tilemap.draw(screen)
            pygame.font.init()
            score_color = (100, 100, 100)
            score_message = 'Score: ' + str(self.player.score)
            score_font = pygame.font.SysFont('tahoma', 16)
            score_text = score_font.render(score_message, 1, score_color)
            screen.blit(score_text, (875, 15))
            if self.player.is_dead:
                pygame.font.init()
                died_color = (255, 255, 255)
                died_message = 'YOU LOSE!'
                died_font = pygame.font.SysFont('tahoma', 150)
                died_text = died_font.render(died_message, 1, died_color)
                screen.blit(died_text, (x-300, 250))
                x += 10
            pygame.display.flip()
        else:
            Menu().main(screen)


class Menu():
    def main(self, screen):
        clock = pygame.time.Clock()
        background = pygame.image.load('graphics/black_background960-512.png')
        self.tilemap = tmx.load('menu_tilemap.tmx', screen.get_size())
        self.tilemap.set_focus(0, 0)
        while 1:
            dt = clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            self.tilemap.update(dt / 1000., self)
            screen.blit(background, (0, 0))
            self.tilemap.draw(screen)
            pygame.display.flip()
            pos = pygame.mouse.get_pos()
            click = pygame.mouse.get_pressed()
            if click[0] == 1 and 385 < pos[0] < 540 and 160 < pos[1] < 220:
                Game().main(screen)
            if click[0] == 1 and 385 < pos[0] < 540 and 260 < pos[1] < 315:
                pygame.quit()
                exit()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((960, 512))
    Menu().main(screen)

"""
Get system fonts:
import pygame
print(pygame.font.get_fonts())
"""