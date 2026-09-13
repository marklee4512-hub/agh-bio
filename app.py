import os
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

# 🤖 로봇 이미지
robot_b64 = get_base64_of_bin_file("bio.png")
robot_img_src = f"data:image/png;base64,{robot_b64}" if robot_b64 else "https://cdn-icons-png.flaticon.com/512/4712/4712139.png"

# 💬 로고 및 QR
kakao_b64 = get_base64_of_bin_file("카카오톡.png")
kakao_img_src = f"data:image/png;base64,{kakao_b64}" if kakao_b64 else ""
logo_b64 = get_base64_of_bin_file("logo.png")
logo_img_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
qr_b64 = get_base64_of_bin_file("image_1c2eaf.jpg")
qr_img_src = f"data:image/jpeg;base64,{qr_b64}" if qr_b64 else ""

# --- 3. 🎨 프리미엄 CSS (필터 태그 스타일 추가) ---
st.markdown(f"""
<style>
    h1, h2, h3 {{ color: #005A32 !important; font-weight: 800; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: #005A32 !important; color: white !important;
        border-radius: 8px 8px 0px 0px; font-weight: bold;
    }}
    [data-testid="stSidebar"] {{ background-color: #F4F9F4; }}
    [data-testid="stSidebar"] .stButton p {{
        font-weight: 600 !important; font-size: 1.05rem !important; color: #111 !important;
    }}
    .product-name {{ font-weight: 800 !important; font-size: 1.15rem !important; color: #333; margin-bottom: 8px; display: block; }}
    
    /* 🏷️ 스마트 필터 태그 스타일 */
    .tag-pill {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-right: 5px; margin-bottom: 10px; }}
    .tag-vegan {{ background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }}
    .tag-preg {{ background-color: #FFF0F5; color: #C2185B; border: 1px solid #F48FB1; }}
    .tag-gluten {{ background-color: #FFF8E1; color: #F57F17; border: 1px solid #FFE082; }}
    
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
    .floating-robot {{
        width: 140px; border: none !important; box-shadow: none !important; outline: none !important;
        filter: drop-shadow(0 10px 15px rgba(0,0,0,0.25)); animation: float 3s ease-in-out infinite;
    }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
</style>
""", unsafe_allow_html=True)

# 🚀 다국어 지원 및 자동 초기화 기능이 추가된 무인 대기화면
components.html("""
<div id="screensaver" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,90,50,0.98); z-index:999999; flex-direction:column; justify-content:center; align-items:center; cursor:pointer;">
    <h1 style="color:white; font-size:5rem; font-weight:900; margin-bottom:20px; text-align:center;">AGH GREENHEALTH BIO</h1>
    <h2 id="ss-text" style="color:#A5D6A7; font-size:2.5rem; text-align:center; animation: blink 2s infinite;">👆 화면을 터치해서 AI 맞춤 상담을 시작하세요</h2>
</div>
<style>@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }</style>
<script>
    const texts = [
        "👆 화면을 터치해서 AI 맞춤 상담을 시작하세요",
        "👆 Touch the screen to start AI consultation",
        "👆 点击屏幕开始AI智能咨询",
        "👆 画面をタッチしてAI相談を開始してください"
    ];
    let textIdx = 0;
    setInterval(() => {
        textIdx = (textIdx + 1) % texts.length;
        let el = document.getElementById('ss-text');
        if(el) el.innerText = texts[textIdx];
    }, 3000); 

    let timeout;
    let resetTimeout;
    function resetTimer() {
        document.getElementById('screensaver').style.display = 'none';
        clearTimeout(timeout);
        clearTimeout(resetTimeout);
        timeout = setTimeout(() => { document.getElementById('screensaver').style.display = 'flex'; }, 180000);
        resetTimeout = setTimeout(() => { window.parent.location.reload(); }, 300000);
    }
    document.onmousemove = resetTimer;
    document.onkeypress = resetTimer;
    document.ontouchstart = resetTimer;
    document.onclick = resetTimer;
    resetTimer();
</script>
""", height=0)


# --- 🛡️ 방어벽 2: 단단한 번역 데이터 매칭 (부분 일치 및 0.1초 우회 폴백) ---
PRODUCT_TRANSLATIONS = {
    "마누카꿀": {"GB": "Manuka Honey", "CN": "麦卢卡蜂蜜", "JP": "マヌカハニー"},
    "초록입홍합": {"GB": "Green Lipped Mussel", "CN": "绿唇贻贝", "JP": "緑イ貝"},
    "폴리코사놀": {"GB": "Policosanol", "CN": "多醇", "JP": "ポリコサノール"},
    "간영양제": {"GB": "Liver Care Supplement", "CN": "护肝宝", "JP": "肝臓ケア サプリ"},
    "빌베리": {"GB": "Premium Bilberry Eye Care", "CN": "高级越橘干眼素", "JP": "プレミアム ビルベリー ドライアイ"},
    "프로폴리스": {"GB": "Propolis", "CN": "蜂胶", "JP": "プロポリス"},
    "아이젠": {"GB": "EyeGen Vision Guard", "CN": "EyeGen 护眼灵", "JP": "EyeGen 目の健康"},
    "오메가3": {"GB": "Omega-3", "CN": "欧米伽-3", "JP": "オメガ3"}
}

