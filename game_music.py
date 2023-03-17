import pygame
import random
import os

SOUND_NAME = os.listdir('./res/sound/')


class MusicPlayer:
    """音乐播放器类"""
    res_path = './res/sound/'

    def __init__(self):
        # 加载背景音乐
        pygame.mixer.music.load(self.res_path + SOUND_NAME[random.randint(0, len(SOUND_NAME) - 1)])
        pygame.mixer.music.set_volume(0.2)

    @staticmethod
    def play_music():
        pygame.mixer.music.play(-1)

    @staticmethod
    def pause_music(is_pause):
        """暂停或播放"""
        if is_pause:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
