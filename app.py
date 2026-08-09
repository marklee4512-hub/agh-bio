import os
import re
import random
import asyncio
import base64
import tempfile
import json
from datetime import datetime
import pytz
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import google.generativeai as genai
import edge_tts

# 1. 태블릿/PC 화면 최적화 및 브랜딩
st.set_page_config(page_title="AGH GREENHEALTH BIO", page_icon="🍀", layout="wide")

# --- 2. 이미지 Base64 인코더 ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

# 🤖 로봇 이미지 (사장님이 만드신 완벽한 투명 누끼 bio.png 적용)
robot_b64 = get_base64_of_bin_file("bio.png")
robot_img_src = f"data:image/png;base64,{robot_b64}" if robot_b64 else "https://cdn-icons-png.flaticon.com/512/4712/4712139.png"

# 💬 카카오톡 로고
kakao_b64 = get_base64_of_bin_file("카카오톡.png")
kakao_img_src = f"data:image/png;base64,{kakao_b64}" if kakao_b64 else ""

logo_b64 = get_base64_of_bin_file("logo.png")
logo_img_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
qr_b64 = get_base64_of_bin_file("image_1c2eaf.jpg")
qr_img_src = f"data:image/jpeg;base64,{qr_b64}" if qr_b64 else ""

# --- 3. 🎨 프리미엄 CSS ---
st.markdown(f"""
<style>
    h1, h2, h3 {{ color: #005A32 !important; font-weight: 800; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: #005A32 !important; color: white !important;
        border-radius: 8px 8px 0px 0px; font-weight: bold;
    }}
    [data-testid="stSidebar"] {{ background-color: #F4F9F4; }}
    
    /* 📝 사이드바 버튼 글씨 굵기를 600(살짝 얇고 세련되게) 조절 */
    [data-testid="stSidebar"] .stButton p {{
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #111 !important;
    }}

    /* 메인 화면 카탈로그 제품명 폰트 굵게 */
    .product-name {{ font-weight: 800 !important; font-size: 1.15rem !important; color: #333; margin-bottom: 8px; display: block; }}

    /* 🚀 플로팅 컨테이너 */
    .floating-container {{
        position: fixed; bottom: 30px; right: 30px; z-index: 9999;
        display: flex; align-items: flex-end; gap: 10px;
    }}
    .floating-bubble {{
        background: rgba(255, 255, 255, 0.95); border: 2.5px solid #005A32; border-radius: 18px 18px 0 18px;
        padding: 15px 20px; width: 270px; height: 100px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        position: relative; margin-bottom: 15px;
    }}
    .floating-bubble::after {{
        content: ''; position: absolute; bottom: 0; right: -12px;
        border-width: 14px 0 0 14px; border-style: solid;
        border-color: transparent transparent transparent rgba(255, 255, 255, 0.95);
    }}
    .roll-msg {{
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 90%; text-align: center; font-size: 0.9rem; font-weight: 700; color: #005A32;
        opacity: 0; animation: fadeCycle 32s infinite; line-height: 1.4;
    }}
    .msg1 {{ animation-delay: 0s; }} .msg2 {{ animation-delay: 8s; }}
    .msg3 {{ animation-delay: 16s; }} .msg4 {{ animation-delay: 24s; }}
    @keyframes fadeCycle {{ 0%, 20% {{ opacity: 1; }} 23%, 100% {{ opacity: 0; }} }}
    
    /* 🤖 로봇 이미지 (누끼 이미지 완벽 대응, mix-blend-mode 삭제) */
    .floating-robot {{
        width: 140px; 
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        filter: drop-shadow(0 10px 15px rgba(0,0,0,0.25));
        animation: float 3s ease-in-out infinite;
    }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
</style>
""", unsafe_allow_html=True)

# 🚀 무인 대기화면(스크린세이버) 3분 미동작 시 작동
components.html("""
<div id="screensaver" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,90,50,0.98); z-index:999999; flex-direction:column; justify-content:center; align-items:center; cursor:pointer;">
    <h1 style="color:white; font-size:5rem; font-weight:900; margin-bottom:20px; text-align:center;">AGH GREENHEALTH BIO</h1>
    <h2 style="color:#A5D6A7; font-size:2.5rem; text-align:center; animation: blink 2s infinite;">👆 화면을 터치해서 AI 맞춤 상담을 시작하세요</h2>
</div>
<style>@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }</style>
<script>
    let timeout;
    function resetTimer() {
        document.getElementById('screensaver').style.display = 'none';
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            document.getElementById('screensaver').style.display = 'flex';
        }, 180000);
    }
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;
    document.ontouchstart = resetTimer;
    document.onclick = resetTimer;
    resetTimer();
</script>
""", height=0)