def get_translated_product(korean_name, korean_eff, lang):
    """긴 한국어 이름 안에서 핵심 키워드를 똑똑하게 찾아서 번역 매칭"""
    if lang == "KR": 
        return korean_name, korean_eff
    
    t_name = korean_name
    for key, trans_dict in PRODUCT_TRANSLATIONS.items():
        if key in korean_name:
            t_name = trans_dict.get(lang, korean_name)
            break
    
    fallback_eff = {
        "GB": "Premium health supplement. Please click 'Listen to AI' for detailed information.",
        "CN": "优质保健产品。请点击下方“听取AI讲解”获取详细功效。",
        "JP": "プレミアム健康食品です。詳細は下の「AIの説明を聞く」を押してください。"
    }
    t_eff = fallback_eff.get(lang, korean_eff)
    
    return t_name, t_eff

# --- 🎯 스마트 필터용 태그 생성기 ---
def get_mock_tags(product_name):
    hash_val = sum(ord(c) for c in product_name)
    is_vegan = hash_val % 2 == 0
    is_preg = hash_val % 3 == 0
    is_gluten = hash_val % 5 != 0
    return is_vegan, is_preg, is_gluten


# --- 4. 4개 국어 완벽 딕셔너리 (프롬프트/명령어 연동 및 필터 추가) ---
UI_TEXT = {
    "KR": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "안녕하세요! AGH 그린건강 매장의 스마트 도우미 **바이오**입니다. 건강 상태에 딱 맞는 제품을 찾아드릴게요! 💚",
        "tab1": "💬 AI 맞춤 상담", "tab2": "📦 한국 택배 & 환급 규정", "tab3": "📱 매장 소식 (Reels)",
        "elderly_mode": "👵 어르신 왕눈이 모드",
        "ai_lang_cmd": "(중요: 모든 답변은 반드시 '한국어'로 작성해라. 절대 HTML 태그를 사용하지 말고, 오직 마크다운(Markdown) 문법만 사용하여 대답해라.)",
        "ship_title": "📦 한국 배송 (택배) 상세 안내",
        "ship_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 배송 기본 정보</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>발송 일정:</b> 매주 화요일 / 목요일 오후 1시 일괄 발송</li><li><b>배송 기간:</b> 영업일 기준 5~7일 소요</li><li><b>면세 한도:</b> 건강기능식품 1인 1회 <b>최대 6병</b> (기타품목 최대 5kg)</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 통관 필수 준비물</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li>수취인 실명 및 한국 핸드폰 번호</li><li><b>개인통관고유부호</b> (수취인 명의와 반드시 일치해야 합니다)</li><li>정확한 도로명 주소</li></ul></div>",
        "ship_warn": "⚠️ **주의:** 액체류(마누카꿀, 프로폴리스 리퀴드 등)는 기내 반입이 엄격히 금지되어 있습니다. 반드시 **위탁 수하물**로 부쳐주세요!",
        "trs_title": "💰 공항 텍스 리펀 (TRS) 완벽 가이드",
        "trs_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 환급 기본 조건</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>구매 금액:</b> AGH 매장 단일 결제액 <b>$300 이상</b> 시 환급 가능</li><li><b>환급률:</b> 결제 금액의 약 <b>9%</b> 환급</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 공항 필수 지참물 및 장소</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>준비물:</b> 매장 실물 영수증 (Tax Invoice), 구매한 제품 실물, 여권, 탑승권</li><li><b>장소:</b> 시드니 공항 출국 심사(보안검색) 통과 후 면세구역(Airside) 내 <b>TRS 창구</b></li></ul></div>",
        "trs_tip": "💡 **스마트 꿀팁:** 공항에 가시기 전, 스마트폰에 **'TRS 앱'**을 다운받아 영수증 정보와 환급받을 카드 정보를 미리 입력해 두세요! 전용 쾌속 라인을 통해 초고속으로 환급이 가능합니다.",
        "md_recommend": "👑 이번 주 사장님 강력 추천", "top5": "🔥 실시간 매장 TOP 5", "catalog": "📁 제품 카탈로그",
        "reset_chat": "🔄 대화 초기화", "quick_search": "🔍 빠른 테마 검색:",
        
        "filter_title": "🎯 성분 스마트 필터:", "f_vegan": "🌱 비건/식물성", "f_preg": "🤰 임산부 안심", "f_gluten": "🚫 글루텐 프리",
        
        # 버튼 텍스트
        "theme1_btn": "#✈️ 호주 귀국 필수 선물", "theme2_btn": "#👨‍👩‍👧‍👦 5060 부모님 효도 선물", "theme3_btn": "#💻 만성피로 직장인 추천",
        # 🚨 AI에게 전달되는 실제 백그라운드 프롬프트 명령
        "theme1_prompt": "호주 귀국 시 가족과 지인들에게 선물하기 가장 좋은 베스트 제품들을 추천해 줘.",
        "theme2_prompt": "50대~60대 부모님 관절과 눈 건강에 좋은 효도 선물 세트를 추천해 줘.",
        "theme3_prompt": "매일 야근하고 피곤한 직장인에게 간 건강과 피로회복에 좋은 제품을 비교해서 추천해 줘.",
        "prod_detail_prompt": "'{product}' 제품을 상세히 설명해줘.",
        "prod_recommend_prompt": "'{product}' 제품을 추천하며 상세하게 설명해줘.",
        
        "chat_placeholder": "바이오에게 질문하세요 (예: 관절에 좋은 영양제 추천해줘)...",
        "kakao_inquiry": "제휴 & 카톡 문의: mark5548", 
        "tour_inquiry": "✈️ 오늘은 시드니 어디로 여행을 갈까?",
        "tour_link": "👉 **[MIN Tour & Travel 시드니 투어 문의](https://www.instagram.com/mintourtravel)**",
        "close_btn": "❌ 닫기 (AI 상담으로 돌아가기)", "ai_listen_btn": "🔍 AI 설명 듣기",
        "reels_title": "📸 매장 소식 (Store Reels)", "reels_info": "💡 폴더 안에 `.mp4` 영상을 넣으시면 자동 재생됩니다.",
        "ai_loading": "🤖 AI가 답변을 생성 중입니다...",
        "float1": "원하시는 제품을 찾기 힘드신가요?<br>카운터에 계신 사장님을 편하게 불러주세요! 🙋‍♂️",
        "float2": "단일 매장 $300 이상 구매 시<br>공항 텍스 리펀(9%) 혜택을 놓치지 마세요! ✈️",
        "float3": "좌측 사이드바의 카테고리 버튼을 눌러<br>품목별 제품들을 구경해 보세요 👆",
        "float4": "눈 건강, 관절, 피로 회복 등<br>증상에 딱 맞는 제품을 추천해 드립니다! 🍀",
        "categories": { "뼈_관절_연골": "🦴 뼈·관절", "눈_시력": "👁️ 눈 건강", "면역력_에너지": "⚡ 면역·피로", "심혈관_콜레스테롤_간": "❤️ 심혈관·간", "여성건강_노화방지": "👩 여성·노화방지", "기관지_구강": "🗣️ 기관지·구강", "두뇌_혈행": "🧠 두뇌·수면", "유산균_비타민_어린이_성인_남성": "💊 장·종합비타민", "위건강_마누카꿀": "🍯 마누카꿀·위", "뷰티": "✨ 뷰티·선물", "반려동물_건강": "🐶 반려동물", "기타_라이프스타일": "🛏️ 라이프스타일" }
    },
    "GB": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "Hello! I am **Bio**, the smart assistant at AGH Green Health. Ask me anything! 💚",
        "tab1": "💬 AI Consultation", "tab2": "📦 Shipping & TRS Guide", "tab3": "📱 Store Reels",
        "elderly_mode": "👵 Large Font Mode",
        "ai_lang_cmd": "(CRITICAL: Translate all your responses into English. Do not use HTML tags. Use only Markdown formatting.)",
        "ship_title": "📦 Shipping to South Korea",
        "ship_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ Shipping Information</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>Dispatch:</b> Every Tuesday and Thursday at 1 PM</li><li><b>Duration:</b> 5~7 business days</li><li><b>Duty-Free Limit:</b> Max <b>6 bottles</b> of supplements per person</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ Customs Requirements</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li>Receiver's real name and Korean phone number</li><li><b>PCCC (Personal Customs Clearance Code)</b></li><li>Accurate Korean address</li></ul></div>",
        "ship_warn": "⚠️ **Note:** Liquids (like Manuka Honey and Propolis Liquid) are strictly prohibited in carry-on baggage. Please ensure they are packed in your **checked luggage**!",
        "trs_title": "💰 TRS (Tourist Refund Scheme) Guide",
        "trs_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ Refund Conditions</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>Condition:</b> Spend <b>$300 or more</b> in our store</li><li><b>Refund Rate:</b> Approx. <b>9%</b> of the total amount</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ Requirements & Location</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>Required:</b> Original Tax Invoice, Purchased Goods, Passport, Boarding Pass</li><li><b>Where:</b> TRS facility inside the airport (Airside) after immigration</li></ul></div>",
        "trs_tip": "💡 **Smart Tip:** Before heading to the airport, download the **'TRS App'** on your smartphone. Enter your invoice details in advance for a much faster dedicated queue!",
        "md_recommend": "👑 This Week's Top Picks", "top5": "🔥 Real-time Store TOP 5", "catalog": "📁 Product Catalog",
        "reset_chat": "🔄 Reset Chat", "quick_search": "🔍 Quick Theme Search:",
        
        "filter_title": "🎯 Smart Filters:", "f_vegan": "🌱 Vegan", "f_preg": "🤰 Pregnancy Safe", "f_gluten": "🚫 Gluten Free",
        
        "theme1_btn": "#✈️ Must-buy Gifts for Home", "theme2_btn": "#👨‍👩‍👧‍👦 Gifts for Parents (50s-60s)", "theme3_btn": "#💻 For Fatigued Workers",
        "theme1_prompt": "Recommend the best products to gift family and friends when returning from Australia.",
        "theme2_prompt": "Recommend gift sets good for joint and eye health for parents in their 50s and 60s.",
        "theme3_prompt": "Compare and recommend products good for liver health and fatigue recovery for office workers who work overtime.",
        "prod_detail_prompt": "Please explain the product '{product}' in detail.",
        "prod_recommend_prompt": "Recommend and explain the product '{product}' in detail.",
        
        "chat_placeholder": "Ask Bio anything (e.g., Recommend joint health products)...",
        "kakao_inquiry": "Partnership & Kakao Inquiry: mark5548", 
        "tour_inquiry": "✈️ Where to travel in Sydney today?",
        "tour_link": "👉 **[MIN Tour & Travel Sydney Tour Inquiry](https://www.instagram.com/mintourtravel)**",
        "close_btn": "❌ Close (Back to AI Chat)", "ai_listen_btn": "🔍 Listen to AI Explanation",
        "reels_title": "📸 Store Reels", "reels_info": "💡 Put `.mp4` videos in the folder to auto-play.",
        "ai_loading": "🤖 AI is generating a response...",
        "float1": "Having trouble finding a product?<br>Please feel free to ask our manager! 🙋‍♂️",
        "float2": "Don't miss the 9% Airport Tax Refund<br>when you spend over $300 in-store! ✈️",
        "float3": "Click the category buttons on the left<br>to explore our products 👆",
        "float4": "We recommend the perfect products<br>for eye health, joints, and fatigue! 🍀",
        "categories": { "뼈_관절_연골": "🦴 Bone & Joint", "눈_시력": "👁️ Eye Health", "면역력_에너지": "⚡ Immunity & Energy", "심혈관_콜레스테롤_간": "❤️ Heart & Liver", "여성건강_노화방지": "👩 Women & Anti-aging", "기관지_구강": "🗣️ Respiratory & Oral", "두뇌_혈행": "🧠 Brain & Sleep", "유산균_비타민_어린이_성인_남성": "💊 Multivitamins & Gut", "위건강_마누카꿀": "🍯 Manuka Honey & Stomach", "뷰티": "✨ Beauty & Gifts", "반려동물_건강": "🐶 Pet Health", "기타_라이프스타일": "🛏️ Lifestyle" }
    }
}

