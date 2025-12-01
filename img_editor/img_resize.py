"""
選択したフォルダ内の画像を、縦横比を維持して横幅500pxにリサイズし、保存先フォルダに保存する。
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import os
from pathlib import Path
import threading


class ImageResizeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("画像リサイズアプリ")
        
        # 変数の初期化
        self.source_folder = ""
        self.dest_folder = ""
        self.image_files = []
        self.is_processing = False
        
        # UI構築
        self.create_widgets()
        
    def create_widgets(self):
        # 上部：フォルダ選択エリア
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=10, padx=10)
        
        # 元フォルダ選択（縦に並べる）
        source_frame = tk.Frame(folder_frame)
        source_frame.pack(pady=5, fill=tk.X)
        tk.Label(source_frame, text="元フォルダ:").pack(side=tk.LEFT, padx=5)
        self.source_label = tk.Label(source_frame, text="未選択", bg="white", width=50, anchor="w", relief=tk.SUNKEN)
        self.source_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(source_frame, text="選択", command=self.select_source_folder).pack(side=tk.LEFT, padx=5)
        
        # 保存先フォルダ選択（縦に並べる）
        dest_frame = tk.Frame(folder_frame)
        dest_frame.pack(pady=5, fill=tk.X)
        tk.Label(dest_frame, text="保存先フォルダ:").pack(side=tk.LEFT, padx=5)
        self.dest_label = tk.Label(dest_frame, text="未選択", bg="white", width=50, anchor="w", relief=tk.SUNKEN)
        self.dest_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(dest_frame, text="選択", command=self.select_dest_folder).pack(side=tk.LEFT, padx=5)
        
        # ボタンフレーム（実行ボタンと終了ボタンを横並び）
        button_frame = tk.Frame(folder_frame)
        button_frame.pack(pady=10)
        
        self.execute_button = tk.Button(button_frame, text="実行", command=self.start_resize, bg="lightblue")
        self.execute_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="終了", command=self.root.quit, bg="lightcoral").pack(side=tk.LEFT, padx=5)
        
        # プログレスバーフレーム
        progress_frame = tk.Frame(folder_frame)
        progress_frame.pack(pady=10, fill=tk.X)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.progress_label = tk.Label(progress_frame, text="", width=15, anchor="e")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
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
            
    def start_resize(self):
        if not self.source_folder:
            messagebox.showwarning("警告", "元フォルダを選択してください")
            return
            
        if not self.dest_folder:
            messagebox.showwarning("警告", "保存先フォルダを選択してください")
            return
            
        if self.is_processing:
            messagebox.showwarning("警告", "処理中です。しばらくお待ちください。")
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
            
        # 非同期で処理を開始
        self.is_processing = True
        self.execute_button.config(state=tk.DISABLED)
        self.progress_bar['maximum'] = len(self.image_files)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0/{}".format(len(self.image_files)))
        
        # 別スレッドで処理を実行
        thread = threading.Thread(target=self.resize_images, daemon=True)
        thread.start()
        
    def resize_images(self):
        """画像をリサイズする処理（別スレッドで実行）"""
        total = len(self.image_files)
        completed = 0
        
        try:
            for filename in self.image_files:
                # 画像を読み込み
                image_path = os.path.join(self.source_folder, filename)
                try:
                    img = Image.open(image_path)
                    
                    # 縦横比を維持して横幅500pxにリサイズ
                    original_width, original_height = img.size
                    new_width = 500
                    new_height = int(original_height * (new_width / original_width))
                    
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 保存
                    save_path = os.path.join(self.dest_folder, filename)
                    resized_img.save(save_path, quality=95)
                    
                    completed += 1
                    
                    # プログレスバーを更新（メインスレッドで実行）
                    self.root.after(0, self.update_progress, completed, total)
                    
                except Exception as e:
                    print(f"エラー: {filename} の処理中にエラーが発生しました: {e}")
                    completed += 1
                    self.root.after(0, self.update_progress, completed, total)
                    
            # 処理完了
            self.root.after(0, self.on_complete)
            
        except Exception as e:
            messagebox.showerror("エラー", f"処理中にエラーが発生しました: {e}")
            self.root.after(0, self.on_complete)
            
    def update_progress(self, completed, total):
        """プログレスバーを更新"""
        self.progress_bar['value'] = completed
        self.progress_label.config(text="{}/{}".format(completed, total))
        
    def on_complete(self):
        """処理完了時の処理"""
        self.is_processing = False
        self.execute_button.config(state=tk.NORMAL)
        self.progress_label.config(text="Completed!")
        messagebox.showinfo("完了", "すべての画像のリサイズが完了しました")


def main():
    root = tk.Tk()
    app = ImageResizeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
