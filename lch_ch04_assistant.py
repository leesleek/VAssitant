# 기본 정보 입력

import streamlit as st

# from audiorecorder import audiorecorder
# from streamlit_audiorecorder import audiorecorder
from audio_recorder_streamlit import audio_recorder

from openai import OpenAI

import os
import base64
import numpy as np

# 기능 구현 함수
def STT(audio, client):
    # Whisper API가 파일 형태로 음성을 입력받으므로 input.mp3로 저장
    filename = "input.mp3"
    # wav_file = open(filename, "wb")
    # wav_file.write(audio.export().read())
    # wav_file.close()

    with open(filename, "wb") as f:
        f.write(audio)

    # 음성 파일 열기
    audio_file = open(filename, "rb")
    # Whisper 모델을 활용하여 텍스트 얻기
    try: 
        # openai의 whisper API를 활용하여 텍스트를 추출합니다.
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file, 
            response_format="text"
        )

        audio_file.close()
        os.remove(filename)  # 파일 삭제
    except Exception as e:
        transcript = f"음성 인식에 실패했습니다. 오류: {e}"
    return transcript

# 텍스트를 음성으로 변환하는 TTS(Text-to-Speech) API
def TTS(reponse, client):
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=reponse,
    ) as response:
        # 음성 파일을 저장합니다.
        filename = "output.mp3"
        response.stream_to_file(filename)

    # 저장한 음성 파일을 자동으로 재생
    with open(filename, "rb") as f: 
        data = f.read()
        b64 = base64.b64encode(data).decode()

        # 스트림릿에서 음성 자동 재생
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True,)   # streamlit 안에서 HTML 문법 구현에 사용되는 st.markdown()을 활용하여 실행

    # 폴더에 남지 않도록 파일 삭제
    os.remove(filename)  # 파일 삭제

# 음성 비서의 답변을 생성하는 ChatGPT API
def ask_gpt(prompt, client):
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )
    return response.choices[0].message.content
    
### 메인 함수 ###
def main():
    # API 키 입력
    client = OpenAI(api_key="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")
                             
    # 화면 상단에 표시될 프로그램 이름
    st.set_page_config(page_title="LCH 음성 비서", layout="wide")

    
    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = None # 프로그램이 재실행될때마다 이전 녹음 파일 정보가 버퍼에 남아있어 실행되는 것을 방지하기 위해 이전 녹음 파일 정보를 저장하는 리스트를 생성합니다.

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughful assistant. Respond to all input in 25 words and answer in Korean"}] 
        # GPT API에 전달할 프롬프트 양식. 이전 질문 및 답변을 누적하여 저장.

    # 기능 구현 공간
    col1, col2 = st.columns(2) # 화면을 두 개의 열로 나누어 사용합니다.

    with col1: # 음성 비서 기능을 구현하는 공간입니다. (왼쪽 공간)
        st.header("AI Assistant 🔊")
        st.image('ai.png', width=200) # AI 비서 이미지 삽입
        st.markdown('---')

        flag_start = False # 음성 비서 시작 여부를 판단하는 플래그 변수입니다.

        audio = audio_recorder("질문", "녹음 중 ...")

        if audio is not None and len(audio) > 0 and st.session_state["check_audio"] is not audio:
            #  st.audio(audio.export().read()) # 녹음된 음성을 재생합니다.
            st.audio(audio) # 녹음된 음성을 재생합니다.
            question = STT(audio, client) # STT 함수를 호출하여 음성을 텍스트로 변환합니다.

            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}] # 사용자의 질문을 메시지에 추가합니다.
            st.session_state["check_audio"] = audio # 녹음된 음성을 세션 상태에 저장합니다.
            flag_start = True # 음성 비서 시작 플래그를 True로 설정합니다.

    with col2:
        st.header('대화기록 🔊')
        if flag_start: # 음성 비서가 시작되면 대화 기록을 표시합니다.         
            response = ask_gpt(st.session_state["messages"], client) # ask_gpt 함수를 호출하여 ChatGPT의 답변을 생성합니다. 
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "assistant", "content": response}] # ChatGPT의 답변을 메시지에 추가합니다.

            for message in st.session_state["messages"]: # # 대화 기록을 표시합니다.                    
                if message["role"] != "system": # 시스템 메시지는 제외합니다.
                    with st.chat_message(message["role"]): ## 사용자의 질문과 ChatGPT의 답변을 표시합니다.
                        st.markdown(message["content"]) ## 사용자의 질문과 ChatGPT의 답변을 마크다운 형식으로 표시합니다.
            
            TTS(response, client)

if __name__ == "__main__":
    main()


        