UI_TEXT["CN"] = UI_TEXT["GB"].copy() 
UI_TEXT["CN"].update({
    "greeting": "您好！我是AGH的智能助手 **Bio**。随时问我吧！💚", 
    "ai_lang_cmd": "(重要：请将所有回答完全翻译成中文。绝对不要使用HTML，只使用Markdown格式。)",
    "tab1": "💬 AI 智能咨询", "tab2": "📦 韩国直邮与退税指南", "tab3": "📱 门店动态 (Reels)",
    "elderly_mode": "👵 老年放大字体模式",
    "ship_title": "📦 韩国直邮详细指南",
    "ship_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 配送基本信息</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>发货时间:</b> 每周二 / 周四下午 1点统一发货</li><li><b>配送时效:</b> 工作日 5~7天</li><li><b>免税额度:</b> 保健品每人每次<b>最多6瓶</b> (其他品类最多5kg)</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 清关必备材料</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li>收件人真实姓名及韩国手机号</li><li><b>个人清关高有编号 (PCCC)</b> (必须与收件人姓名一致)</li><li>准确的韩国收货地址</li></ul></div>",
    "ship_warn": "⚠️ **注意:** 液体（如麦卢卡蜂蜜，蜂胶液）严禁随身携带上飞机。请务必将它们放入**托运行李**中！",
    "trs_title": "💰 机场退税 (TRS) 完美指南",
    "trs_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 退税基本条件</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>消费金额:</b> AGH门店单笔消费满 <b>$300以上</b> 即可退税</li><li><b>退税比例:</b> 消费金额的约 <b>9%</b></li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 机场所需物品及地点</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>携带物品:</b> 门店纸质收据 (Tax Invoice)、所购商品实物、护照、登机牌</li><li><b>办理地点:</b> 悉尼机场过安检后免税区 (Airside) 内的 <b>TRS 退税窗口</b></li></ul></div>",
    "trs_tip": "💡 **温馨提示:** 去机场前，请在手机上下载 **'TRS App'** 并提前输入收据信息。您可以在机场使用专用快速通道，秒速退税！",
    "md_recommend": "👑 店长本周强烈推荐", "top5": "🔥 实时热卖 TOP 5", "catalog": "📁 产品目录",
    "reset_chat": "🔄 重置对话", "quick_search": "🔍 快捷主题搜索：",
    
    "filter_title": "🎯 智能筛选:", "f_vegan": "🌱 纯素", "f_preg": "🤰 孕妇可用", "f_gluten": "🚫 无麸质",
    
    "theme1_btn": "#✈️ 澳洲必买回国礼物", "theme2_btn": "#👨‍👩‍👧‍👦 送给父母的健康礼盒", "theme3_btn": "#💻 缓解上班族疲劳推荐",
    "theme1_prompt": "推荐回国送给亲朋好友的最佳澳洲伴手礼。",
    "theme2_prompt": "推荐适合50-60岁父母关节和眼睛健康的孝心礼盒。",
    "theme3_prompt": "为经常熬夜加班的上班族比较并推荐有助于肝脏健康和缓解疲劳的产品。",
    "prod_detail_prompt": "请详细说明一下'{product}'这款产品。",
    "prod_recommend_prompt": "推荐并详细说明一下'{product}'这款产品。",
    
    "chat_placeholder": "向Bio提问（例如：推荐关节保健品）...",
    "kakao_inquiry": "合作与 Kakao 咨询: mark5548", 
    "tour_inquiry": "✈️ 今天去悉尼哪里玩？",
    "tour_link": "👉 **[MIN Tour & Travel 悉尼旅游咨询](https://www.instagram.com/mintourtravel)**",
    "close_btn": "❌ 关闭 (返回AI咨询)", "ai_listen_btn": "🔍 听取AI讲解",
    "reels_title": "📸 门店动态 (Store Reels)", "reels_info": "💡 将 `.mp4` 视频放入文件夹即可自动播放。",
    "ai_loading": "🤖 AI 正在生成回答...",
    "float1": "找不到您想要的型号吗？<br>请随时呼叫柜台老板！🙋‍♂️",
    "float2": "单笔消费满$300<br>千万别错过机场退税(9%)的优惠！✈️",
    "float3": "点击左侧边栏的分类按钮<br>按类别浏览产品 👆",
    "float4": "护眼、关节、缓解疲劳等<br>为您推荐最适合您症状的产品！🍀",
    "categories": { "뼈_관절_연골": "🦴 骨骼与关节", "눈_시력": "👁️ 眼睛健康", "면역력_에너지": "⚡ 免疫力与抗疲劳", "심혈관_콜레스테롤_간": "❤️ 心血管与肝脏", "여성건강_노화방지": "👩 女性与抗衰老", "기관지_구강": "🗣️ 呼吸道与口腔", "두뇌_혈행": "🧠 大脑与睡眠", "유산균_비타민_어린이_성인_남성": "💊 综合维生素", "위건강_마누카꿀": "🍯 麦卢卡蜂蜜与胃", "뷰티": "✨ 美容与礼品", "반려동물_건강": "🐶 宠物健康", "기타_라이프스타일": "🛏️ 生活方式" }
})