# 플로팅 로봇 UI 주입
st.markdown(f"""
<div class="floating-container">
    <div class="floating-bubble">
        <div class="roll-msg msg1">원하시는 제품을 찾기 힘드신가요?<br>카운터에 계신 사장님을 편하게 불러주세요! 🙋‍♂️</div>
        <div class="roll-msg msg2">단일 매장 $300 이상 구매 시<br>공항 텍스 리펀(9%) 혜택을 놓치지 마세요! ✈️</div>
        <div class="roll-msg msg3">좌측 사이드바의 카테고리 버튼을 눌러<br>품목별 제품들을 구경해 보세요 👆</div>
        <div class="roll-msg msg4">눈 건강, 관절, 피로 회복 등<br>증상에 딱 맞는 제품을 추천해 드립니다! 🍀</div>
    </div>
    <img class="floating-robot" src="{robot_img_src}">
</div>
""", unsafe_allow_html=True)

# 4. API 설정
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# --- 5. 상태 관리 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "selected_category" not in st.session_state: st.session_state.selected_category = None
if "chat_query" not in st.session_state: st.session_state.chat_query = None
if "chat_img" not in st.session_state: st.session_state.chat_img = None

# 사장님 추천 랜덤 로테이션을 위한 세션(초기화될 때만 바뀜)
if "current_md_picks" not in st.session_state:
    md_picks_pool = ["마누카꿀 MGO 850+", "초록입홍합 21000", "리트리플 폴리코사놀", "리버케어 간영양제", "프리미엄 빌베리 안구건조", "유칼립투스 프로폴리스"]
    st.session_state.current_md_picks = random.sample(md_picks_pool, 2)

def set_category(cat_name): st.session_state.selected_category = cat_name

def trigger_ai_consultation(query, img_path=None):
    st.session_state.chat_query = query
    st.session_state.chat_img = img_path
    st.session_state.selected_category = None

# --- 6. JSON 데이터 로더 ---
@st.cache_data
def load_product_data():
    file_path = 'products.json'
    categories = {}
    flat_products = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for cat_name, items in data.items():
                        cat_list = []
                        if isinstance(items, list):
                            for item in items:
                                link = item.get("link", "")
                                extracted_id = "default"
                                if link:
                                    match_srl = re.search(r'document_srl=(\d+)', link)
                                    match_slash = re.search(r'/(\d+)/?$', link)
                                    if match_srl:
                                        extracted_id = match_srl.group(1)
                                    elif match_slash:
                                        extracted_id = match_slash.group(1)
                                item["image_file"] = f"{extracted_id}.jpg"
                                cat_list.append(item)
                                flat_products.append(item)
                        categories[cat_name] = cat_list
        except Exception: pass
    return categories, flat_products

categories_db, products_db = load_product_data()

# 🎯 카테고리 아이콘
CATEGORY_EMOJIS = {
    "뼈_관절_연골": "🦴 뼈·관절", "눈_시력": "👁️ 눈 건강", "면역력_에너지": "⚡ 면역·피로",
    "심혈관_콜레스테롤_간": "❤️ 심혈관·간", "여성건강_노화방지": "👩 여성·노화방지", "기관지_구강": "🗣️ 기관지·구강",
    "두뇌_혈행": "🧠 두뇌·수면", "유산균_비타민_어린이_성인_남성": "💊 장·종합비타민", "위건강_마누카꿀": "🍯 마누카꿀·위",
    "뷰티": "✨ 뷰티·선물", "반려동물_건강": "🐶 반려동물", "기타_라이프스타일": "🛏️ 라이프스타일"
}

