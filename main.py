import pygame
import os
import sys
import math
import random
import json
from pygame.locals import *
from datetime import datetime

# 初始化
pygame.init()
pygame.mixer.init()

# 版本信息
VERSION = "beta 0.3.0"
GAME_NAME = "PyTonk 游戏"

# 颜色定义
BACKGROUND = (15, 15, 30)
PRIMARY = (70, 130, 180)
ACCENT = (255, 105, 180)
TEXT_COLOR = (240, 240, 255)
HIGHLIGHT = (255, 215, 0)
ERROR_COLOR = (255, 50, 50)
SUCCESS_COLOR = (50, 205, 50)

# 自适应渲染系统
class AdaptiveRenderer:
    def __init__(self):
        self.base_width = 1280
        self.base_height = 720
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
    def update(self, screen):
        """动态检测分辨率并计算缩放因子"""
        current_width, current_height = screen.get_size()
        width_ratio = current_width / self.base_width
        height_ratio = current_height / self.base_height
        self.scale_factor = min(width_ratio, height_ratio)
        self.offset_x = (current_width - self.base_width * self.scale_factor) / 2
        self.offset_y = (current_height - self.base_height * self.scale_factor) / 2
    
    def transform_pos(self, x, y):
        """转换坐标到当前分辨率"""
        scaled_x = x * self.scale_factor + self.offset_x
        scaled_y = y * self.scale_factor + self.offset_y
        return scaled_x, scaled_y
    
    def transform_size(self, size):
        """转换尺寸到当前分辨率"""
        return size * self.scale_factor
    
    def transform_rect(self, rect):
        """转换矩形到当前分辨率"""
        x, y, w, h = rect
        scaled_x = x * self.scale_factor + self.offset_x
        scaled_y = y * self.scale_factor + self.offset_y
        scaled_w = w * self.scale_factor
        scaled_h = h * self.scale_factor
        return (scaled_x, scaled_y, scaled_w, scaled_h)

# 音符系统
class NoteSystem:
    def __init__(self, renderer):
        self.renderer = renderer
        self.notes = []
        self.note_types = {
            'tap': {'color': (0, 200, 255), 'size': 25, 'score': 100},
            'hold': {'color': (255, 150, 0), 'size': 30, 'score': 150},
            'flick': {'color': (200, 0, 255), 'size': 28, 'score': 200},
            'drag': {'color': (0, 255, 100), 'size': 26, 'score': 180},
            'special': {'color': (255, 215, 0), 'size': 35, 'score': 300}
        }
        self.active_notes = []
        self.missed_notes = 0
        self.combo = 0
        self.max_combo = 0
        self.score = 0
        
    def add_note(self, note_type, time, lane, duration=0):
        """添加多类型音符"""
        if note_type not in self.note_types:
            note_type = random.choice(list(self.note_types.keys()))
        
        note = {
            'type': note_type,
            'time': time,
            'lane': lane,
            'duration': duration,
            'state': 'inactive',  # inactive, active, hit, missed
            'progress': 0,
            'hit_time': 0,
            'effect': None
        }
        
        self.notes.append(note)
        return note
    
    def generate_song_notes(self, song_duration, difficulty=1.0):
        """为歌曲生成音符"""
        self.notes = []
        note_count = int(song_duration * difficulty / 1.5)
        
        for _ in range(note_count):
            note_type = random.choice(list(self.note_types.keys()))
            time = random.randint(2000, int(song_duration * 1000) - 2000)
            lane = random.randint(0, 7)
            duration = random.randint(300, 1000) if note_type in ['hold', 'drag'] else 0
            
            self.add_note(note_type, time, lane, duration)
        
        # 按时间排序
        self.notes.sort(key=lambda x: x['time'])
    
    def update(self, current_time):
        """更新音符状态"""
        # 激活音符
        for note in self.notes:
            if note['state'] == 'inactive' and current_time >= note['time'] - 1500:
                note['state'] = 'active'
                self.active_notes.append(note)
        
        # 更新活动音符
        for note in self.active_notes[:]:
            note['progress'] = (current_time - note['time']) / 1000.0
            
            # 检查是否错过
            if note['state'] == 'active' and current_time > note['time'] + 300:
                note['state'] = 'missed'
                self.missed_notes += 1
                self.combo = 0
                self.active_notes.remove(note)
        
        # 更新连击奖励
        combo_bonus = 1.0 + (min(self.combo, 100) / 100.0)
        return combo_bonus

# 判定线系统
class JudgmentLine:
    def __init__(self, renderer):
        self.renderer = renderer
        self.x = 640
        self.y = 500
        self.angle = 0
        self.speed = 0
        self.amplitude = 100
        self.movement_type = "sine"
        self.last_update = pygame.time.get_ticks()
        self.movement_patterns = {
            "sine": self.sine_movement,
            "circle": self.circle_movement,
            "random": self.random_movement,
            "zigzag": self.zigzag_movement
        }
    
    def update(self):
        """更新判定线位置（实现乱飞效果）"""
        current_time = pygame.time.get_ticks()
        delta = (current_time - self.last_update) / 1000.0
        self.last_update = current_time
        
        # 应用当前运动模式
        if self.movement_type in self.movement_patterns:
            self.movement_patterns[self.movement_type](current_time)
    
    def sine_movement(self, time):
        """正弦运动"""
        self.angle = math.sin(time / 1000) * 30
        self.x = 640 + math.sin(time / 800) * self.amplitude
        self.y = 500 + math.sin(time / 1200) * self.amplitude * 0.5
    
    def circle_movement(self, time):
        """圆周运动"""
        self.x = 640 + math.cos(time / 1200) * self.amplitude
        self.y = 500 + math.sin(time / 1200) * self.amplitude
    
    def random_movement(self, time):
        """随机跳跃"""
        if random.random() > 0.98:
            self.x = random.randint(200, 1000)
            self.y = random.randint(300, 600)
    
    def zigzag_movement(self, time):
        """锯齿运动"""
        t = time / 1000
        self.x = 640 + math.sin(t * 2) * self.amplitude
        self.y = 500 + math.sin(t * 3) * self.amplitude * 0.5
        self.angle = math.sin(t) * 45

    def transform_coords(self, x, y):
        """转换坐标到判定线坐标系"""
        rad = math.radians(-self.angle)
        dx = x - self.x
        dy = y - self.y
        rotated_x = dx * math.cos(rad) - dy * math.sin(rad)
        rotated_y = dx * math.sin(rad) + dy * math.cos(rad)
        return rotated_x, rotated_y