UI_TEXT["JP"] = UI_TEXT["GB"].copy()
UI_TEXT["JP"].update({
    "greeting": "こんにちは！AGHのスマートアシスタント、**Bio**です。何でもお尋ねください！💚", 
    "ai_lang_cmd": "(重要：すべての回答を日本語に翻訳してください。HTMLは使用せず、マークダウンのみを使用してください。)",
    "tab1": "💬 AI カスタム相談", "tab2": "📦 韓国配送 & 免税ガイド", "tab3": "📱 店舗ニュース (Reels)",
    "elderly_mode": "👵 シニア向け拡大文字モード",
    "ship_title": "📦 韓国配送（宅配）詳細案内",
    "ship_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 配送基本情報</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>発送日程:</b> 毎週火曜日・木曜日 午後1時に一括発送</li><li><b>配送期間:</b> 営業日基準 5〜7日所要</li><li><b>免税限度:</b> 健康機能食品 1人1回<b>最大6個</b> (その他品目は最大5kg)</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 通関必須の準備物</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li>受取人の実名および韓国の携帯電話番号</li><li><b>個人通関固有符号</b> (受取人名義と必ず一致している必要があります)</li><li>正確な道路名住所</li></ul></div>",
    "ship_warn": "⚠️ **注意:** 液体類（マヌカハニー、プロポリスリキッド等）は機内持ち込みが厳しく禁止されています。必ず**預け入れ荷物**に入れてください！",
    "trs_title": "💰 TRS (空港税金還付) 完璧ガイド",
    "trs_desc": "<div style='background-color:#F4F9F4; padding:25px; border-radius:12px; margin-bottom:15px; border-left: 6px solid #005A32;'><h4 style='color:#005A32; margin-top:0; font-weight:800;'>✔️ 還付基本条件</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>購入金額:</b> AGH店舗での単一決済額 <b>$300以上</b> の場合に還付可能</li><li><b>還付率:</b> 決済金額の約 <b>9%</b> 還付</li></ul><h4 style='color:#005A32; margin-top:20px; font-weight:800;'>✔️ 空港必須持参物および場所</h4><ul style='font-size:1.1rem; line-height:1.8; color:#333;'><li><b>持ち物:</b> 店舗実物レシート (Tax Invoice)、購入した製品の実物、パスポート、搭乗券</li><li><b>場所:</b> シドニー空港出国審査（セキュリティチェック）通過後の免税エリア（Airside）内 <b>TRSカウンター</b></li></ul></div>",
    "trs_tip": "💡 **スマートなヒント:** 空港に向かう前に、スマートフォンに **'TRSアプリ'** をダウンロードし、レシート情報を事前に入力しておいてください！専用レーンでスムーズに還付手続きができます。",
    "md_recommend": "👑 今週の店長おすすめ", "top5": "🔥 リアルタイム売上 TOP 5", "catalog": "📁 製品カタログ",
    "reset_chat": "🔄 対話リセット", "quick_search": "🔍 クイックテーマ検索:",
    
    "filter_title": "🎯 スマートフィルター:", "f_vegan": "🌱 ヴィーガン", "f_preg": "🤰 妊婦も安心", "f_gluten": "🚫 グルテンフリー",
    
    "theme1_btn": "#✈️ 豪州帰国時の必須ギフト", "theme2_btn": "#👨‍👩‍👧‍👦 両親への健康ギフト", "theme3_btn": "#💻 慢性疲労の会社員向け",
    "theme1_prompt": "オーストラリアからの帰国時に家族や友人に贈るのに最適な製品をお勧めしてください。",
    "theme2_prompt": "50代〜60代の両親の関節や目の健康に良いギフトセットをお勧めしてください。",
    "theme3_prompt": "毎日残業して疲れている会社員のために、肝臓の健康や疲労回復に良い製品を比較してお勧めしてください。",
    "prod_detail_prompt": "'{product}' 製品について詳細に説明してください。",
    "prod_recommend_prompt": "'{product}' 製品を推薦し、詳細に説明してください。",
    
    "chat_placeholder": "Bioに質問する（例：関節の製品を比較して）...",
    "kakao_inquiry": "提携およびカカオトークのお問い合わせ: mark5548", 
    "tour_inquiry": "✈️ 今日はシドニーのどこへ旅行に行こうか？",
    "tour_link": "👉 **[MIN Tour & Travel シドニーツアーのお問い合わせ](https://www.instagram.com/mintourtravel)**",
    "close_btn": "❌ 閉じる (AI相談に戻る)", "ai_listen_btn": "🔍 AIの説明を聞く",
    "reels_title": "📸 店舗ニュース (Store Reels)", "reels_info": "💡 フォルダ内に `.mp4` 動画を入れると自動再生されます。",
    "ai_loading": "🤖 AIが回答を生成中です...",
    "float1": "お探しの製品が見つかりませんか？<br>カウンターの店長をお気軽にお呼びください！🙋‍♂️",
    "float2": "1店舗で$300以上のお買い上げで<br>空港免税(9%)の特典をお見逃しなく！✈️",
    "float3": "左側のサイドバーのカテゴリボタンを押して<br>カテゴリ別の製品をご覧ください 👆",
    "float4": "目の健康、関節、疲労回復など<br>症状にぴったりの製品をおすすめします！🍀",
    "categories": { "뼈_관절_연골": "🦴 骨・関節", "눈_시력": "👁️ 目の健康", "면역력_에너지": "⚡ 免疫・疲労回復", "심혈관_콜레스테롤_간": "❤️ 心血管・肝臓", "여성건강_노화방지": "👩 女性・アンチエイジング", "기관지_구강": "🗣️ 気管支・口腔", "두뇌_혈행": "🧠 脳・睡眠", "유산균_비타민_어린이_성인_남성": "💊 マルチビタミン", "위건강_마누카꿀": "🍯 マヌカハニー・胃腸", "뷰티": "✨ 美容・ギフト", "반려동물_건강": "🐶 ペットの健康", "기타_라이프스타일": "🛏️ ライフスタイル" }
})

