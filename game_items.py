import pygame
import random
import hashlib

SCREEN_RECT = pygame.Rect(0, 0, 480, 700)
FRAME_INTERVAL = 10

# 英雄飞机默认炸弹数量
HERO_BOMB_COUNT = 3
# 英雄飞机默认初始位置
HERO_DEFAULT_MID_BOTTOM = (SCREEN_RECT.centerx, SCREEN_RECT.bottom - 90)
# 英雄飞机牺牲事件
HERO_DEAD_EVENT = pygame.USEREVENT
# 取消英雄飞机无敌事件
HERO_POWER_OFF_EVENT = pygame.USEREVENT + 1
# 英雄飞机发射子弹事件
HERO_FIRE_EVENT = pygame.USEREVENT + 2
# 道具固定时间生成事件
PROPS_GENERATE = pygame.USEREVENT + 3


class GameSprite(pygame.sprite.Sprite):
    """游戏精灵类"""
    res_path = "./res/images/"  # 图片资源路径

    def __init__(self, image_name, speed, *groups):
        """构造方法
        :param image_name: 要加载的图片文件名
        :param speed: 移动速度
        :param groups: 要添加到的精灵组，不传值则不添加
        """
        super().__init__(*groups)
        # 图像
        self.image = pygame.image.load(self.res_path + image_name)
        self.rect = self.image.get_rect()   # 矩形区域，默认在左上角
        self.speed = speed                  # 移动速度
        # 图像遮罩，可以提高碰撞检测的执行性能
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        """更新精灵位置，默认在垂直方向移动"""
        self.rect.y += self.speed


class Background(GameSprite):
    """背景精灵类"""
    def __init__(self, is_alt, *groups):
        # 调用父类方法实现精灵的创建
        super().__init__("background.png", 1, *groups)
        # 判断是否是另一个精灵，如果是，需要设置初始位置
        if is_alt:
            self.rect.y = -self.rect.h      # 设置到游戏窗口正上方

    def update(self, *args):
        # 调用父类的方法实现向下移动
        super().update(*args)               # 向下运动
        # 判断是否移出屏幕，如果移出屏幕，将图像设置到屏幕的上方
        if self.rect.y >= self.rect.h:
            self.rect.y = -self.rect.h


class StatusButton(GameSprite):
    """状态按钮类"""
    def __init__(self, image_names, *groups):
        """构造方法
        :param image_names: 要加载的图像名称列表
        :param groups: 要添加到的精灵组
        """
        super().__init__(image_names[0], 0, *groups)
        # 加载图像
        self.images = []
        for name in image_names:
            self.images.append(pygame.image.load(self.res_path + name))

    def switch_status(self, is_pause):
        """切换状态
        :param is_pause: 是否暂停
        """
        self.image = self.images[1 if is_pause else 0]


class Label(pygame.sprite.Sprite):
    """文本标签精灵"""
    font_path = "./res/font/MarkerFelt.TTF"     # 字体文件路径

    def __init__(self, text, size, color, *groups):
        """构造方法
        :param text: 文本内容
        :param size: 字体大小
        :param color: 字体颜色
        :param groups: 要添加到的精灵组
        """
        super().__init__(*groups)
        self.font = pygame.font.Font(self.font_path, size)
        self.color = color
        self.image = self.font.render(text, True, self.color)
        self.rect = self.image.get_rect()

    def set_text(self, text):
        """设置文本，使用指定的文本重新渲染 image，并且更新 rect
        :param text: 文本内容
        """
        self.image = self.font.render(text, True, self.color)
        self.rect = self.image.get_rect()


class Plane(GameSprite):
    """飞机类"""
    def __init__(self, hp, speed, value, wav_name, normal_names,
                 hurt_name, destroy_names, *groups):
        """构造方法
        :param hp: 当前生命值
        :param speed: 速度
        :param value: 敌机被摧毁后的分值
        :param wav_name: 被摧毁时播放的音效文件名
        :param normal_names: 记录正常飞行状态的图像名称列表
        :param hurt_name: 受损图像文件名
        :param destroy_names: 摧毁状态图像名称列表
        :param groups: 要添加到的精灵组
        """
        super().__init__(normal_names[0], speed, *groups)
        # 飞机属性
        self.hp = hp
        self.max_hp = hp
        self.value = value
        self.wav_name = wav_name
        # 图像属性
        # 正常图像列表及索引
        self.normal_images = [pygame.image.load(self.res_path + name) for name in normal_names]
        self.normal_index = 0
        # 受伤图像
        self.hurt_image = pygame.image.load(self.res_path + hurt_name)
        # 被摧毁图像列表及索引
        self.destroy_images = [pygame.image.load(self.res_path + name)
                               for name in destroy_names]
        self.destroy_index = 0

    def reset_plane(self):
        """重置飞机"""
        self.hp = self.max_hp               # 重置生命值
        self.normal_index = 0               # 重置飞机正常状态图像索引
        self.destroy_index = 0              # 重置被摧毁状态图像索引
        self.image = self.normal_images[0]  # 恢复正常图像

    def update(self, *args):
        # 如果第 1 个参数为 False，则不需要更新图像，直接返回
        if not args[0]:
            return
        # 判断飞机状态
        if self.hp == self.max_hp or self.hp > self.max_hp // 2:        # 未受伤
            self.image = self.normal_images[self.normal_index]
            count = len(self.normal_images)
            self.normal_index = (self.normal_index + 1) % count
        elif 0 < self.hp <= self.max_hp // 2:                           # 受伤
            self.image = self.hurt_image
        else:
            # 判断是否显示到最后一张图像，若是说明飞机被完全摧毁
            if self.destroy_index < len(self.destroy_images):
                self.image = self.destroy_images[self.destroy_index]
                self.destroy_index += 1
            else:
                self.reset_plane()


