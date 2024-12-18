import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import openai
import io
import requests
import threading

# OpenAI API 키 설정
openai.api_key = "api키 필요"

# 전역 변수
root = None
story_text_widget = None
image_label = None
choice1_button = None
choice2_button = None

# GPT로 스토리 생성
def generate_story(choice=None):
    messages = [
        {"role": "system", "content": (
            "당신은 비주얼 노벨 게임의 AI입니다. 반드시 아래와 같은 형식으로 응답하세요:\n"
            "스토리: [스토리 내용]\n"
            "선택지 1: [첫 번째 선택지]\n"
            "선택지 2: [두 번째 선택지]\n"
        )}
    ]
    if choice:
        messages.append({"role": "user", "content": f"이전 선택: {choice}"})
    messages.append({"role": "user", "content": "새로운 스토리를 생성해주세요."})
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    content = response['choices'][0]['message']['content']
    
    # GPT 응답 확인 (디버깅용)
    print("GPT 응답:", content)

    # 텍스트 분리
    try:
        story = content.split("스토리:")[1].split("선택지 1:")[0].strip()
        choice1 = content.split("선택지 1:")[1].split("선택지 2:")[0].strip()
        choice2 = content.split("선택지 2:")[1].strip()
    except IndexError:
        # 형식 오류 시 기본값 제공
        story = "기본 스토리: 오류가 발생했습니다. 다시 실행하거나, 선택지를 눌러 주세요."
        choice1 = "기본 선택지 1"
        choice2 = "기본 선택지 2"
    
    return story, choice1, choice2

# GPT로 이미지 설명 생성
def generate_image_description(story):
    prompt = (
        "다음 스토리를 기반으로 이미지를 생성하기 위한 설명을 작성하세요:\n"
        f"{story}\n"
        "이미지 설명은 다음 형식으로 작성하세요:\n"
        "[배경/장소], [캐릭터의 모습과 행동], [분위기와 주요 시각적 요소]\n"
    )
    
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7,
    )
    
    description = response['choices'][0]['message']['content']
    print("이미지 설명 (한국어):", description)  # 디버깅용
    return description.strip()

# GPT로 이미지 설명 번역 (한국어 → 영어)
def translate_to_english(korean_text):
    prompt = (
        f"다음 한국어 문장을 영어로 번역해주세요:\n"
        f"{korean_text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )
    english_translation = response['choices'][0]['message']['content']
    print("번역된 이미지 설명 (영어):", english_translation)  # 디버깅용
    return english_translation.strip()

# DALL·E로 이미지 생성
def generate_image(description):
    response = openai.Image.create(
        prompt=f"{description}, visual novel style, highly detailed, colorful",
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']

    # 이미지 다운로드
    image_response = requests.get(image_url)
    image_bytes = io.BytesIO(image_response.content)
    return Image.open(image_bytes)

# 스토리 및 화면 업데이트
def display_story(choice=None):
    def task():
        try:
            # GPT로 스토리 및 선택지 생성
            story, choice1, choice2 = generate_story(choice)

            # 스토리 업데이트
            story_text_widget.delete("1.0", tk.END)
            story_text_widget.insert(tk.END, story)

            # 이미지 설명 생성 및 번역
            try:
                image_description_korean = generate_image_description(story)
                image_description_english = translate_to_english(image_description_korean)
                img = generate_image(image_description_english)
                img = img.resize((400, 400))
                photo = ImageTk.PhotoImage(img)
                image_label.config(image=photo)
                image_label.image = photo
            except Exception as e:
                messagebox.showerror("오류", f"이미지를 생성할 수 없습니다: {e}")

            # 선택지 업데이트
            choice1_button.config(text=choice1, command=lambda: display_story(choice1))
            choice2_button.config(text=choice2, command=lambda: display_story(choice2))
        except Exception as e:
            # 오류 발생 시 기본 메시지 표시
            story_text_widget.delete("1.0", tk.END)
            story_text_widget.insert(tk.END, "스토리 생성 중 오류가 발생했습니다. 다시 시도해주세요.")
            messagebox.showerror("오류", f"스토리와 이미지를 생성할 수 없습니다: {e}")

    # 백그라운드 스레드 실행
    threading.Thread(target=task).start()

# GUI 초기화
def init_gui():
    global root, story_text_widget, image_label, choice1_button, choice2_button

    root = tk.Tk()
    root.title("선택 게임")
    root.geometry("800x700")

    # 이미지 표시
    image_label = tk.Label(root)
    image_label.pack(pady=10)

    # 스토리 텍스트 박스
    story_text_widget = tk.Text(root, wrap="word", height=10, width=80, bg="white", fg="black")
    story_text_widget.pack(pady=10)

    # 선택지 버튼
    choice1_button = tk.Button(root, text="선택지 1", command=lambda: display_story("선택지 1"))
    choice1_button.pack(side=tk.LEFT, padx=20)

    choice2_button = tk.Button(root, text="선택지 2", command=lambda: display_story("선택지 2"))
    choice2_button.pack(side=tk.RIGHT, padx=20)

    # 게임 시작
    display_story()

    root.mainloop()

# 게임 실행
if __name__ == "__main__":
    init_gui()