# 🌐 고급스러운 카드 형태의 택배/TRS 안내 다국어 UI 딕셔너리
UI_TEXT = {
    "KR": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "안녕하세요! AGH 그린건강 매장의 스마트 도우미 **바이오**입니다. 건강 상태에 딱 맞는 제품을 찾아드릴게요! 💚",
        "tab1": "💬 AI 맞춤 상담", "tab2": "📦 한국 택배 & 환급 규정", "tab3": "📱 매장 소식 (Reels)",
        "elderly_mode": "👵 어르신 왕눈이 모드",
        "ai_lang_cmd": "(중요: 모든 답변은 반드시 '한국어'로 작성해라. 절대 HTML 태그를 사용하지 말고, 오직 마크다운(Markdown) 문법만 사용하여 대답해라.)",
        "ship_title": "📦 한국 배송 (택배) 상세 안내",
        "ship_desc": """
        <div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'>
            <h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 배송 기본 정보</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>발송 일정:</b> 매주 화요일 / 목요일 오후 1시 일괄 발송</li>
                <li><b>배송 기간:</b> 영업일 기준 5~7일 소요</li>
                <li><b>면세 한도:</b> 건강기능식품 1인 1회 <b>최대 6병</b> (기타품목 최대 5kg)</li>
            </ul>
            <h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 통관 필수 준비물</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li>수취인 실명 및 한국 핸드폰 번호</li>
                <li><b>개인통관고유부호</b> (수취인 명의와 반드시 일치해야 합니다)</li>
                <li>정확한 도로명 주소</li>
            </ul>
        </div>
        """,
        "ship_warn": "⚠️ **주의:** 액체류(마누카꿀, 프로폴리스 리퀴드 등)는 기내 반입이 엄격히 금지되어 있습니다. 반드시 **위탁 수하물**로 부쳐주세요!",
        "trs_title": "💰 공항 텍스 리펀 (TRS) 완벽 가이드",
        "trs_desc": """
        <div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'>
            <h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 환급 기본 조건</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>구매 금액:</b> AGH 매장 단일 결제액 <b>$300 이상</b> 시 환급 가능</li>
                <li><b>환급률:</b> 결제 금액의 약 <b>9%</b> 환급</li>
            </ul>
            <h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 공항 필수 지참물 및 장소</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>준비물:</b> 매장 실물 영수증 (Tax Invoice), 구매한 제품 실물, 여권, 탑승권</li>
                <li><b>장소:</b> 시드니 공항 출국 심사(보안검색) 통과 후 면세구역(Airside) 내 <b>TRS 창구</b></li>
            </ul>
        </div>
        """,
        "trs_tip": "💡 **스마트 꿀팁:** 공항에 가시기 전, 스마트폰에 **'TRS 앱'**을 다운받아 영수증 정보와 환급받을 카드 정보를 미리 입력해 두세요! 전용 쾌속 라인을 통해 초고속으로 환급이 가능합니다."
    },
    "GB": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "Hello! I am **Bio**, the smart assistant at AGH Green Health. Ask me anything! 💚",
        "tab1": "💬 AI Consultation", "tab2": "📦 Shipping & TRS Guide", "tab3": "📱 Store Reels",
        "elderly_mode": "👵 Large Font Mode",
        "ai_lang_cmd": "(CRITICAL: Translate all your responses into English. Do not use HTML tags. Use only Markdown formatting.)",
        "ship_title": "📦 Shipping to South Korea",
        "ship_desc": """
        <div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'>
            <h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ Shipping Information</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>Dispatch:</b> Every Tuesday and Thursday at 1 PM</li>
                <li><b>Duration:</b> 5~7 business days</li>
                <li><b>Duty-Free Limit:</b> Max <b>6 bottles</b> of supplements per person</li>
            </ul>
            <h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ Customs Requirements</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li>Receiver's real name and Korean phone number</li>
                <li><b>PCCC (Personal Customs Clearance Code)</b></li>
                <li>Accurate Korean address</li>
            </ul>
        </div>
        """,
        "ship_warn": "⚠️ **Note:** Liquids (like Manuka Honey and Propolis Liquid) are strictly prohibited in carry-on baggage. Please ensure they are packed in your **checked luggage**!",
        "trs_title": "💰 TRS (Tourist Refund Scheme) Guide",
        "trs_desc": """
        <div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'>
            <h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ Refund Conditions</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>Condition:</b> Spend <b>$300 or more</b> in our store</li>
                <li><b>Refund Rate:</b> Approx. <b>9%</b> of the total amount</li>
            </ul>
            <h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ Requirements & Location</h4>
            <ul style='font-size:1.1rem; line-height:1.8; color:#333;'>
                <li><b>Required:</b> Original Tax Invoice, Purchased Goods, Passport, Boarding Pass</li>
                <li><b>Where:</b> TRS facility inside the airport (Airside) after immigration</li>
            </ul>
        </div>
        """,
        "trs_tip": "💡 **Smart Tip:** Before heading to the airport, download the **'TRS App'** on your smartphone. Enter your invoice details in advance for a much faster dedicated queue!"
    }
}