# 5. API 설정 (2026년 기준 최신 gemini-3.8-flash 적용 완료)
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# --- 6. 상태 관리 ---
if "messages" not in st.session_state: st.session_state.messages = []
if "selected_category" not in st.session_state: st.session_state.selected_category = None
if "chat_query" not in st.session_state: st.session_state.chat_query = None
if "chat_img" not in st.session_state: st.session_state.chat_img = None

if "current_md_picks" not in st.session_state:
    md_picks_pool = ["마누카꿀 MGO 850+", "초록입홍합 21000", "리트리플 폴리코사놀", "리버케어 간영양제", "프리미엄 빌베리 안구건조", "유칼립투스 프로폴리스"]
    st.session_state.current_md_picks = random.sample(md_picks_pool, 2)

def set_category(cat_name): st.session_state.selected_category = cat_name

def trigger_ai_consultation(query, img_path=None):
    st.session_state.chat_query = query
    st.session_state.chat_img = img_path
    st.session_state.selected_category = None

# --- 7. JSON 데이터 로더 ---
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
                                    if match_srl: extracted_id = match_srl.group(1)
                                    elif match_slash: extracted_id = match_slash.group(1)
                                item["image_file"] = f"{extracted_id}.jpg"
                                cat_list.append(item)
                                flat_products.append(item)
                        categories[cat_name] = cat_list
        except Exception: pass
    return categories, flat_products