# 成就系统
class AchievementSystem:
    def __init__(self):
        self.achievements = {
            'first_play': {'name': '初次游玩', 'desc': '完成第一次游戏', 'achieved': False, 'icon': '🎮'},
            'full_combo': {'name': '完美连击', 'desc': '达成全连击', 'achieved': False, 'icon': '🌟'},
            'master': {'name': '节奏大师', 'desc': '在困难难度获得S评价', 'achieved': False, 'icon': '👑'},
            'no_miss': {'name': '无懈可击', 'desc': '无失误完成歌曲', 'achieved': False, 'icon': '💯'},
            'high_score': {'name': '高分玩家', 'desc': '得分超过500,000', 'achieved': False, 'icon': '🏆'},
            'specialist': {'name': '特技专家', 'desc': '击中50个特殊音符', 'achieved': False, 'icon': '🎯'},
            'long_combo': {'name': '连击之王', 'desc': '达成100+连击', 'achieved': False, 'icon': '🔥'},
            'song_complete': {'name': '歌曲达人', 'desc': '完成所有歌曲', 'achieved': False, 'icon': '🎵'}
        }
        self.unlocked = []
    
    def unlock(self, achievement_id):
        if achievement_id in self.achievements and not self.achievements[achievement_id]['achieved']:
            self.achievements[achievement_id]['achieved'] = True
            self.unlocked.append(achievement_id)
            return True
        return False
    
    def check_achievements(self, game_stats):
        """检查成就条件"""
        if game_stats['games_played'] >= 1:
            self.unlock('first_play')
        if game_stats['max_combo'] >= 100:
            self.unlock('long_combo')
        if game_stats['max_combo'] == game_stats['total_notes'] and game_stats['total_notes'] > 0:
            self.unlock('full_combo')
        if game_stats['misses'] == 0 and game_stats['games_played'] > 0:
            self.unlock('no_miss')
        if game_stats['score'] > 500000:
            self.unlock('high_score')
        if game_stats['special_hits'] >= 50:
            self.unlock('specialist')
        if game_stats['rank'] == 'S' and game_stats['difficulty'] == '困难':
            self.unlock('master')
        if game_stats['completed_songs'] == 12:
            self.unlock('song_complete')

# 自动校准系统
class AutoCalibration:
    def __init__(self):
        self.offset = 0
        self.samples = []
        self.calibration_complete = False
        self.calibration_step = 0
        self.calibration_times = [pygame.time.get_ticks() + 2000, pygame.time.get_ticks() + 4000, 
                                 pygame.time.get_ticks() + 6000, pygame.time.get_ticks() + 8000]
    
    def start_calibration(self):
        """开始校准过程"""
        self.samples = []
        self.calibration_step = 0
        self.calibration_complete = False
        self.calibration_times = [pygame.time.get_ticks() + 2000, pygame.time.get_ticks() + 4000, 
                                 pygame.time.get_ticks() + 6000, pygame.time.get_ticks() + 8000]
    
    def update_calibration(self, current_time):
        """更新校准状态"""
        if self.calibration_step < len(self.calibration_times):
            if current_time >= self.calibration_times[self.calibration_step]:
                self.calibration_step += 1
                if self.calibration_step == len(self.calibration_times):
                    self.calculate_offset()
                    return True
        return False
    
    def add_sample(self, input_time, expected_time):
        """添加校准样本"""
        self.samples.append(input_time - expected_time)
        if len(self.samples) > 10:
            self.samples.pop(0)
        
        # 计算平均偏移
        if len(self.samples) > 2:
            self.offset = sum(self.samples) / len(self.samples)
    
    def calculate_offset(self):
        """计算最终偏移量"""
        if self.samples:
            self.offset = sum(self.samples) / len(self.samples)
            self.calibration_complete = True
    
    def adjust_time(self, time):
        """根据校准结果调整时间"""
        return time - self.offset

# 音乐库系统
class MusicLibrary:
    def __init__(self):
        self.songs = []
        self.load_songs()
    
    def load_songs(self):
        """加载歌曲列表"""
        # 12首预定义歌曲
        self.songs = [
            {
                "id": "song1",
                "title": "电子脉冲",
                "artist": "数字节奏",
                "duration": 120,  # 秒
                "difficulty": {"简单": 0.7, "中等": 1.0, "困难": 1.5},
                "bpm": 128,
                "file": "Music/song1.mp3"
            },
            {
                "id": "song2",
                "title": "星光之旅",
                "artist": "宇宙之声",
                "duration": 150,
                "difficulty": {"简单": 0.8, "中等": 1.1, "困难": 1.6},
                "bpm": 110,
                "file": "Music/song2.mp3"
            },
            {
                "id": "song3",
                "title": "机械心跳",
                "artist": "未来工厂",
                "duration": 135,
                "difficulty": {"简单": 0.9, "中等": 1.2, "困难": 1.7},
                "bpm": 140,
                "file": "Music/song3.mp3"
            },
            {
                "id": "song4",
                "title": "夏日微风",
                "artist": "自然之声",
                "duration": 125,
                "difficulty": {"简单": 0.6, "中等": 1.0, "困难": 1.4},
                "bpm": 100,
                "file": "Music/song4.mp3"
            },
            {
                "id": "song5",
                "title": "城市之夜",
                "artist": "霓虹灯影",
                "duration": 140,
                "difficulty": {"简单": 0.8, "中等": 1.1, "困难": 1.5},
                "bpm": 95,
                "file": "Music/song5.mp3"
            },
            {
                "id": "song6",
                "title": "深海探险",
                "artist": "海洋探索者",
                "duration": 160,
                "difficulty": {"简单": 0.7, "中等": 1.0, "困难": 1.3},
                "bpm": 85,
                "file": "Music/song6.mp3"
            },
            {
                "id": "song7",
                "title": "云端漫步",
                "artist": "天空之城",
                "duration": 130,
                "difficulty": {"简单": 0.9, "中等": 1.2, "困难": 1.8},
                "bpm": 120,
                "file": "Music/song7.mp3"
            },
            {
                "id": "song8",
                "title": "沙漠风暴",
                "artist": "荒野旅人",
                "duration": 145,
                "difficulty": {"简单": 0.8, "中等": 1.1, "困难": 1.6},
                "bpm": 115,
                "file": "Music/song8.mp3"
            },
            {
                "id": "song9",
                "title": "森林之歌",
                "artist": "绿色守护者",
                "duration": 128,
                "difficulty": {"简单": 0.7, "中等": 1.0, "困难": 1.4},
                "bpm": 105,
                "file": "Music/song9.mp3"
            },
            {
                "id": "song10",
                "title": "火山爆发",
                "artist": "熔岩之心",
                "duration": 155,
                "difficulty": {"简单": 0.9, "中等": 1.3, "困难": 1.9},
                "bpm": 145,
                "file": "Music/song10.mp3"
            },
            {
                "id": "song11",
                "title": "极光之舞",
                "artist": "北极星",
                "duration": 138,
                "difficulty": {"简单": 0.8, "中等": 1.1, "困难": 1.5},
                "bpm": 98,
                "file": "Music/song11.mp3"
            },
            {
                "id": "song12",
                "title": "时间旅行",
                "artist": "时空旅者",
                "duration": 148,
                "difficulty": {"简单": 0.7, "中等": 1.0, "困难": 1.4},
                "bpm": 110,
                "file": "Music/song12.mp3"
            }
        ]
    
    def get_song_by_id(self, song_id):
        """根据ID获取歌曲"""
        for song in self.songs:
            if song["id"] == song_id:
                return song
        return None
    
    def get_all_songs(self):
        """获取所有歌曲"""
        return self.songs

