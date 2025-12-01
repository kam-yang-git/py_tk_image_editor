"""
フォルダ内の画像を読み込み、矩形や線を描画して保存する。
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import os
from pathlib import Path


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("画像エディタ")
        
        # 変数の初期化
        self.source_folder = ""
        self.dest_folder = ""
        self.image_files = []
        self.current_image_index = -1
        self.current_image = None
        self.display_image = None
        self.original_image = None
        
        # 描画用の変数
        self.rectangles = []  # [(x1, y1, x2, y2, color), ...]
        self.lines = []  # [(x1, y1, x2, y2), ...]
        self.click_points = []  # クリック座標のリスト
        self.drag_start = None
        self.drag_end = None
        self.is_dragging = False
        self.drag_color = "red"
        
        # UI構築
        self.create_widgets()
        
        # キーバインド
        self.root.bind('<Return>', self.close_polygon)
        
    def create_widgets(self):
        # 上部：フォルダ選択エリア
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=10)
        
        # 元フォルダ選択
        source_frame = tk.Frame(folder_frame)
        source_frame.pack(pady=5)
        tk.Label(source_frame, text="元フォルダ:").pack(side=tk.LEFT, padx=5)
        self.source_label = tk.Label(source_frame, text="未選択", bg="white", width=50, anchor="w", relief=tk.SUNKEN)
        self.source_label.pack(side=tk.LEFT, padx=5)
        tk.Button(source_frame, text="選択", command=self.select_source_folder).pack(side=tk.LEFT, padx=5)
        
        # 保存先フォルダ選択
        dest_frame = tk.Frame(folder_frame)
        dest_frame.pack(pady=5)
        tk.Label(dest_frame, text="保存先:").pack(side=tk.LEFT, padx=5)
        self.dest_label = tk.Label(dest_frame, text="未選択", bg="white", width=50, anchor="w", relief=tk.SUNKEN)
        self.dest_label.pack(side=tk.LEFT, padx=5)
        tk.Button(dest_frame, text="選択", command=self.select_dest_folder).pack(side=tk.LEFT, padx=5)
        
        # 実行ボタン
        tk.Button(folder_frame, text="実行", command=self.load_images, bg="lightblue").pack(pady=10)
        
        # 中央：画像表示エリア
        self.canvas = tk.Canvas(self.root, bg="gray", width=500, height=500)
        self.canvas.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # 下部：ボタンエリア
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="前へ", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="次へ", command=self.next_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="リセット", command=self.reset_drawings, bg="lightyellow").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="保存", command=self.save_image, bg="lightgreen").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="終了", command=self.root.quit, bg="lightcoral").pack(side=tk.LEFT, padx=5)
        
    def select_source_folder(self):
        folder = filedialog.askdirectory(title="元フォルダを選択")
        if folder:
            self.source_folder = folder
            self.source_label.config(text=folder)
            
    def select_dest_folder(self):
        folder = filedialog.askdirectory(title="保存先フォルダを選択")
        if folder:
            self.dest_folder = folder
            self.dest_label.config(text=folder)
            
    def load_images(self):
        if not self.source_folder:
            messagebox.showwarning("警告", "元フォルダを選択してください")
            return
            
        # 画像ファイルを取得
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        self.image_files = [
            f for f in os.listdir(self.source_folder)
            if Path(f).suffix.lower() in image_extensions
        ]
        self.image_files.sort()
        
        if not self.image_files:
            messagebox.showinfo("情報", "画像ファイルが見つかりませんでした")
            return
            
        self.current_image_index = 0
        self.display_current_image()
        
    def display_current_image(self):
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_files):
            return
            
        # 画像を読み込み（リサイズ処理なし）
        image_path = os.path.join(self.source_folder, self.image_files[self.current_image_index])
        self.original_image = Image.open(image_path)
        
        # 表示用の画像を作成（描画用のコピー、元のサイズのまま）
        self.display_image = self.original_image.copy()
        
        # キャンバスのサイズを画像サイズに合わせる
        img_width, img_height = self.display_image.size
        self.canvas.config(width=img_width, height=img_height)
        
        # 描画をクリア
        self.rectangles = []
        self.lines = []
        self.click_points = []
        self.drag_start = None
        self.drag_end = None
        
        self.update_canvas()
        
    def update_canvas(self):
        if self.display_image is None:
            return
            
        # キャンバスをクリア
        self.canvas.delete("all")
        
        # 画像を表示
        self.photo = ImageTk.PhotoImage(self.display_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # 既存の描画を再描画
        self.redraw_all()
        
    def redraw_all(self):
        # 矩形を描画
        for rect in self.rectangles:
            x1, y1, x2, y2, color = rect
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            
        # 線を描画
        for line in self.lines:
            x1, y1, x2, y2 = line
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)
            
        # ドラッグ中の矩形を描画
        if self.is_dragging and self.drag_start and self.drag_end:
            self.canvas.create_rectangle(
                self.drag_start[0], self.drag_start[1],
                self.drag_end[0], self.drag_end[1],
                outline=self.drag_color, width=2
            )
            
    def on_canvas_click(self, event):
        # Shiftキーが押されているかチェック
        if event.state & 0x1:  # Shiftキー
            # Shift+クリック：ドラッグ開始（蛍光緑枠）
            self.drag_start = (event.x, event.y)
            self.drag_end = (event.x, event.y)
            self.is_dragging = True
            self.drag_color = "lime"  # 蛍光緑
        else:
            # 通常のクリック：線の描画用
            # ドラッグ開始位置を設定（ドラッグ判定用）
            self.drag_start = (event.x, event.y)
            self.drag_end = (event.x, event.y)
            self.is_dragging = False
            
    def on_canvas_drag(self, event):
        # Shiftキーが押されている場合
        if event.state & 0x1:  # Shiftキー
            if self.drag_start:
                self.drag_end = (event.x, event.y)
                self.is_dragging = True
                self.drag_color = "lime"  # 蛍光緑
        # 通常のドラッグ（Shiftなし）
        else:
            if self.drag_start:
                self.drag_end = (event.x, event.y)
                self.is_dragging = True
                self.drag_color = "red"
            
        self.update_canvas()
        
    def on_canvas_release(self, event):
        if self.drag_start and self.drag_end:
            # ドラッグだった場合（開始位置と終了位置が異なる）
            if self.is_dragging:
                # 矩形を確定
                x1, y1 = self.drag_start
                x2, y2 = self.drag_end
                # 座標を正規化（左上と右下を確定）
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                self.rectangles.append((x1, y1, x2, y2, self.drag_color))
            else:
                # クリックのみの場合：線の描画用
                if len(self.click_points) > 0:
                    # 前回の座標から今回の座標まで線を引く
                    prev_x, prev_y = self.click_points[-1]
                    self.lines.append((prev_x, prev_y, event.x, event.y))
                self.click_points.append((event.x, event.y))
            
        self.drag_start = None
        self.drag_end = None
        self.is_dragging = False
        self.update_canvas()
        
    def close_polygon(self, event=None):
        if len(self.click_points) >= 2:
            # 最後の点と最初の点を結ぶ
            last_x, last_y = self.click_points[-1]
            first_x, first_y = self.click_points[0]
            self.lines.append((last_x, last_y, first_x, first_y))
            # Enterキーを押した後は、次のクリックから新しい描画を開始するため、座標をクリア
            self.click_points = []
            self.update_canvas()
            
    def reset_drawings(self):
        # すべての描画をクリア
        self.rectangles = []
        self.lines = []
        self.click_points = []
        self.drag_start = None
        self.drag_end = None
        self.is_dragging = False
        self.update_canvas()
            
    def save_image(self):
        if self.display_image is None:
            messagebox.showwarning("警告", "画像が読み込まれていません")
            return
            
        if not self.dest_folder:
            messagebox.showwarning("警告", "保存先フォルダを選択してください")
            return
            
        # 元の画像サイズの画像に描画を反映
        save_image = self.display_image.copy()
        draw = ImageDraw.Draw(save_image)
        
        # 矩形を描画
        for rect in self.rectangles:
            x1, y1, x2, y2, color = rect
            # 色をRGBに変換
            if color == "red":
                rgb_color = (255, 0, 0)
            elif color == "lime":
                rgb_color = (0, 255, 0)
            else:
                rgb_color = (255, 0, 0)
                
            draw.rectangle([x1, y1, x2, y2], outline=rgb_color, width=2)
            
        # 線を描画
        for line in self.lines:
            x1, y1, x2, y2 = line
            draw.line([x1, y1, x2, y2], fill=(255, 0, 0), width=2)
            
        # 保存
        original_filename = self.image_files[self.current_image_index]
        base_name = Path(original_filename).stem
        save_path = os.path.join(self.dest_folder, f"{base_name}_answer.jpg")
        save_image.save(save_path, "JPEG")
        messagebox.showinfo("保存完了", f"画像を保存しました:\n{save_path}")
        
    def next_image(self):
        if len(self.image_files) == 0:
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
        self.display_current_image()
        
    def prev_image(self):
        if len(self.image_files) == 0:
            return
        self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
        self.display_current_image()


def main():
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