class Enemy(Plane):
    """敌机类"""
    def __init__(self, kind, max_speed, *groups):
        """构造方法
        :param kind: 敌机类型。0：小敌机，1：中敌机，2：大敌机
        :param max_speed: 最大速度
        """
        # 记录敌机类型和最大速度
        self.kind = kind
        self.max_speed = max_speed
        # 根据类型调用父类方法传递不同参数
        if kind == 0:
            super().__init__(1, 1, 100, "enemy1_down.wav",
                             ["enemy1.png"], "enemy1.png",
                             ["enemy1_down_{}.png".format(i) for i in range(1, 5)], *groups)
        elif kind == 1:
            super().__init__(35, 1, 500, "enemy2_down.wav",
                             ["enemy2.png"], "enemy2_hit.png",
                             ["enemy2_down_{}.png".format(i) for i in range(1, 5)], *groups)
        else:
            super().__init__(200, 1, 1500, "enemy3_down.wav",
                             ["enemy3_n1.png", "enemy3_n2.png"], "enemy3_hit.png",
                             ["enemy3_down_{}.png".format(i) for i in range(1, 7)], *groups)

        # 调用重置飞机方法，设置敌机初始位置和速度
        self.reset_plane()

    def reset_plane(self):
        """重置飞机"""
        super().reset_plane()
        # 设置初始随机位置和速度
        self.speed = self.max_speed
        # 设置随机 x 值
        x = random.randint(10, SCREEN_RECT.w - self.rect.w)
        # 设置随机 y 值
        y = random.randint(10, SCREEN_RECT.h - self.rect.h) - SCREEN_RECT.h
        self.rect.topleft = (x, y)

    def update(self, *args):
        """更新图像和位置"""
        # 调用父类方法更新敌机图像
        super().update(*args)
        # 判断敌机是否被摧毁，则根据速度更新敌机的位置
        if self.hp > 0:
            self.rect.y += self.speed
        else:
            self.rect.y += (self.max_speed // 2) + 1
        # 判断是否飞出屏幕，如果是，重置敌机
        if self.rect.y >= SCREEN_RECT.h:
            self.reset_plane()


class Hero(Plane):
    """英雄飞机类"""
    def __init__(self, invincible_image, *groups):
        """
        :param invincible_image: 无敌状态
        :param groups: 要添加到的精灵组
        """
        super().__init__(1000, 5, 0, "explode.mp3",
                         ["mel_n{}.png".format(i) for i in range(1, 4)],
                         "mel_n1.png", ["mel_down_{}.png".format(i) for i in range(1, 7)],
                         *groups)
        self.is_power = False                       # 无敌判断标记
        self.bomb_count = HERO_BOMB_COUNT           # 炸弹数量
        self.bullets_kind = 0                       # 子弹类型
        self.bullets_group = pygame.sprite.Group()  # 子弹精灵组
        self.fire_count = 1                         # 一次性发射 1 颗子弹
        # 无敌状态
        self.invincible_image = pygame.image.load(self.res_path + invincible_image)
        # 初始位置
        self.rect.midbottom = HERO_DEFAULT_MID_BOTTOM
        # 设置 0.1s 发射子弹定时器事件
        pygame.time.set_timer(HERO_FIRE_EVENT, 100)

    def update(self, *args):
        """更新英雄飞机的图像及矩形区域
        :param args: 0 更新图像标记， 1 水平移动基数， 2 垂直移动基数
        """
        # 调用父类方法更新飞机图像
        super().update(*args)
        # 无敌状态
        if self.is_power:
            self.image = self.invincible_image
        # 英雄飞机在摧毁状态时，不能发射子弹
        elif self.hp <= 0:
            self.fire_count = 0
        # 如果没有传递方向基数或者英雄飞机被摧毁，直接返回
        if len(args) != 3 or self.hp <= 0:
            return
        # 调整水平移动距离
        self.rect.x += args[1] * self.speed
        self.rect.y += args[2] * self.speed
        # 限定在游戏窗口内部移动
        self.rect.x = 0 if self.rect.x < 0 else self.rect.x
        if self.rect.right > SCREEN_RECT.right:
            self.rect.right = SCREEN_RECT.right
        self.rect.y = 0 if self.rect.y < 0 else self.rect.y
        if self.rect.bottom > SCREEN_RECT.bottom:
            self.rect.bottom = SCREEN_RECT.bottom

    def fire(self, display_group):
        """发射子弹
        :param display_group: 要添加的显示精灵组
        """
        # 需要将子弹精灵添加到 2 个精灵组
        groups = (self.bullets_group, display_group)
        for i in range(self.fire_count):
            # 创建子弹精灵
            bullet1 = Bullet(self.bullets_kind, *groups)
            # 计算子弹重置位置
            y = self.rect.y - i * 30
            # 判断子弹类型
            if self.bullets_kind == 0:
                bullet1.rect.midbottom = (self.rect.centerx, y + 20)
            elif self.bullets_kind == 1:
                y += 50
                bullet1.rect.midbottom = (self.rect.centerx - 30, y)
                # 再创建一颗子弹
                bullet2 = Bullet(self.bullets_kind, *groups)
                bullet2.rect.midbottom = (self.rect.centerx + 30, y)
            else:
                bullet1.rect.midbottom = (self.rect.centerx - 10, y + 20)
                bullet7 = Bullet(1, *groups)
                bullet7.rect.midbottom = (self.rect.centerx + 10, y + 20)

                bullet2 = Bullet(0, *groups, right=True)
                bullet2.rect.midbottom = (self.rect.centerx + 33, y + 50)
                bullet3 = Bullet(0, *groups, left=True)
                bullet3.rect.midbottom = (self.rect.centerx - 33, y + 50)
                bullet4 = Bullet(0, *groups, right=True)
                bullet4.rect.midbottom = (self.rect.centerx + 18, y + 50)
                bullet6 = Bullet(0, *groups, left=True)
                bullet6.rect.midbottom = (self.rect.centerx - 18, y + 50)

    def blowup(self, enemies_group):
        """引爆炸弹
        :param enemies_group: 敌机精灵组
        :return: 累计得分
        """
        # 如果没有足够数量的炸弹或者英雄飞机被摧毁，直接返回
        if self.bomb_count <= 0 or self.hp <= 0:
            return 0
        self.bomb_count -= 1            # 炸弹数量 -1
        score = 0                       # 本次得分
        count = 0                       # 炸毁数量
        # 遍历敌机精灵组，将游戏窗口内的敌机引爆
        for enemy in enemies_group.sprites():
            # 判断敌机是否进入敌机窗口
            if enemy.rect.bottom > 0:
                score += enemy.value    # 计算得分
                count += 1              # 累计数量
                enemy.hp = 0            # 摧毁敌机
        print("炸毁了 {} 架敌机，得分 {} 分".format(count, score))
        return score

    def reset_plane(self):
        """重置英雄飞机"""
        super().reset_plane()
        self.is_power = True                # 无敌判断标记
        self.bomb_count = HERO_BOMB_COUNT   # 炸弹数量
        self.bullets_kind = 0               # 子弹类型
        self.fire_count = 1                 # 子弹发射数量
        # 发布英雄牺牲事件
        pygame.event.post(pygame.event.Event(HERO_DEAD_EVENT))
        # 设置 3s 之后取消无敌状态定时器事件
        pygame.time.set_timer(HERO_POWER_OFF_EVENT, 3000)


class Bullet(GameSprite):
    """子弹类"""
    def __init__(self, kind, *groups, right=False, left=False):
        """构造方法
        :param kind: 子弹类型
        :param groups: 要添加到的精灵组
        """
        image_name = "bullet1.png" if kind == 0 else "bullet2.png"
        super().__init__(image_name, -12, *groups)
        self.damage = 1         # 杀伤力
        self.right = right      # 子弹往右
        self.left = left        # 子弹往左

    def update(self, *args):
        super().update(*args)
        # 判断是否从上方飞出窗口
        if self.rect.bottom < 0:
            self.kill()
        elif self.rect.left < 0 or self.rect.right > SCREEN_RECT.w:
            self.kill()
        if self.right:
            self.rect.x += 1
        if self.left:
            self.rect.x += -1


class Props(GameSprite):
    """道具类"""
    def __init__(self, image_name, *groups):
        """
        :param image_name: 道具图片名称
        """
        self.image_name = image_name
        super().__init__(self.image_name, 0, *groups)
        # 道具刷新时间为 35s
        pygame.time.set_timer(PROPS_GENERATE, 35000)
        # 重置位置
        self.reset_plane(0)

    def update(self, *args):
        super().update(*args)
        # 判断是否掉落屏幕外
        if self.rect.top > SCREEN_RECT.h:
            self.reset_plane(0)

    def reset_plane(self, speed):
        """重置道具位置"""
        self.speed = speed
        x = random.randint(10, SCREEN_RECT.w - self.rect.w)
        y = random.randint(10, SCREEN_RECT.h - self.rect.h) - SCREEN_RECT.h
        self.rect.topleft = (x, y)


class UpBullet(Props):
    """升级子弹道具类"""
    def __init__(self, images_name, *groups):
        super().__init__(images_name, *groups)
        self.props_kind = 1     # 道具类型


class BombCount(Props):
    """炸弹道具类"""
    def __init__(self, images_name, *groups):
        super().__init__(images_name, *groups)
        self.props_kind = 0     # 道具类型