# 游戏主类
class PyTonkGame:
    def __init__(self):
        # 初始化系统
        self.renderer = AdaptiveRenderer()
        self.judgment_line = JudgmentLine(self.renderer)
        self.note_system = NoteSystem(self.renderer)
        self.achievements = AchievementSystem()
        self.calibration = AutoCalibration()
        self.music_library = MusicLibrary()
        
        # 游戏状态
        self.game_state = "main_menu"  # main_menu, song_select, playing, pause, results, achievements, settings
        self.screen = None
        self.clock = pygame.time.Clock()
        self.start_time = 0
        self.current_time = 0
        self.song_duration = 0
        self.song_position = 0
        self.difficulty = "中等"  # 简单, 中等, 困难
        self.difficulties = {"简单": 0.7, "中等": 1.0, "困难": 1.5}
        self.skin = "default"
        self.show_tutorial = True
        self.show_calibration = True
        self.current_song_id = None
        
        # 游戏统计
        self.game_stats = {
            'score': 0,
            'combo': 0,
            'max_combo': 0,
            'accuracy': 0.0,
            'hits': 0,
            'perfect_hits': 0,
            'good_hits': 0,
            'misses': 0,
            'total_notes': 0,
            'special_hits': 0,
            'games_played': 0,
            'play_time': 0,
            'rank': "F",
            'difficulty': self.difficulty,
            'completed_songs': 0,
            'unlocked_achievements': 0
        }
        
        # 设备优化
        self.device_type = "tablet"  # 自动检测或手动设置
        self.vibration_enabled = True
        
        # 加载资源
        self.load_resources()
        
        # 初始化回放系统
        self.replay_data = []
        self.recording = False
        self.playback_speed = 1.0
        
        # 初始化编辑器
        self.editor_active = False
        self.editor_time = 0
        self.selected_note_type = "tap"
        
        # 加载歌曲完成状态
        self.load_progress()
    
    def load_resources(self):
        """加载游戏资源"""
        # 先加载字体
        self.title_font = pygame.font.SysFont("Arial", 72, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.medium_font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 28)
        self.tiny_font = pygame.font.SysFont("Arial", 22)
        
        # 创建动态背景
        self.background = pygame.Surface((1280, 720))
        self.generate_dynamic_background()
        
        # 加载按钮
        self.buttons = {
            "play": {"rect": (500, 300, 280, 60), "text": "开始游戏"},
            "achievements": {"rect": (500, 380, 280, 60), "text": "成就系统"},
            "settings": {"rect": (500, 460, 280, 60), "text": "游戏设置"},
            "editor": {"rect": (500, 540, 280, 60), "text": "关卡编辑器"},
            "exit": {"rect": (500, 620, 280, 60), "text": "退出游戏"},
            "back": {"rect": (50, 50, 120, 50), "text": "返回"},
            "easy": {"rect": (400, 400, 200, 60), "text": "简单"},
            "medium": {"rect": (400, 480, 200, 60), "text": "中等"},
            "hard": {"rect": (400, 560, 200, 60), "text": "困难"},
            "resume": {"rect": (540, 300, 200, 60), "text": "继续游戏"},
            "restart": {"rect": (540, 380, 200, 60), "text": "重新开始"},
            "menu": {"rect": (540, 460, 200, 60), "text": "主菜单"},
            "calibrate": {"rect": (400, 500, 300, 60), "text": "立即校准"},
            "skin1": {"rect": (300, 350, 150, 60), "text": "默认"},
            "skin2": {"rect": (500, 350, 150, 60), "text": "霓虹"},
            "skin3": {"rect": (700, 350, 150, 60), "text": "柔和"},
            "save": {"rect": (500, 600, 200, 60), "text": "保存关卡"},
            "add_note": {"rect": (1000, 100, 200, 50), "text": "添加音符"}
        }
        
        # 音符类型按钮
        y_pos = 200
        for note_type in self.note_system.note_types:
            self.buttons[f"note_{note_type}"] = {
                "rect": (1000, y_pos, 200, 40),
                "text": note_type.capitalize()
            }
            y_pos += 50
    
    def generate_dynamic_background(self):
        """生成动态背景"""
        self.background.fill(BACKGROUND)
        for i in range(100):
            x = random.randint(0, 1279)
            y = random.randint(0, 719)
            radius = random.randint(2, 10)
            r = random.randint(50, 150)
            g = random.randint(50, 150)
            b = random.randint(100, 200)
            color = (r, g, b)
            pygame.draw.circle(self.background, color, (x, y), radius)
        
        # 添加游戏名称
        name_surf = self.title_font.render(GAME_NAME, True, PRIMARY)
        self.background.blit(name_surf, (640 - name_surf.get_width()//2, 100))
    
    def start_game(self, song_id=None):
        """开始新游戏"""
        if song_id is None:
            song_id = random.choice([song["id"] for song in self.music_library.songs])
        
        self.current_song_id = song_id
        song = self.music_library.get_song_by_id(song_id)
        
        if song is None:
            print(f"错误: 找不到歌曲 {song_id}")
            return
            
        self.game_state = "playing"
        self.start_time = pygame.time.get_ticks()
        self.current_time = 0
        self.song_position = 0
        self.song_duration = song["duration"] * 1000  # 转换为毫秒
        
        self.game_stats = {
            'score': 0,
            'combo': 0,
            'max_combo': 0,
            'accuracy': 0.0,
            'hits': 0,
            'perfect_hits': 0,
            'good_hits': 0,
            'misses': 0,
            'total_notes': 0,
            'special_hits': 0,
            'games_played': self.game_stats['games_played'],
            'play_time': self.game_stats['play_time'],
            'rank': "F",
            'difficulty': self.difficulty,
            'completed_songs': self.game_stats['completed_songs'],
            'unlocked_achievements': self.game_stats['unlocked_achievements']
        }
        
        # 生成音符
        self.note_system = NoteSystem(self.renderer)
        song_difficulty = song["difficulty"].get(self.difficulty, 1.0)
        self.note_system.generate_song_notes(self.song_duration, song_difficulty)
        self.game_stats['total_notes'] = len(self.note_system.notes)
        
        # 开始回放记录
        self.replay_data = []
        self.recording = True
        
        # 尝试播放音乐
        try:
            pygame.mixer.music.load(song["file"])
            pygame.mixer.music.play()
            print(f"正在播放: {song['title']}")
        except Exception as e:
            print(f"无法播放音乐: {e}")
        
        # 如果启用了校准，运行校准过程
        if self.show_calibration:
            self.calibration.start_calibration()
    
    def handle_input(self, event):
        """处理输入事件"""
        if event.type == MOUSEBUTTONDOWN or event.type == FINGERDOWN:
            # 处理触摸/鼠标点击
            if event.type == MOUSEBUTTONDOWN:
                touch_x, touch_y = event.pos
            else:  # FINGERDOWN
                screen_width, screen_height = self.screen.get_size()
                touch_x = event.x * screen_width
                touch_y = event.y * screen_height
            
            # 处理菜单点击
            if self.game_state == "main_menu":
                self.handle_menu_click(touch_x, touch_y)
            elif self.game_state == "playing":
                # 转换到游戏坐标系
                game_x, game_y = self.renderer.transform_pos(touch_x, touch_y)
                
                # 处理音符判定
                self.check_note_hit(game_x, game_y)
            elif self.game_state == "song_select":
                self.handle_song_select(touch_x, touch_y)
            elif self.game_state == "pause":
                self.handle_pause_click(touch_x, touch_y)
            elif self.game_state == "achievements":
                if self.is_button_clicked("back", touch_x, touch_y):
                    self.game_state = "main_menu"
            elif self.game_state == "settings":
                self.handle_settings_click(touch_x, touch_y)
            elif self.game_state == "editor":
                self.handle_editor_click(touch_x, touch_y)
        
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if self.game_state == "playing":
                    self.game_state = "pause"
                elif self.game_state == "pause":
                    self.game_state = "playing"
                elif self.game_state in ["song_select", "achievements", "settings", "editor"]:
                    self.game_state = "main_menu"
    
    def handle_menu_click(self, x, y):
        """处理主菜单点击"""
        if self.is_button_clicked("play", x, y):
            self.game_state = "song_select"
        elif self.is_button_clicked("achievements", x, y):
            self.game_state = "achievements"
        elif self.is_button_clicked("settings", x, y):
            self.game_state = "settings"
        elif self.is_button_clicked("editor", x, y):
            self.game_state = "editor"
            self.editor_active = True
            self.editor_time = pygame.time.get_ticks()
        elif self.is_button_clicked("exit", x, y):
            self.save_progress()
            pygame.quit()
            sys.exit()
    
    def handle_song_select(self, x, y):
        """处理歌曲选择"""
        # 检查歌曲选择
        for song in self.music_library.get_all_songs():
            btn_id = f"song_{song['id']}"
            if self.is_button_clicked(btn_id, x, y):
                self.start_game(song["id"])
                return
        
        # 检查难度选择
        if self.is_button_clicked("easy", x, y):
            self.difficulty = "简单"
        elif self.is_button_clicked("medium", x, y):
            self.difficulty = "中等"
        elif self.is_button_clicked("hard", x, y):
            self.difficulty = "困难"
        elif self.is_button_clicked("back", x, y):
            self.game_state = "main_menu"
    
    def handle_pause_click(self, x, y):
        """处理暂停菜单点击"""
        if self.is_button_clicked("resume", x, y):
            self.game_state = "playing"
        elif self.is_button_clicked("restart", x, y):
            if self.current_song_id:
                self.start_game(self.current_song_id)
            else:
                self.start_game()
        elif self.is_button_clicked("menu", x, y):
            self.game_state = "main_menu"
    
    def handle_settings_click(self, x, y):
        """处理设置菜单点击"""
        if self.is_button_clicked("back", x, y):
            self.game_state = "main_menu"
        elif self.is_button_clicked("calibrate", x, y):
            self.calibration.start_calibration()
            self.show_calibration = True
        elif self.is_button_clicked("skin1", x, y):
            self.skin = "default"
        elif self.is_button_clicked("skin2", x, y):
            self.skin = "neon"
        elif self.is_button_clicked("skin3", x, y):
            self.skin = "pastel"
    
    def handle_editor_click(self, x, y):
        """处理编辑器点击"""
        if self.is_button_clicked("back", x, y):
            self.game_state = "main_menu"
            self.editor_active = False
        elif self.is_button_clicked("save", x, y):
            self.save_level()
        elif self.is_button_clicked("add_note", x, y):
            lane = random.randint(0, 7)
            self.note_system.add_note(self.selected_note_type, self.editor_time, lane)
        
        # 音符类型选择
        for note_type in self.note_system.note_types:
            if self.is_button_clicked(f"note_{note_type}", x, y):
                self.selected_note_type = note_type
    
    def is_button_clicked(self, button_id, x, y):
        """检查按钮是否被点击"""
        if button_id in self.buttons:
            rect = self.buttons[button_id]["rect"]
            scaled_rect = self.renderer.transform_rect(rect)
            btn_rect = pygame.Rect(scaled_rect)
            return btn_rect.collidepoint(x, y)
        return False
    
    def check_note_hit(self, x, y):
        """检查音符是否被击中"""
        current_time = pygame.time.get_ticks()
        adjusted_time = self.calibration.adjust_time(current_time)
        
        for note in self.note_system.active_notes[:]:
            if note['state'] != 'active':
                continue
                
            # 计算音符位置
            note_x, note_y = self.calculate_note_position(note)
            
            # 计算距离
            distance = math.sqrt((x - note_x)**2 + (y - note_y)**2)
            hit_threshold = self.renderer.transform_size(30)
            
            if distance < hit_threshold:
                # 计算准确度
                time_diff = abs(current_time - note['time'])
                self.calibration.add_sample(current_time, note['time'])
                
                # 评分逻辑
                if time_diff < 50:
                    score = self.note_system.note_types[note['type']]['score'] * 1.2
                    self.game_stats['perfect_hits'] += 1
                    effect = "perfect"
                elif time_diff < 100:
                    score = self.note_system.note_types[note['type']]['score'] * 1.0
                    self.game_stats['good_hits'] += 1
                    effect = "good"
                else:
                    score = self.note_system.note_types[note['type']]['score'] * 0.8
                    effect = "ok"
                
                # 应用连击奖励
                combo_bonus = 1.0 + (min(self.game_stats['combo'], 100) / 100.0)
                score *= combo_bonus
                
                # 更新分数和连击
                self.game_stats['score'] += int(score)
                self.game_stats['combo'] += 1
                self.game_stats['max_combo'] = max(self.game_stats['max_combo'], self.game_stats['combo'])
                self.game_stats['hits'] += 1
                
                # 特殊音符统计
                if note['type'] == 'special':
                    self.game_stats['special_hits'] += 1
                
                note['state'] = 'hit'
                note['hit_time'] = current_time
                note['effect'] = effect
                
                # 从活动音符中移除
                self.note_system.active_notes.remove(note)
                break
    
    def calculate_note_position(self, note):
        """计算音符位置（考虑判定线运动）"""
        base_y = self.judgment_line.y - 200
        progress = min(1.0, max(0.0, note['progress']))
        
        # 音符最终位置
        final_x = self.judgment_line.x + (note['lane'] * 100 - 350)
        final_y = self.judgment_line.y
        
        # 当前位置
        current_y = base_y + (final_y - base_y) * progress
        return final_x, current_y
    
    def trigger_vibration(self, duration):
        """触发震动反馈（安卓设备）"""
        # 在Pydroid 3中禁用震动功能
        pass
    
    def update(self):
        """更新游戏状态"""
        self.current_time = pygame.time.get_ticks()
        
        if self.game_state == "playing":
            # 更新音符系统
            combo_bonus = self.note_system.update(self.current_time)
            
            # 更新游戏统计
            if self.note_system.active_notes:
                self.game_stats['misses'] = self.note_system.missed_notes
                self.game_stats['combo'] = self.note_system.combo
                self.game_stats['max_combo'] = max(self.game_stats['max_combo'], self.note_system.combo)
            
            # 计算准确率
            if self.game_stats['hits'] + self.game_stats['misses'] > 0:
                self.game_stats['accuracy'] = self.game_stats['hits'] / (self.game_stats['hits'] + self.game_stats['misses'])
            
            # 计算评级
            self.calculate_rank()
            
            # 更新判定线位置
            self.judgment_line.update()
            
            # 校准过程
            if self.show_calibration:
                if self.calibration.update_calibration(self.current_time):
                    self.show_calibration = False
            
            # 记录回放数据
            if self.recording:
                self.replay_data.append({
                    'time': self.current_time - self.start_time,
                    'notes': [n.copy() for n in self.note_system.notes if n['state'] in ['active', 'hit']],
                    'line_pos': (self.judgment_line.x, self.judgment_line.y, self.judgment_line.angle),
                    'stats': self.game_stats.copy()
                })
            
            # 检查游戏结束
            if self.current_time - self.start_time > self.song_duration:
                self.game_state = "results"
                self.game_stats['games_played'] += 1
                
                # 检查是否首次完成这首歌
                if self.current_song_id and self.game_stats['completed_songs'] < 12:
                    self.game_stats['completed_songs'] += 1
                
                self.achievements.check_achievements(self.game_stats)
                pygame.mixer.music.stop()
        
        elif self.game_state == "editor":
            self.editor_time = pygame.time.get_ticks()
            self.note_system.update(self.editor_time)
    
    def calculate_rank(self):
        """计算当前评级"""
        accuracy = self.game_stats['accuracy']
        combo_ratio = self.game_stats['max_combo'] / max(1, self.game_stats['total_notes'])
        
        score = accuracy * 0.7 + combo_ratio * 0.3
        
        if score > 0.95:
            self.game_stats['rank'] = "S"
        elif score > 0.9:
            self.game_stats['rank'] = "A"
        elif score > 0.8:
            self.game_stats['rank'] = "B"
        elif score > 0.7:
            self.game_stats['rank'] = "C"
        elif score > 0.6:
            self.game_stats['rank'] = "D"
        else:
            self.game_stats['rank'] = "F"
    
    def save_level(self):
        """保存自定义关卡"""
        level_data = {
            "name": "自定义关卡",
            "difficulty": self.difficulty,
            "notes": [],
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for note in self.note_system.notes:
            level_data["notes"].append({
                "type": note['type'],
                "time": note['time'],
                "lane": note['lane'],
                "duration": note['duration']
            })
        
        # 保存到文件
        try:
            with open("custom_level.json", "w") as f:
                json.dump(level_data, f, indent=2)
        except Exception as e:
            print(f"保存关卡错误: {e}")
    
    def save_progress(self):
        """保存游戏进度"""
        progress_data = {
            "completed_songs": self.game_stats['completed_songs'],
            "unlocked_achievements": len(self.achievements.unlocked),
            "last_played": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "difficulty": self.difficulty,
            "skin": self.skin
        }
        
        try:
            with open("game_progress.json", "w") as f:
                json.dump(progress_data, f, indent=2)
            print("游戏进度已保存")
        except Exception as e:
            print(f"保存进度错误: {e}")
    
    def load_progress(self):
        """加载游戏进度"""
        try:
            if os.path.exists("game_progress.json"):
                with open("game_progress.json", "r") as f:
                    progress_data = json.load(f)
                
                self.game_stats['completed_songs'] = progress_data.get("completed_songs", 0)
                self.difficulty = progress_data.get("difficulty", "中等")
                self.skin = progress_data.get("skin", "default")
                
                # 加载成就解锁状态
                unlocked_count = progress_data.get("unlocked_achievements", 0)
                self.game_stats['unlocked_achievements'] = unlocked_count
                
                print(f"已加载进度: 完成歌曲 {self.game_stats['completed_songs']}/12")
        except Exception as e:
            print(f"加载进度错误: {e}")

    def draw_main_menu(self):
        """绘制主菜单"""
        # 绘制背景
        scaled_bg = pygame.transform.scale(
            self.background, 
            (int(1280 * self.renderer.scale_factor), 
            int(720 * self.renderer.scale_factor)
        )
        self.screen.blit(scaled_bg, (self.renderer.offset_x, self.renderer.offset_y))
        
        # 绘制标题
        title_surf = self.title_font.render(GAME_NAME, True, ACCENT)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 150)
        self.screen.blit(title_surf, title_pos)
        
        # 绘制版本号
        version_surf = self.small_font.render(f"版本: {VERSION}", True, TEXT_COLOR)
        version_pos = self.renderer.transform_pos(50, 680)
        self.screen.blit(version_surf, version_pos)
        
        # 绘制进度
        progress_surf = self.small_font.render(f"完成歌曲: {self.game_stats['completed_songs']}/12", True, HIGHLIGHT)
        progress_pos = self.renderer.transform_pos(640 - progress_surf.get_width()//2, 220)
        self.screen.blit(progress_surf, progress_pos)
        
        # 绘制按钮
        for btn_id, btn_data in self.buttons.items():
            if btn_id in ["play", "achievements", "settings", "editor", "exit"]:
                self.draw_button(btn_id, btn_data["text"])
    
    def draw_song_select(self):
        """绘制歌曲选择界面"""
        self.screen.fill(BACKGROUND)
        
        # 绘制标题
        title_surf = self.large_font.render("选择歌曲", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 50)
        self.screen.blit(title_surf, title_pos)
        
        # 返回按钮
        self.draw_button("back", "返回")
        
        # 难度选择
        diff_title = self.medium_font.render("选择难度:", True, TEXT_COLOR)
        self.screen.blit(diff_title, self.renderer.transform_pos(200, 550))
        
        self.draw_button("easy", "简单", (350, 540, 120, 40))
        self.draw_button("medium", "中等", (500, 540, 120, 40))
        self.draw_button("hard", "困难", (650, 540, 120, 40))
        
        # 显示当前难度
        diff_surf = self.small_font.render(f"当前难度: {self.difficulty}", True, HIGHLIGHT)
        self.screen.blit(diff_surf, self.renderer.transform_pos(500, 600))
        
        # 显示歌曲列表
        y_pos = 120
        for song in self.music_library.get_all_songs():
            # 检查歌曲是否已完成
            is_completed = self.game_stats['completed_songs'] >= int(song['id'][4:])
            song_color = HIGHLIGHT if is_completed else TEXT_COLOR
            
            song_text = f"{song['title']} - {song['artist']}"
            song_surf = self.medium_font.render(song_text, True, song_color)
            self.screen.blit(song_surf, self.renderer.transform_pos(200, y_pos))
            
            # 添加选择按钮
            btn_rect = (900, y_pos-10, 200, 40)
            self.draw_button(f"song_{song['id']}", "选择", btn_rect)
            
            # 显示歌曲时长
            duration_text = f"{song['duration']//60}:{song['duration']%60:02}"
            duration_surf = self.small_font.render(duration_text, True, PRIMARY)
            self.screen.blit(duration_surf, self.renderer.transform_pos(1100, y_pos+5))
            
            # 显示难度
            diff_text = f"难度: {song['difficulty'][self.difficulty]}"
            diff_surf = self.small_font.render(diff_text, True, ACCENT)
            self.screen.blit(diff_surf, self.renderer.transform_pos(200, y_pos+40))
            
            y_pos += 80
    
    def draw_playing(self):
        """绘制游戏画面"""
        # 绘制动态背景
        scaled_bg = pygame.transform.scale(
            self.background, 
            (int(1280 * self.renderer.scale_factor), 
            int(720 * self.renderer.scale_factor)
        )
        self.screen.blit(scaled_bg, (self.renderer.offset_x, self.renderer.offset_y))
        
        # 绘制判定线
        line_start = self.renderer.transform_pos(
            self.judgment_line.x - 500, 
            self.judgment_line.y
        )
        line_end = self.renderer.transform_pos(
            self.judgment_line.x + 500, 
            self.judgment_line.y
        )
        pygame.draw.line(
            self.screen, 
            (255, 255, 255), 
            line_start, 
            line_end, 
            int(self.renderer.transform_size(3))
        )
        
        # 绘制音符
        for note in self.note_system.notes:
            if note['state'] == 'active':
                x, y = self.calculate_note_position(note)
                tx, ty = self.renderer.transform_pos(x, y)
                note_type = note['type']
                note_data = self.note_system.note_types[note_type]
                radius = self.renderer.transform_size(note_data['size'])
                
                # 绘制音符
                pygame.draw.circle(self.screen, note_data['color'], (tx, ty), radius)
                
                # 绘制音符类型指示
                if note_type in ['hold', 'drag']:
                    inner_radius = radius * 0.6
                    pygame.draw.circle(self.screen, (255, 255, 255), (tx, ty), inner_radius, 2)
                if note_type == 'flick':
                    # 绘制箭头
                    arrow_size = radius * 0.8
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                   (tx - arrow_size, ty), 
                                   (tx + arrow_size, ty), 2)
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                   (tx + arrow_size - 10, ty - 10), 
                                   (tx + arrow_size, ty), 2)
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                   (tx + arrow_size - 10, ty + 10), 
                                   (tx + arrow_size, ty), 2)
                if note_type == 'special':
                    # 绘制星形
                    star_points = []
                    for i in range(5):
                        angle = math.pi/2 + i * 2*math.pi/5
                        px = tx + radius * math.cos(angle)
                        py = ty + radius * math.sin(angle)
                        star_points.append((px, py))
                        angle += math.pi/5
                        px = tx + radius * 0.5 * math.cos(angle)
                        py = ty + radius * 0.5 * math.sin(angle)
                        star_points.append((px, py))
                    pygame.draw.polygon(self.screen, (255, 255, 255), star_points, 2)
        
        # 绘制UI
        # 显示歌曲信息
        if self.current_song_id:
            song = self.music_library.get_song_by_id(self.current_song_id)
            if song:
                song_text = f"{song['title']} - {song['artist']}"
                song_surf = self.medium_font.render(song_text, True, TEXT_COLOR)
                self.screen.blit(song_surf, self.renderer.transform_pos(50, 50))
        
        score_text = self.medium_font.render(f"分数: {self.game_stats['score']}", True, TEXT_COLOR)
        combo_text = self.medium_font.render(f"连击: {self.game_stats['combo']}", True, TEXT_COLOR)
        rank_text = self.large_font.render(f"评价: {self.game_stats['rank']}", True, HIGHLIGHT)
        
        self.screen.blit(score_text, self.renderer.transform_pos(50, 100))
        self.screen.blit(combo_text, self.renderer.transform_pos(50, 150))
        self.screen.blit(rank_text, self.renderer.transform_pos(50, 200))
        
        # 进度条
        progress_width = 1000 * self.renderer.scale_factor
        progress_height = 10 * self.renderer.scale_factor
        progress_x = self.renderer.offset_x + (self.screen.get_width() - progress_width) / 2
        progress_y = self.renderer.offset_y + self.renderer.transform_size(650)
        
        # 背景条
        pygame.draw.rect(self.screen, (80, 80, 100), (progress_x, progress_y, progress_width, progress_height))
        
        # 进度填充
        progress = min(1.0, (self.current_time - self.start_time) / self.song_duration)
        fill_width = progress_width * progress
        pygame.draw.rect(self.screen, PRIMARY, (progress_x, progress_y, fill_width, progress_height))
        
        # 校准提示
        if self.show_calibration:
            cal_surf = self.medium_font.render("校准中... 请按节拍点击!", True, HIGHLIGHT)
            cal_pos = self.renderer.transform_pos(640 - cal_surf.get_width()//2, 300)
            self.screen.blit(cal_surf, cal_pos)
            
            # 绘制校准节拍
            if self.calibration.calibration_step < len(self.calibration.calibration_times):
                next_time = self.calibration.calibration_times[self.calibration.calibration_step]
                time_left = max(0, (next_time - self.current_time) / 1000.0)
                
                # 绘制节拍指示器
                indicator_size = 100 * (1.0 - time_left)
                indicator_x, indicator_y = self.renderer.transform_pos(640, 400)
                pygame.draw.circle(self.screen, ACCENT, (indicator_x, indicator_y), indicator_size, 5)
    
    def draw_pause_menu(self):
        """绘制暂停菜单"""
        # 半透明覆盖层
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 标题
        title_surf = self.large_font.render("游戏暂停", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 200)
        self.screen.blit(title_surf, title_pos)
        
        # 按钮
        self.draw_button("resume", "继续游戏")
        self.draw_button("restart", "重新开始")
        self.draw_button("menu", "主菜单")
    
    def draw_results(self):
        """绘制结果画面"""
        self.screen.fill(BACKGROUND)
        
        # 标题
        title_surf = self.large_font.render("游戏结果", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 100)
        self.screen.blit(title_surf, title_pos)
        
        # 显示歌曲信息
        if self.current_song_id:
            song = self.music_library.get_song_by_id(self.current_song_id)
            if song:
                song_text = f"{song['title']} - {song['artist']}"
                song_surf = self.medium_font.render(song_text, True, TEXT_COLOR)
                self.screen.blit(song_surf, self.renderer.transform_pos(640 - song_surf.get_width()//2, 150))
        
        # 结果数据
        y_pos = 200
        results = [
            f"分数: {self.game_stats['score']}",
            f"最大连击: {self.game_stats['max_combo']}/{self.game_stats['total_notes']}",
            f"准确率: {self.game_stats['accuracy']*100:.1f}%",
            f"完美: {self.game_stats['perfect_hits']}",
            f"良好: {self.game_stats['good_hits']}",
            f"失误: {self.game_stats['misses']}",
            f"评价: {self.game_stats['rank']}",
            f"难度: {self.difficulty}"
        ]
        
        for result in results:
            result_surf = self.medium_font.render(result, True, TEXT_COLOR)
            result_pos = self.renderer.transform_pos(640 - result_surf.get_width()//2, y_pos)
            self.screen.blit(result_surf, result_pos)
            y_pos += 40
        
        # 绘制按钮
        self.draw_button("restart", "再玩一次", (440, 550, 200, 60))
        self.draw_button("menu", "主菜单", (640, 550, 200, 60))
        
        # 显示新解锁的成就
        if self.achievements.unlocked:
            y_pos = 500
            unlock_surf = self.medium_font.render("解锁成就:", True, HIGHLIGHT)
            self.screen.blit(unlock_surf, self.renderer.transform_pos(640 - unlock_surf.get_width()//2, y_pos))
            y_pos += 40
            
            for ach_id in self.achievements.unlocked[:3]:  # 最多显示3个
                ach = self.achievements.achievements[ach_id]
                ach_surf = self.medium_font.render(f"{ach['icon']} {ach['name']}", True, HIGHLIGHT)
                self.screen.blit(ach_surf, self.renderer.transform_pos(640 - ach_surf.get_width()//2, y_pos))
                y_pos += 30
                
                desc_surf = self.small_font.render(ach['desc'], True, ACCENT)
                self.screen.blit(desc_surf, self.renderer.transform_pos(640 - desc_surf.get_width()//2, y_pos))
                y_pos += 40
    
    def draw_achievements(self):
        """绘制成就页面"""
        self.screen.fill(BACKGROUND)
        
        # 标题
        title_surf = self.large_font.render("成就系统", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 50)
        self.screen.blit(title_surf, title_pos)
        
        # 返回按钮
        self.draw_button("back", "返回")
        
        # 成就统计
        unlocked = sum(1 for a in self.achievements.achievements.values() if a['achieved'])
        total = len(self.achievements.achievements)
        stats_surf = self.medium_font.render(f"已解锁: {unlocked}/{total}", True, HIGHLIGHT)
        self.screen.blit(stats_surf, self.renderer.transform_pos(640 - stats_surf.get_width()//2, 120))
        
        # 显示成就
        y_pos = 180
        for ach_id, ach in self.achievements.achievements.items():
            color = HIGHLIGHT if ach['achieved'] else (100, 100, 100)
            ach_surf = self.medium_font.render(f"{ach['icon']} {ach['name']}: {ach['desc']}", True, color)
            self.screen.blit(ach_surf, self.renderer.transform_pos(200, y_pos))
            y_pos += 60
    
    def draw_settings(self):
        """绘制设置页面"""
        self.screen.fill(BACKGROUND)
        
        # 标题
        title_surf = self.large_font.render("游戏设置", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 100)
        self.screen.blit(title_surf, title_pos)
        
        # 返回按钮
        self.draw_button("back", "返回")
        
        # 校准按钮
        self.draw_button("calibrate", "立即校准")
        
        # 皮肤选择
        skin_title = self.medium_font.render("选择主题:", True, TEXT_COLOR)
        self.screen.blit(skin_title, self.renderer.transform_pos(200, 300))
        
        self.draw_button("skin1", "默认")
        self.draw_button("skin2", "霓虹")
        self.draw_button("skin3", "柔和")
        
        # 当前设置
        setting_y = 450
        settings = [
            f"难度: {self.difficulty}",
            f"主题: {self.skin}",
            f"震动反馈: {'开启' if self.vibration_enabled else '关闭'}"
        ]
        
        for setting in settings:
            setting_surf = self.medium_font.render(setting, True, TEXT_COLOR)
            self.screen.blit(setting_surf, self.renderer.transform_pos(200, setting_y))
            setting_y += 50
    
    def draw_editor(self):
        """绘制关卡编辑器"""
        self.screen.fill(BACKGROUND)
        
        # 标题
        title_surf = self.large_font.render("关卡编辑器", True, PRIMARY)
        title_pos = self.renderer.transform_pos(640 - title_surf.get_width()//2, 50)
        self.screen.blit(title_surf, title_pos)
        
        # 返回按钮
        self.draw_button("back", "返回")
        
        # 保存按钮
        self.draw_button("save", "保存关卡")
        
        # 添加音符按钮
        self.draw_button("add_note", "添加音符")
        
        # 音符类型选择
        note_title = self.medium_font.render("音符类型:", True, TEXT_COLOR)
        self.screen.blit(note_title, self.renderer.transform_pos(1000, 150))
        
        for note_type in self.note_system.note_types:
            btn_id = f"note_{note_type}"
            self.draw_button(btn_id, note_type.capitalize())
        
        # 当前选择
        selected_surf = self.small_font.render(f"当前选择: {self.selected_note_type}", True, HIGHLIGHT)
        self.screen.blit(selected_surf, self.renderer.transform_pos(1000, 450))
        
        # 绘制游戏视图
        self.draw_playing()
        
        # 编辑器信息
        time_surf = self.small_font.render(f"时间: {self.editor_time/1000:.1f}秒", True, TEXT_COLOR)
        self.screen.blit(time_surf, self.renderer.transform_pos(50, 150))
        
        count_surf = self.small_font.render(f"音符数量: {len(self.note_system.notes)}", True, TEXT_COLOR)
        self.screen.blit(count_surf, self.renderer.transform_pos(50, 180))
    
    def draw_button(self, button_id, text=None, custom_rect=None):
        """绘制按钮"""
        if button_id not in self.buttons and custom_rect is None:
            return
        
        if custom_rect:
            rect = custom_rect
        else:
            rect = self.buttons[button_id]["rect"]
            if not text:
                text = self.buttons[button_id]["text"]
        
        scaled_rect = self.renderer.transform_rect(rect)
        btn_rect = pygame.Rect(scaled_rect)
        
        # 绘制按钮背景
        pygame.draw.rect(self.screen, PRIMARY, btn_rect)
        pygame.draw.rect(self.screen, ACCENT, btn_rect, 3)
        
        # 绘制按钮文本
        if text:
            btn_text = self.medium_font.render(text, True, TEXT_COLOR)
            text_x = btn_rect.x + (btn_rect.width - btn_text.get_width()) // 2
            text_y = btn_rect.y + (btn_rect.height - btn_text.get_height()) // 2
            self.screen.blit(btn_text, (text_x, text_y))
    
    def run(self):
        """运行游戏主循环"""
        # 创建窗口 - 使用固定尺寸以适应Pydroid 3
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption(GAME_NAME)
        
        # 更新渲染器
        self.renderer.update(self.screen)
        
        # 初始绘制
        self.screen.fill(BACKGROUND)
        self.draw_main_menu()
        pygame.display.flip()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.save_progress()
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        if self.game_state == "playing":
                            self.game_state = "pause"
                        elif self.game_state == "pause":
                            self.game_state = "playing"
                        else:
                            self.game_state = "main_menu"
                # 处理鼠标/触摸事件
                self.handle_input(event)
            
            # 更新游戏状态
            self.update()
            
            # 绘制当前屏幕
            self.screen.fill(BACKGROUND)
            
            if self.game_state == "main_menu":
                self.draw_main_menu()
            elif self.game_state == "song_select":
                self.draw_song_select()
            elif self.game_state == "playing":
                self.draw_playing()
            elif self.game_state == "pause":
                self.draw_playing()
                self.draw_pause_menu()
            elif self.game_state == "results":
                self.draw_results()
            elif self.game_state == "achievements":
                self.draw_achievements()
            elif self.game_state == "settings":
                self.draw_settings()
            elif self.game_state == "editor":
                self.draw_editor()
            
            # 更新显示
            pygame.display.flip()
            
            # 控制帧率
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

# 启动游戏
if __name__ == "__main__":
    game = PyTonkGame()
    game.run()