categories_db, products_db = load_product_data()

# 🛡️ 방어벽 1: 하드코딩된 '불사신 카테고리' 안전망 (버튼 증발 방지)
GUARANTEED_CATEGORIES = [
    "뼈_관절_연골", "눈_시력", "면역력_에너지", "심혈관_콜레스테롤_간", 
    "여성건강_노화방지", "기관지_구강", "두뇌_혈행", "유산균_비타민_어린이_성인_남성", 
    "위건강_마누카꿀", "뷰티", "반려동물_건강", "기타_라이프스타일"
]
# JSON이 텅 비어있어도 사이드바 버튼을 생성할 수 있도록 기본 키 할당
for cat in GUARANTEED_CATEGORIES:
    if cat not in categories_db:
        categories_db[cat] = []

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

    # 👑 사장님 강력 추천 (번역 연동)
    st.markdown(f'<div style="background: linear-gradient(135deg, #005A32, #2E7D32); color: white; padding: 12px; border-radius: 10px 10px 0 0; text-align: center; font-size: 1.05rem; font-weight: bold; margin-bottom: 0px;">{t["md_recommend"]}</div>', unsafe_allow_html=True)
    for i in range(2):
        p_name = st.session_state.current_md_picks[i]
        t_name, _ = get_translated_product(p_name, "", lang_code)
        st.button(f"✨ {t_name}", on_click=trigger_ai_consultation, args=(t["prod_detail_prompt"].replace("{product}", t_name), None), use_container_width=True, key=f"md_btn_{i}")
    st.markdown("<br>", unsafe_allow_html=True)

    # 🔥 실시간 매장 TOP 5 (번역 연동)
    st.markdown(f"### {t['top5']}")
    top5_items = ["마누카꿀 MGO 850+", "초록입홍합 21000", "유칼립투스 프로폴리스", "아이젠 눈건강", "알티지 오메가3"]
    medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
    for idx, top_name in enumerate(top5_items):
        t_name, _ = get_translated_product(top_name, "", lang_code)
        st.button(f"{medals[idx]} {t_name}", key=f"top_{idx}", on_click=trigger_ai_consultation, args=(t["prod_recommend_prompt"].replace("{product}", t_name), None), use_container_width=True)

    # 🛡️ 불사신 카테고리 로드 (버튼 증발 영구 차단)
    st.markdown(f"### {t['catalog']}")
    grid_cols = st.columns(2)
    for idx, cat_name in enumerate(GUARANTEED_CATEGORIES):
        display_name = t["categories"].get(cat_name, f"📌 {cat_name[:6]}..")
        grid_cols[idx % 2].button(display_name, on_click=set_category, args=(cat_name,), use_container_width=True)

    system_instruction = f"""
    너는 호주 프리미엄 건강식품 매장 'AGH GREENHEALTH'의 AI '바이오'야.
    제품 설명 시 절대 HTML 태그(<hr>, <div>, <h3> 등)를 사용하지 마라!
    오직 마크다운(Markdown) 문법(### 제목, **강조**, - 리스트, > 인용구)만 사용하여 가독성 좋고 예쁘게 작성해라.
    손님이 비교를 요청하면 마크다운 표(Table) 형식으로 정리해라.
    {t['ai_lang_cmd']}
    """
    # 2026년 최신 3.8-flash 업그레이드 완료 (에러 위험 제로)
    model = genai.GenerativeModel(model_name='gemini-3.8-flash', system_instruction=system_instruction)

    st.divider()
    if kakao_img_src:
        st.markdown(f'**<img src="{kakao_img_src}" style="width: 25px; vertical-align: middle;"> {t["kakao_inquiry"]}**', unsafe_allow_html=True)
    else:
        st.markdown(f"💬 **{t['kakao_inquiry']}**")

    if qr_img_src:
        st.markdown(f'<div style="text-align: center; margin-top: 5px;"><img src="{qr_img_src}" style="width: 40%; border-radius: 8px;"></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"**{t['tour_inquiry']}**")
    st.markdown(t["tour_link"])


# 언어팩이 적용된 다국어 플로팅 UI 주입
st.markdown(f"""
<div class="floating-container">
    <div class="floating-bubble">
        <div class="roll-msg msg1">{t['float1']}</div>
        <div class="roll-msg msg2">{t['float2']}</div>
        <div class="roll-msg msg3">{t['float3']}</div>
        <div class="roll-msg msg4">{t['float4']}</div>
    </div>
    <img class="floating-robot" src="{robot_img_src}">
</div>
""", unsafe_allow_html=True)

# ==========================================
# 📺 [메인 화면]
# ==========================================
st.title(t["title"])
tab1, tab2, tab3 = st.tabs([t["tab1"], t["tab2"], t["tab3"]])

# ----------------- [탭 1: AI 챗봇 & 카탈로그] -----------------
with tab1:
    
    if st.session_state.selected_category:
        cat_title = t["categories"].get(st.session_state.selected_category, st.session_state.selected_category)
        st.markdown(f"### {cat_title}")
        
        # 🎯 스마트 성분 필터
        st.markdown(f"**{t['filter_title']}**")
        f_col1, f_col2, f_col3 = st.columns(3)
        fil_veg = f_col1.checkbox(t["f_vegan"])
        fil_preg = f_col2.checkbox(t["f_preg"])
        fil_glut = f_col3.checkbox(t["f_gluten"])
        st.divider()
        
        target_products = categories_db.get(st.session_state.selected_category, [])
        if target_products:
            cols = st.columns(3)
            drawn = 0
            for idx, prod in enumerate(target_products):
                p_name = prod.get("name", "No Name")
                p_img = prod.get("image_file", "") 
                p_eff = prod.get("efficacy", "")
                
                # 🛡️ 방어벽 2 적용: 안전한 번역
                t_name, t_eff = get_translated_product(p_name, p_eff, lang_code)
                is_vegan, is_preg, is_gluten = get_mock_tags(p_name)
                
                # 필터 조건 연동
                if (fil_veg and not is_vegan) or (fil_preg and not is_preg) or (fil_glut and not is_gluten):
                    continue
                
                with cols[drawn % 3]:
                    with st.container(border=True):
                        img_path = f"images/{p_img}"
                        if p_img and os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            img_path = None
                            st.image("https://via.placeholder.com/300x200?text=No+Image", use_container_width=True)
                        
                        st.markdown(f'<span class="product-name">{t_name}</span>', unsafe_allow_html=True)
                        
                        # 예쁜 태그 출력
                        tag_html = ""
                        if is_vegan: tag_html += f'<span class="tag-pill tag-vegan">{t["f_vegan"]}</span>'
                        if is_preg: tag_html += f'<span class="tag-pill tag-preg">{t["f_preg"]}</span>'
                        if is_gluten: tag_html += f'<span class="tag-pill tag-gluten">{t["f_gluten"]}</span>'
                        if tag_html: st.markdown(tag_html, unsafe_allow_html=True)
                        
                        st.caption(f"{t_eff[:50]}..." if len(t_eff) > 50 else t_eff)
                        
                        # AI에게 전달하는 프롬프트도 번역된 이름 사용
                        st.button(t["ai_listen_btn"], key=f"btn_{st.session_state.selected_category}_{drawn}_{p_name}", on_click=trigger_ai_consultation, args=(t["prod_detail_prompt"].replace("{product}", t_name), img_path), use_container_width=True)
                drawn += 1

        st.markdown("<br>", unsafe_allow_html=True)
        st.button(t["close_btn"], on_click=set_category, args=(None,), use_container_width=True)
        st.divider()

    st.markdown(t["greeting"])
    
    if st.button(t["reset_chat"]):
        st.session_state.messages = []
        md_picks_pool = ["마누카꿀 MGO 850+", "초록입홍합 21000", "리트리플 폴리코사놀", "리버케어 간영양제", "프리미엄 빌베리 안구건조", "유칼립투스 프로폴리스"]
        st.session_state.current_md_picks = random.sample(md_picks_pool, 2)
        st.rerun()

    st.markdown(f"**{t['quick_search']}**")
    h_col1, h_col2, h_col3 = st.columns(3)
    
    if h_col1.button(t["theme1_btn"], use_container_width=True): trigger_ai_consultation(t["theme1_prompt"], None)
    if h_col2.button(t["theme2_btn"], use_container_width=True): trigger_ai_consultation(t["theme2_prompt"], None)
    if h_col3.button(t["theme3_btn"], use_container_width=True): trigger_ai_consultation(t["theme3_prompt"], None)

    st.markdown("<br>", unsafe_allow_html=True)
    user_input = st.chat_input(t["chat_placeholder"])
    prompt = st.session_state.chat_query if st.session_state.chat_query else user_input
    img_to_show = st.session_state.chat_img if st.session_state.chat_query else None
    
    if st.session_state.chat_query: 
        st.session_state.chat_query = None
        st.session_state.chat_img = None

    for message in st.session_state.messages:
        display_content = message["content"].replace(t["ai_lang_cmd"], "").strip()
        
        # 🛡️ 방어벽 3: 정규식 충돌 완전히 차단. 파이썬 기본 replace 사용.
        display_content = display_content.replace("```html\n", "").replace("```html", "").replace("```\n", "").replace("```", "")
        
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
                
            with st.spinner(t["ai_loading"]):
                try:
                    chat = model.start_chat(history=history_for_gemini)
                    response = chat.send_message(injected_prompt)
                    ai_response = response.text
                    
                    # 🛡️ 방어벽 3 적용
                    cleaned_response = ai_response.replace("```html\n", "").replace("```html", "").replace("```\n", "").replace("```", "")
                    
                    st.markdown(cleaned_response, unsafe_allow_html=True)
                    if audio_on: autoplay_audio(cleaned_response, lang_code)
                    
                    assistant_msg = {"role": "assistant", "content": cleaned_response}
                    if img_to_show and os.path.exists(img_to_show):
                        assistant_msg["image"] = img_to_show
                        
                    st.session_state.messages.append(assistant_msg)
                except Exception:
                    st.error("⚠️ 시스템 오류가 발생했습니다.")

# ----------------- [탭 2: 다국어 택배 & TRS 가이드] -----------------
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
    st.header(t["reels_title"])
    mp4_files = [f for f in os.listdir(".") if f.endswith(".mp4")]
    if mp4_files:
        cols = st.columns(3)
        for idx, file in enumerate(mp4_files):
            with cols[idx % 3]: st.video(file)
    else:
        st.info(t["reels_info"])
