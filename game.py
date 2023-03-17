import sys

from game_items import *
from game_hud import *
from game_music import *


class Game(object):
    """游戏类"""

    def __init__(self):
        # 游戏主窗口
        self.main_window = pygame.display.set_mode(SCREEN_RECT.size)
        pygame.display.set_caption("飞机大战")
        # 游戏状态属性
        self.is_game_over = False   # 游戏结束标记
        self.is_pause = False       # 游戏暂停标记

        # 精灵组属性
        self.all_group = pygame.sprite.Group()              # 所有精灵组
        self.enemies_group = pygame.sprite.Group()          # 敌机精灵组
        self.supplies_group = pygame.sprite.Group()         # 道具精灵组

        # 创建精灵
        self.b1 = Background(False)
        self.b2 = Background(True)
        self.all_group.add(self.b1, self.b2)      # 背景精灵，交替滚动
        # 指示器面板
        self.hud_panel = HudPanel(self.all_group)
        # 创建敌机
        self.create_enemies()
        # 创建英雄
        self.hero = Hero('mel_nb.png', self.all_group)
        # 设置面板中炸弹数量
        self.hud_panel.show_bomb(self.hero.bomb_count)
        # 创建道具精灵
        group = (self.supplies_group, self.all_group)
        self.up_bullet = UpBullet('props1.png', *group)       # 创建升级子弹道具类
        self.bomb_add = BombCount('props2.png', *group)       # 创建炸弹道具

        # 创建声音对象
        self.player = MusicPlayer()
        self.player.play_music()

    def create_enemies(self):
        """根据关卡级别创建不同数量的敌机"""
        # 敌机精灵组中的精灵数量
        count = len(self.enemies_group.sprites())
        # 要添加到的精灵组
        groups = (self.all_group, self.enemies_group)
        # 判断关卡级别及以有的敌机数量
        if self.hud_panel.level == 1 and count == 0:        # 关卡1
            for i in range(7):
                Enemy(0, 3, *groups)
        elif self.hud_panel.level == 2 and count == 7:      # 关卡2
            # 提高背景移动速度
            self.b1.speed = 2
            self.b2.speed = 2
            # 提高敌机的最大速度
            for enemy in self.enemies_group.sprites():
                enemy.max_speed = 5
            # 创建敌机
            for i in range(2):
                Enemy(0, 3, *groups)
            for i in range(2):
                Enemy(1, 3, *groups)
        elif self.hud_panel.level == 3 and count == 11:     # 关卡3
            # 提高背景移动速度
            self.b1.speed = 4
            self.b2.speed = 4
            # 提高敌机的最大速度
            for enemy in self.enemies_group.sprites():
                enemy.max_speed = 5 if enemy.kind == 0 else 3
            # 创建敌机
            for i in range(2):
                Enemy(1, 3, *groups)
            for i in range(2):
                Enemy(2, 1, *groups)

    def check_collide(self):
        """碰撞检测"""
        # 检测英雄飞机和敌机的碰撞，若英雄飞机处于无敌状态，彼此不发生碰撞
        if not self.hero.is_power:
            collide_enemies = pygame.sprite.spritecollide(
                self.hero, self.enemies_group, False, pygame.sprite.collide_mask)
            # 过滤掉已经被摧毁的敌机
            collide_enemies = list(filter(lambda x: x.hp > 0, collide_enemies))
            for enemy in collide_enemies:
                enemy.hp = 0        # 摧毁发生碰撞的敌机
            if collide_enemies:
                self.hero.hp = 0    # 英雄同样被摧毁
        # 检测英雄飞机和道具的碰撞
        collide_bullet = pygame.sprite.spritecollide(
            self.hero, self.supplies_group, False, pygame.sprite.collide_mask)
        for i in collide_bullet:
            # 1 为子弹升级道具，0 为炸弹道具
            if i.props_kind == 1:
                self.hero.bullets_kind += 1
                self.up_bullet.reset_plane(0)
            else:
                self.hero.bomb_count += 1
                self.hud_panel.show_bomb(self.hero.bomb_count)
                self.bomb_add.reset_plane(0)

        # 检测敌机是否被子弹击中
        hit_enemies = pygame.sprite.groupcollide(self.enemies_group,
                                                 self.hero.bullets_group,
                                                 False, False,
                                                 pygame.sprite.collide_mask)
        # 遍历字典
        for enemy in hit_enemies:
            # 已经被摧毁的敌机，不需要浪费子弹
            if enemy.hp <= 0:
                continue
            # 遍历击中敌机的子弹列表
            for bullet in hit_enemies[enemy]:
                # 将子弹从所有精灵组中清除
                bullet.kill()
                # 修改敌机的生命值
                enemy.hp -= bullet.damage
                # 如果敌机没有被摧毁，继续判定下一颗子弹
                if enemy.hp > 0:
                    continue
                # 修改游戏得分并判定是否升级
                if self.hud_panel.increase_score(enemy.value):
                    print("升级到关卡{}".format(self.hud_panel.level))
                    self.create_enemies()
                # 退出子弹列表循环
                break

    def reset_game(self):
        """重置游戏"""
        self.is_game_over = False           # 游戏结束标记
        self.is_pause = False               # 游戏暂停标记
        self.hud_panel.reset_panel()        # 重置指示器面板

        # 清空所有飞机
        for enemy in self.enemies_group:
            enemy.kill()
        # 清空残留子弹
        for bullet in self.hero.bullets_group:
            bullet.kill()
        # 清空道具
        for props in self.supplies_group:
            props.kill()
        # 重新创建敌机
        self.create_enemies()

    def event_handler(self):
        """事件监听
        :return: 如果监听到退出事件，返回True，否则返回False
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.is_game_over:                   # 游戏已经结束
                    self.reset_game()                   # 重新开始游戏
                else:
                    self.is_pause = not self.is_pause   # 切换暂停状态
                    # 暂停或恢复背景音乐
                    self.player.pause_music(self.is_pause)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_u:
                self.hero.bullets_kind += 1
            # 判断是否正在游戏
            if not self.is_game_over and not self.is_pause:
                # 监听发射子弹事件
                if event.type == HERO_FIRE_EVENT:
                    self.hero.fire(self.all_group)
                # 监听取消英雄飞机无敌事件
                if event.type == HERO_POWER_OFF_EVENT:
                    print('取消无敌状态...')
                    self.hero.is_power = False
                    # 取消定时器
                    pygame.time.set_timer(HERO_POWER_OFF_EVENT, 0)
                # 监听英雄飞机牺牲事件
                if event.type == HERO_DEAD_EVENT:
                    print('英雄牺牲了...')
                    # 生命数 -1
                    self.hud_panel.lives_count -= 1
                    # 更新生命数显示
                    self.hud_panel.show_lives()
                    # 更新炸弹显示
                    self.hud_panel.show_bomb(self.hero.bomb_count)

                # 监听道具生成事件
                if event.type == PROPS_GENERATE:
                    self.up_bullet.reset_plane(3)
                    self.bomb_add.reset_plane(4)

                # 监听我家按下 F 键, 引爆1颗炸弹
                if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                    # 炸毁所有敌机
                    score = self.hero.blowup(self.enemies_group)
                    # 更新炸弹数量显示
                    self.hud_panel.show_bomb(self.hero.bomb_count)
                    # 更新游戏得分，若关卡等级提升，则可创建新类型的敌机
                    if self.hud_panel.increase_score(score):
                        print("升级到关卡{}".format(self.hud_panel.level))
                        self.create_enemies()
        return False

    def start(self):
        """开始游戏"""
        frame_counter = 0               # 定义逐帧动画计数器
        clock = pygame.time.Clock()     # 游戏时钟
        while True:                     # 游戏循环
            # 生命数为 0 ，表示游戏结束
            self.is_game_over = self.hud_panel.lives_count == 0

            if self.event_handler():    # 事件监听
                # 在游戏关闭前，保存最高分数
                self.hud_panel.save_best_score()
                return

            # 判断游戏状态
            if self.is_game_over:
                # 游戏结束，显示结束面板
                self.hud_panel.panel_pause(True, self.all_group)
            elif self.is_pause:
                # 游戏暂停，显示暂停面板
                self.hud_panel.panel_pause(False, self.all_group)
            else:
                # 游戏正常运行，面板关闭
                self.hud_panel.panel_resume(self.all_group)
                # 碰撞检测
                self.check_collide()
                # 获取当前时刻的按键元组
                keys = pygame.key.get_pressed()
                # 水平移动基数
                move_hor = keys[pygame.K_d] - keys[pygame.K_a]
                # 重置移动基数
                move_ver = keys[pygame.K_s] - keys[pygame.K_w]

                # 修改逐帧动画计数器
                frame_counter = (frame_counter + 1) % FRAME_INTERVAL
                # 更新 all_group 中所有精灵内容
                self.all_group.update(frame_counter == 0, move_hor, move_ver)

            self.all_group.draw(self.main_window)   # 绘制 all_group 中的所有精灵

            pygame.display.update()                 # 更新画面
            clock.tick(60)                          # 设置游戏帧率


if __name__ == '__main__':
    pygame.init()       # 初始化模块
    Game().start()      # 开启游戏循环
    pygame.quit()
    sys.exit()