UI_TEXT["CN"] = UI_TEXT["GB"].copy() 
UI_TEXT["CN"].update({
    "greeting": "您好！我是AGH的智能助手 **Bio**。随时问我吧！💚", 
    "ai_lang_cmd": "(重要：请将所有回答完全翻译成中文。绝对不要使用HTML，只使用Markdown格式。)",
    "ship_title": "📦 韩国直邮指南",
    "ship_warn": "⚠️ **注意:** 液体（如麦卢卡蜂蜜，蜂胶液）严禁随身携带上飞机。请务必将它们放入**托运行李**中！",
    "trs_title": "💰 TRS (机场退税) 完美指南",
    "trs_tip": "💡 **温馨提示:** 去机场前，请在手机上下载 **'TRS App'** 并提前输入收据信息。您可以在机场使用专用快速通道，秒速退税！"
})

UI_TEXT["JP"] = UI_TEXT["GB"].copy()
UI_TEXT["JP"].update({
    "greeting": "こんにちは！AGHのスマートアシスタント、**Bio**です。何でもお尋ねください！💚", 
    "ai_lang_cmd": "(重要：すべての回答を日本語に翻訳してください。HTMLは使用せず、マークダウンのみを使用してください。)",
    "ship_title": "📦 韓国配送（宅配）詳細案内",
    "ship_warn": "⚠️ **注意:** 液体類（マヌカハニー、プロポリスリキッド等）は機内持ち込みが厳しく禁止されています。必ず**預け入れ荷物**に入れてください！",
    "trs_title": "💰 TRS (空港税金還付) 完璧ガイド",
    "trs_tip": "💡 **スマートなヒント:** 空港に向かう前に、スマートフォンに **'TRSアプリ'** をダウンロードし、レシート情報を事前に入力しておいてください！専用レーンでスムーズに還付手続きができます。"
})

# 음성 재생
async def generate_audio(text, lang_choice):
    voice = 'ko-KR-SunHiNeural'
    if lang_choice == 'GB': voice = 'en-US-AriaNeural'
    elif lang_choice == 'CN': voice = 'zh-CN-XiaoxiaoNeural'
    elif lang_choice == 'JP': voice = 'ja-JP-NanamiNeural'
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await communicate.save(fp.name)
        return fp.name

def autoplay_audio(text, lang_choice):
    try:
        audio_file = asyncio.run(generate_audio(text, lang_choice))
        with open(audio_file, "rb") as f: data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
        os.remove(audio_file)
    except: pass 

