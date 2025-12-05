import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path
from PIL import Image, ImageTk
import shutil


class JsonEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON Editor")
        self.root.geometry("1200x800")
        
        # 種別のマッピング
        self.type_mapping = {
            "電力": ("electricity", "electricity.json"),
            "水道": ("water", "water.json"),
            "ガス": ("gas", "gas.json")
        }
        
        self.current_type = None
        self.current_type_english = None
        self.current_json_file = None
        self.json_data = None
        self.current_id = 1
        self.current_data = None
        
        # 画像パスを保持
        self.meter_image_path = None
        self.explanation_image_path = None
        
        # 無限ループ防止用フラグ
        self.is_loading = False
        self.last_shown_id = None  # 最後にメッセージを表示したID
        
        self.setup_ui()
        
    def setup_ui(self):
        # 上部フレーム：ラジオボタンと読み込みボタン
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # ラジオボタン
        self.type_var = tk.StringVar(value="電力")
        type_frame = ttk.Frame(top_frame)
        type_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(type_frame, text="種別:").pack(side=tk.LEFT, padx=5)
        for type_name in ["電力", "水道", "ガス"]:
            ttk.Radiobutton(
                type_frame,
                text=type_name,
                variable=self.type_var,
                value=type_name,
                command=self.on_type_change
            ).pack(side=tk.LEFT, padx=5)
        
        # 読み込みボタン
        ttk.Button(top_frame, text="読み込み", command=self.load_json).pack(side=tk.LEFT, padx=10)
        
        # ID選択フレーム
        id_frame = ttk.Frame(top_frame)
        id_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(id_frame, text="ID:").pack(side=tk.LEFT, padx=5)
        self.id_var = tk.StringVar(value="1")
        id_spinbox = ttk.Spinbox(
            id_frame,
            from_=1,
            to=999,
            textvariable=self.id_var,
            width=5,
            command=self.on_id_change
        )
        id_spinbox.pack(side=tk.LEFT, padx=5)
        id_spinbox.bind("<Return>", lambda e: self.on_id_change())
        
        # データ追加ボタン
        ttk.Button(top_frame, text="データ追加", command=self.add_new_data).pack(side=tk.LEFT, padx=10)
        
        # 保存ボタン
        ttk.Button(top_frame, text="保存", command=self.save_data).pack(side=tk.LEFT, padx=10)
        
        # メインフレーム：左右に分割
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左フレーム：画像表示（幅を固定）
        self.left_frame = ttk.Frame(main_frame, width=520)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.left_frame.pack_propagate(False)  # 幅を固定
        
        # meterImage
        self.meter_frame = ttk.LabelFrame(self.left_frame, text="メーター画像", padding="10")
        self.meter_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.meter_image_label = ttk.Label(self.meter_frame, text="画像が表示されます")
        self.meter_image_label.pack(expand=True)
        
        ttk.Button(self.meter_frame, text="画像を選択", command=self.select_meter_image).pack(pady=5)
        
        # explanationImage
        self.explanation_frame = ttk.LabelFrame(self.left_frame, text="解説画像", padding="10")
        self.explanation_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.explanation_image_label = ttk.Label(self.explanation_frame, text="画像が表示されます")
        self.explanation_image_label.pack(expand=True)
        
        ttk.Button(self.explanation_frame, text="画像を選択", command=self.select_explanation_image).pack(pady=5)
        
        # 右フレーム：テキストボックス
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(right_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # テキストボックス用の変数とウィジェットを保持
        self.text_vars = {}
        self.text_entries = {}
        
        # フィールド名のリスト（multiplierからexplanationTextまで）
        self.field_names = [
            "multiplier", "pulseUnit", "pulseUnitDisplay", "integerDigits",
            "decimalDigits", "displayUnit", "serialNumber", "inspectionYear",
            "inspectionMonth", "displayValue", "explanationText"
        ]
        
        # 各フィールドのラベルとテキストボックスを作成
        for field_name in self.field_names:
            if field_name == "explanationText":
                # explanationTextは複数行テキストボックス（画面下まで拡張）
                frame = ttk.Frame(scrollable_frame, padding="5")
                frame.pack(fill=tk.BOTH, expand=True, pady=2)
                
                label_text = self.get_field_label(field_name)
                ttk.Label(frame, text=label_text + ":", width=20).pack(side=tk.TOP, anchor=tk.W)
                
                text_frame = ttk.Frame(frame)
                text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
                
                text_widget = tk.Text(text_frame, wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True)
                self.text_entries[field_name] = text_widget
            else:
                frame = ttk.Frame(scrollable_frame, padding="5")
                frame.pack(fill=tk.X, pady=2)
                
                label_text = self.get_field_label(field_name)
                ttk.Label(frame, text=label_text + ":", width=20).pack(side=tk.LEFT)
                
                var = tk.StringVar()
                entry = ttk.Entry(frame, textvariable=var, width=30)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.text_vars[field_name] = var
                self.text_entries[field_name] = entry
        
    def get_field_label(self, field_name):
        """フィールド名を日本語ラベルに変換"""
        labels = {
            "multiplier": "倍率",
            "pulseUnit": "パルス単位",
            "pulseUnitDisplay": "パルス単位表示",
            "integerDigits": "整数桁",
            "decimalDigits": "小数桁",
            "displayUnit": "表示単位",
            "serialNumber": "シリアル番号",
            "inspectionYear": "検定年",
            "inspectionMonth": "検定月",
            "displayValue": "表示値",
            "explanationText": "解説文"
        }
        return labels.get(field_name, field_name)
    
    def on_type_change(self):
        """種別が変更されたときの処理"""
        self.current_type = self.type_var.get()
        self.current_type_english, json_filename = self.type_mapping[self.current_type]
        self.current_json_file = os.path.join("json", json_filename)
        self.current_id = 1
        self.id_var.set("1")
        self.clear_display()
    
    def on_id_change(self):
        """IDが変更されたときの処理"""
        # 無限ループ防止：ロード中は何もしない
        if self.is_loading:
            return
        
        try:
            new_id = int(self.id_var.get())
            if 1 <= new_id <= 999:
                self.current_id = new_id
                self.load_data_by_id()
            else:
                messagebox.showerror("エラー", "IDは1～999の範囲で指定してください")
                self.id_var.set(str(self.current_id))
        except ValueError:
            messagebox.showerror("エラー", "IDは数値で入力してください")
            self.id_var.set(str(self.current_id))
    
    def load_json(self):
        """JSONファイルを読み込む"""
        if not self.current_type:
            self.current_type = self.type_var.get()
            self.on_type_change()
        
        json_path = os.path.join(os.path.dirname(__file__), self.current_json_file)
        
        if not os.path.exists(json_path):
            messagebox.showerror("エラー", f"JSONファイルが見つかりません: {json_path}")
            return
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)
            self.load_data_by_id()
        except Exception as e:
            messagebox.showerror("エラー", f"JSONファイルの読み込みに失敗しました: {str(e)}")
    
    def load_data_by_id(self):
        """指定されたIDのデータを読み込んで表示"""
        # 無限ループ防止
        if self.is_loading:
            return
        self.is_loading = True
        
        try:
            if not self.json_data:
                # メッセージ表示を遅延実行して、イベントループが完了してから表示
                self.root.after(100, lambda: messagebox.showinfo("情報", "JSONファイルを読み込んでください"))
                return
            
            # 指定IDのデータを検索
            self.current_data = None
            for question in self.json_data.get("questions", []):
                if question.get("id") == self.current_id:
                    self.current_data = question
                    break
            
            if not self.current_data:
                # 同じIDに対しては一度だけメッセージを表示
                if self.last_shown_id != self.current_id:
                    self.last_shown_id = self.current_id
                    # メッセージ表示を遅延実行して、イベントループが完了してから表示
                    self.root.after(100, lambda: messagebox.showinfo("情報", "データがありません"))
                self.clear_display()
                return
            
            # データが見つかった場合は、last_shown_idをリセット
            self.last_shown_id = None
            
            # 画像を表示
            self.display_images()
            
            # テキストフィールドを更新
            self.update_text_fields()
        finally:
            self.is_loading = False
    
    def add_new_data(self):
        """新規データを追加"""
        if not self.json_data:
            messagebox.showwarning("警告", "JSONファイルを読み込んでください")
            return
        
        # 既に存在するIDかチェック
        for question in self.json_data.get("questions", []):
            if question.get("id") == self.current_id:
                messagebox.showinfo("情報", f"ID {self.current_id} のデータは既に存在します。")
                self.load_data_by_id()
                return
        
        # 新規データを作成
        self.create_new_data()
        messagebox.showinfo("情報", "情報を入力して保存してください。")
        
        # 画像を表示
        self.display_images()
        
        # テキストフィールドを更新
        self.update_text_fields()
    
    def create_new_data(self):
        """新規データを作成"""
        id_str = f"{self.current_id:03d}"
        
        # デフォルト値を設定
        self.current_data = {
            "id": self.current_id,
            "meterImage": f"img/{self.current_type_english}/{self.current_type_english}_{id_str}.jpg",
            "multiplier": "1",
            "pulseUnit": "1",
            "pulseUnitDisplay": "kWh/Pulse" if self.current_type_english == "electricity" else "m3/Pulse",
            "integerDigits": "5",
            "decimalDigits": "1",
            "displayUnit": "kWh" if self.current_type_english == "electricity" else "m3",
            "serialNumber": "",
            "inspectionYear": "2025",
            "inspectionMonth": "1",
            "displayValue": "",
            "explanationImage": f"img/{self.current_type_english}/{self.current_type_english}_{id_str}_answer.jpg",
            "explanationText": []
        }
    
    def display_images(self):
        """画像を表示"""
        if not self.current_data:
            return
        
        # 利用可能な高さを計算
        self.root.update_idletasks()  # レイアウトを更新
        left_frame_height = self.left_frame.winfo_height()
        
        # パディングとボタンの高さを考慮
        # 各フレームのパディング: 10px (上下) = 20px
        # ボタンの高さ: 約30px
        # フレーム間のマージン: 5px (上下) = 10px
        # タイトルバーの高さ: 約20px
        available_height = left_frame_height - 20 - 30 - 20 - 30 - 10 - 20  # 約130pxを引く
        
        # 2つの画像で分割（各50%）
        max_height_per_image = max(available_height // 2, 100)  # 最低100px
        
        # meterImage
        meter_image_path = self.current_data.get("meterImage", "")
        if meter_image_path:
            full_path = os.path.join(os.path.dirname(__file__), meter_image_path)
            if os.path.exists(full_path):
                self.load_and_display_image(full_path, self.meter_image_label, max_height_per_image)
            else:
                self.meter_image_label.config(image="", text="画像が見つかりません")
        else:
            self.meter_image_label.config(image="", text="画像が設定されていません")
        
        # explanationImage
        explanation_image_path = self.current_data.get("explanationImage", "")
        if explanation_image_path:
            full_path = os.path.join(os.path.dirname(__file__), explanation_image_path)
            if os.path.exists(full_path):
                self.load_and_display_image(full_path, self.explanation_image_label, max_height_per_image)
            else:
                self.explanation_image_label.config(image="", text="画像が見つかりません")
        else:
            self.explanation_image_label.config(image="", text="画像が設定されていません")
    
    def load_and_display_image(self, image_path, label, max_height=None):
        """画像を読み込んで表示（縦横比を維持）"""
        try:
            img = Image.open(image_path)
            original_width = img.width
            original_height = img.height
            
            # 最大サイズを設定
            max_width = 500
            
            # 高さの制限がある場合
            if max_height:
                # 幅と高さの両方の制限を考慮
                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                
                # 小さい方の比率を使用（縦横比を維持）
                ratio = min(width_ratio, height_ratio, 1.0)  # 1.0以上には拡大しない
            else:
                # 高さの制限がない場合は幅のみ考慮
                ratio = min(max_width / original_width, 1.0)
            
            # リサイズ
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            if new_width != original_width or new_height != original_height:
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo, text="")
            label.image = photo  # 参照を保持
        except Exception as e:
            label.config(image="", text=f"画像読み込みエラー: {str(e)}")
    
    def update_text_fields(self):
        """テキストフィールドを更新"""
        if not self.current_data:
            return
        
        for field_name in self.field_names:
            if field_name == "explanationText":
                # explanationTextは配列なので、改行で結合して表示
                text_array = self.current_data.get(field_name, [])
                if isinstance(text_array, list):
                    text_content = "\n".join(text_array)
                else:
                    text_content = str(text_array)
                self.text_entries[field_name].delete("1.0", tk.END)
                self.text_entries[field_name].insert("1.0", text_content)
            else:
                value = self.current_data.get(field_name, "")
                self.text_vars[field_name].set(str(value))
    
    def clear_display(self):
        """表示をクリア"""
        # 画像をクリア
        self.meter_image_label.config(image="", text="画像が表示されます")
        self.explanation_image_label.config(image="", text="画像が表示されます")
        
        # テキストフィールドをクリア
        for field_name in self.field_names:
            if field_name == "explanationText":
                self.text_entries[field_name].delete("1.0", tk.END)
            else:
                self.text_vars[field_name].set("")
    
    
    def select_meter_image(self):
        """meterImageの画像を選択"""
        if not self.current_data:
            messagebox.showwarning("警告", "データを読み込んでください")
            return
        
        file_path = filedialog.askopenfilename(
            title="メーター画像を選択",
            filetypes=[("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if file_path:
            self.copy_and_update_image(file_path, "meterImage")
    
    def select_explanation_image(self):
        """explanationImageの画像を選択"""
        if not self.current_data:
            messagebox.showwarning("警告", "データを読み込んでください")
            return
        
        file_path = filedialog.askopenfilename(
            title="解説画像を選択",
            filetypes=[("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if file_path:
            self.copy_and_update_image(file_path, "explanationImage")
    
    def copy_and_update_image(self, source_path, image_type):
        """画像をコピーして更新"""
        # 保存先パスを生成
        id_str = f"{self.current_id:03d}"
        base_dir = os.path.dirname(__file__)
        img_dir = os.path.join(base_dir, "img", self.current_type_english)
        os.makedirs(img_dir, exist_ok=True)
        
        if image_type == "meterImage":
            dest_filename = f"{self.current_type_english}_{id_str}.jpg"
        else:  # explanationImage
            dest_filename = f"{self.current_type_english}_{id_str}_answer.jpg"
        
        dest_path = os.path.join(img_dir, dest_filename)
        
        try:
            # 画像をコピー
            shutil.copy2(source_path, dest_path)
            
            # JSON内のパスを更新
            json_path = f"img/{self.current_type_english}/{dest_filename}"
            self.current_data[image_type] = json_path
            
            # 画像を再表示
            self.display_images()
            
            messagebox.showinfo("成功", f"画像を更新しました: {dest_filename}")
        except Exception as e:
            messagebox.showerror("エラー", f"画像のコピーに失敗しました: {str(e)}")
    
    def save_data(self):
        """データを保存"""
        if not self.json_data or not self.current_data:
            messagebox.showwarning("警告", "保存するデータがありません")
            return
        
        try:
            # テキストフィールドから値を取得して更新
            for field_name in self.field_names:
                if field_name == "explanationText":
                    # 改行区切りのテキストを配列に変換
                    text_content = self.text_entries[field_name].get("1.0", tk.END).strip()
                    if text_content:
                        # 改行で分割して配列に
                        text_array = [line for line in text_content.split("\n") if line.strip()]
                        self.current_data[field_name] = text_array
                    else:
                        self.current_data[field_name] = []
                else:
                    value = self.text_vars[field_name].get()
                    self.current_data[field_name] = value
            
            # IDが既存かどうかを確認
            questions = self.json_data.get("questions", [])
            existing_index = None
            for i, question in enumerate(questions):
                if question.get("id") == self.current_id:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # 既存データを更新
                questions[existing_index] = self.current_data
            else:
                # 新規データを追加
                questions.append(self.current_data)
                # IDでソート
                questions.sort(key=lambda x: x.get("id", 0))
            
            # JSONファイルに保存
            json_path = os.path.join(os.path.dirname(__file__), self.current_json_file)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "データを保存しました")
        except Exception as e:
            messagebox.showerror("エラー", f"データの保存に失敗しました: {str(e)}")


def main():
    root = tk.Tk()
    app = JsonEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