# ==========================================
# 🧹 [사이드바 구성]
# ==========================================
with st.sidebar:
    if logo_img_src:
        st.markdown(f'<img src="{logo_img_src}" style="width:100%; mix-blend-mode: multiply; margin-bottom: 10px;">', unsafe_allow_html=True)
        
    selected_lang_label = st.radio("🌐 언어 선택 (Language)", ["KR 한국어", "GB English", "CN 中文", "JP 日本語"], horizontal=True)
    lang_code = selected_lang_label[:2]
    t = UI_TEXT[lang_code]
    
    col_a, col_e = st.columns(2)
    audio_on = col_a.toggle("🔊 음성 출력", value=False)
    elderly_mode = col_e.toggle(t["elderly_mode"], value=False)
    
    if elderly_mode:
        st.markdown("""
        <style>
            html, body, [class*="st-"], p, span, div, h1, h2, h3, h4, h5, h6, li, .stMarkdown, button {
                font-size: 1.25rem !important;
            }
        </style>
        """, unsafe_allow_html=True)

    # 👑 사장님 강력 추천 랜덤 로테이션 (버튼)
    st.markdown('<div style="background: linear-gradient(135deg, #005A32, #2E7D32); color: white; padding: 12px; border-radius: 10px 10px 0 0; text-align: center; font-size: 1.05rem; font-weight: bold; margin-bottom: 0px;">👑 이번 주 사장님 강력 추천</div>', unsafe_allow_html=True)
    st.button(f"✨ {st.session_state.current_md_picks[0]}", on_click=trigger_ai_consultation, args=(f"'{st.session_state.current_md_picks[0]}' 제품을 상세히 설명해줘.", None), use_container_width=True, key="md_btn_1")
    st.button(f"✨ {st.session_state.current_md_picks[1]}", on_click=trigger_ai_consultation, args=(f"'{st.session_state.current_md_picks[1]}' 제품을 상세히 설명해줘.", None), use_container_width=True, key="md_btn_2")
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🔥 실시간 매장 TOP 5")
    top5_items = ["마누카꿀 MGO 850+", "초록입홍합 21000", "유칼립투스 프로폴리스", "아이젠 눈건강", "알티지 오메가3"]
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    for idx, top_name in enumerate(top5_items):
        st.button(f"{medals[idx]} {top_name}", key=f"top_{idx}", on_click=trigger_ai_consultation, args=(f"'{top_name}' 제품을 추천하며 상세하게 설명해줘.", None), use_container_width=True)

    st.markdown("### 📁 제품 카탈로그")
    cat_keys = list(categories_db.keys())
    grid_cols = st.columns(2)
    for idx, cat_name in enumerate(cat_keys):
        display_name = CATEGORY_EMOJIS.get(cat_name, f"📌 {cat_name[:6]}..")
        grid_cols[idx % 2].button(display_name, on_click=set_category, args=(cat_name,), use_container_width=True)

    # 🚨 AI 외계어(HTML) 출력 완벽 차단 프롬프트
    system_instruction = f"""
    너는 호주 프리미엄 건강식품 매장 'AGH GREENHEALTH'의 AI '바이오'야.
    제품 설명 시 절대 HTML 태그(<hr>, <div>, <h3> 등)를 사용하지 마라!
    오직 마크다운(Markdown) 문법(### 제목, **강조**, - 리스트, > 인용구)만 사용하여 가독성 좋고 예쁘게 작성해라.
    손님이 비교를 요청하면 마크다운 표(Table) 형식으로 정리해라.
    {t['ai_lang_cmd']}
    """
    model = genai.GenerativeModel(model_name='gemini-3.6-flash', system_instruction=system_instruction)

    st.divider()
    if kakao_img_src:
        st.markdown(f'**<img src="{kakao_img_src}" style="width: 25px; vertical-align: middle;"> 제휴 & 카톡 문의: mark5548**', unsafe_allow_html=True)
    else:
        st.markdown("💬 **제휴 & 카톡 문의: mark5548**")

    if qr_img_src:
        st.markdown(f'<div style="text-align: center; margin-top: 5px;"><img src="{qr_img_src}" style="width: 40%; border-radius: 8px;"></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("✈️ **오늘은 시드니 어디로 여행을 갈까?**")
    st.markdown("👉 **[MIN Tour & Travel 시드니 투어 문의](https://www.instagram.com/mintourtravel)**")

# ==========================================
# 📺 [메인 화면]
# ==========================================
st.title(t["title"])
tab1, tab2, tab3 = st.tabs([t["tab1"], t["tab2"], t["tab3"]])

# ----------------- [탭 1: AI 챗봇 & 카탈로그] -----------------
with tab1:
    
    if st.session_state.selected_category:
        cat_title = CATEGORY_EMOJIS.get(st.session_state.selected_category, st.session_state.selected_category)
        st.markdown(f"### {cat_title} 카탈로그")
        
        target_products = categories_db.get(st.session_state.selected_category, [])
        if target_products:
            cols = st.columns(3)
            for idx, prod in enumerate(target_products):
                p_name = prod.get("name", "제품명 없음")
                p_img = prod.get("image_file", "") 
                p_eff = prod.get("efficacy", "")
                
                with cols[idx % 3]:
                    with st.container(border=True):
                        img_path = f"images/{p_img}"
                        if p_img and os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            img_path = None
                            st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
                        
                        st.markdown(f'<span class="product-name">{p_name}</span>', unsafe_allow_html=True)
                        st.caption(f"{p_eff[:50]}..." if len(p_eff) > 50 else p_eff)
                        st.button("🔍 AI 설명 듣기", key=f"btn_{st.session_state.selected_category}_{idx}", on_click=trigger_ai_consultation, args=(f"'{p_name}' 상세하게 설명해줘.", img_path), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.button("❌ 닫기 (AI 상담으로 돌아가기)", on_click=set_category, args=(None,), use_container_width=True)
        st.divider()

    st.markdown(t["greeting"])
    
    if st.button("🔄 대화 초기화"):
        st.session_state.messages = []
        md_picks_pool = ["마누카꿀 MGO 850+", "초록입홍합 21000", "리트리플 폴리코사놀", "리버케어 간영양제", "프리미엄 빌베리 안구건조", "유칼립투스 프로폴리스"]
        st.session_state.current_md_picks = random.sample(md_picks_pool, 2)
        st.rerun()

    st.markdown("**🔍 빠른 테마 검색:**")
    h_col1, h_col2, h_col3 = st.columns(3)
    if h_col1.button("#✈️ 호주 귀국 필수 선물", use_container_width=True): trigger_ai_consultation("호주 귀국 시 가족과 지인들에게 선물하기 가장 좋은 베스트 제품들을 추천해 줘.", None)
    if h_col2.button("#👨‍👩‍👧‍👦 5060 부모님 효도 선물", use_container_width=True): trigger_ai_consultation("50대~60대 부모님 관절과 눈 건강에 좋은 효도 선물 세트를 추천해 줘.", None)
    if h_col3.button("#💻 만성피로 직장인 추천", use_container_width=True): trigger_ai_consultation("매일 야근하고 피곤한 직장인에게 간 건강과 피로회복에 좋은 제품을 비교해서 추천해 줘.", None)

    st.markdown("<br>", unsafe_allow_html=True)
    user_input = st.chat_input("바이오에게 질문하세요 (예: 뼈 관절 제품 비교해줘)...")
    prompt = st.session_state.chat_query if st.session_state.chat_query else user_input
    img_to_show = st.session_state.chat_img if st.session_state.chat_query else None
    
    if st.session_state.chat_query: 
        st.session_state.chat_query = None
        st.session_state.chat_img = None

    for message in st.session_state.messages:
        display_content = message["content"].replace(t["ai_lang_cmd"], "").strip()
        
        display_content = re.sub(r'```html\n?', '', display_content)
        display_content = re.sub(r'```\n?', '', display_content)
        
        if display_content:
            with st.chat_message(message["role"]): 
                if "image" in message and message["image"]:
                    st.image(message["image"], width=300)
                st.markdown(display_content, unsafe_allow_html=True)

    if prompt:
        injected_prompt = f"{prompt} \n\n{t['ai_lang_cmd']}"
        st.session_state.messages.append({"role": "user", "content": injected_prompt})
        with st.chat_message("user"): st.markdown(prompt)

        history_for_gemini = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]

        with st.chat_message("assistant"):
            if img_to_show and os.path.exists(img_to_show):
                st.image(img_to_show, width=300)
                
            with st.spinner("AI가 답변을 생성 중입니다..."):
                try:
                    chat = model.start_chat(history=history_for_gemini)
                    response = chat.send_message(injected_prompt)
                    ai_response = response.text
                    
                    cleaned_response = re.sub(r'```html\n?', '', ai_response)
                    cleaned_response = re.sub(r'```\n?', '', cleaned_response)
                    
                    st.markdown(cleaned_response, unsafe_allow_html=True)
                    if audio_on: autoplay_audio(cleaned_response, lang_code)
                    
                    assistant_msg = {"role": "assistant", "content": cleaned_response}
                    if img_to_show and os.path.exists(img_to_show):
                        assistant_msg["image"] = img_to_show
                        
                    st.session_state.messages.append(assistant_msg)
                except Exception:
                    st.error("⚠️ 시스템 오류가 발생했습니다.")

# ----------------- [탭 2: 다국어 택배 & TRS 가이드 고급형 디자인 적용] -----------------
with tab2:
    st.header(t["ship_title"])
    st.markdown(t["ship_desc"], unsafe_allow_html=True)
    st.warning(t["ship_warn"])
    
    st.divider()
    
    st.header(t["trs_title"])
    st.markdown(t["trs_desc"], unsafe_allow_html=True)
    st.success(t["trs_tip"])

# ----------------- [탭 3: 릴스 전용관] -----------------
with tab3:
    st.header("📸 매장 소식 (Store Reels)")
    mp4_files = [f for f in os.listdir(".") if f.endswith(".mp4")]
    if mp4_files:
        cols = st.columns(3)
        for idx, file in enumerate(mp4_files):
            with cols[idx % 3]: st.video(file)
    else:
        st.info("💡 폴더 안에 `.mp4` 영상을 넣으시면 자동 재생됩니다.")