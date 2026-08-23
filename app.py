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

st.set_page_config(page_title="AGH GREENHEALTH BIO", page_icon="🍀", layout="wide")

# --- 이미지 Base64 인코더 ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

robot_img_src = f"data:image/png;base64,{get_base64_of_bin_file('bio.png')}" or "https://cdn-icons-png.flaticon.com/512/4712/4712139.png"
kakao_img_src = f"data:image/png;base64,{get_base64_of_bin_file('카카오톡.png')}"
logo_img_src = f"data:image/png;base64,{get_base64_of_bin_file('logo.png')}"
qr_img_src = f"data:image/jpeg;base64,{get_base64_of_bin_file('image_1c2eaf.jpg')}"

# --- CSS ---
st.markdown(f"""
<style>
    h1, h2, h3 {{ color: #005A32 !important; font-weight: 800; }}
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        background-color: #005A32 !important; color: white !important;
        border-radius: 8px 8px 0px 0px; font-weight: bold;
    }}
    [data-testid="stSidebar"] {{ background-color: #F4F9F4; }}
    .product-name {{ font-weight: 800 !important; font-size: 1.15rem !important; color: #333; margin-bottom: 8px; display: block; }}
    .tag-pill {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-right: 5px; margin-bottom: 10px; }}
    .tag-vegan {{ background-color: #E8F5E9; color: #2E7D32; }}
    .tag-preg {{ background-color: #FFF0F5; color: #C2185B; }}
    .tag-gluten {{ background-color: #FFF8E1; color: #F57F17; }}
    
    .floating-container {{ position: fixed; bottom: 30px; right: 30px; z-index: 9999; display: flex; align-items: flex-end; gap: 10px; }}
    .floating-bubble {{ background: rgba(255, 255, 255, 0.95); border: 2.5px solid #005A32; border-radius: 18px 18px 0 18px; padding: 15px 20px; width: 270px; height: 100px; position: relative; margin-bottom: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); }}
    .floating-bubble::after {{ content: ''; position: absolute; bottom: 0; right: -12px; border-width: 14px 0 0 14px; border-style: solid; border-color: transparent transparent transparent rgba(255, 255, 255, 0.95); }}
    .roll-msg {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; text-align: center; font-size: 0.9rem; font-weight: 700; color: #005A32; opacity: 0; animation: fadeCycle 32s infinite; line-height: 1.4; }}
    .msg1 {{ animation-delay: 0s; }} .msg2 {{ animation-delay: 8s; }} .msg3 {{ animation-delay: 16s; }} .msg4 {{ animation-delay: 24s; }}
    @keyframes fadeCycle {{ 0%, 20% {{ opacity: 1; }} 23%, 100% {{ opacity: 0; }} }}
    .floating-robot {{ width: 140px; filter: drop-shadow(0 10px 15px rgba(0,0,0,0.25)); animation: float 3s ease-in-out infinite; }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} }}
</style>
""", unsafe_allow_html=True)

# 🚀 다국어 대기화면 및 자동 초기화
components.html("""
<div id="screensaver" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,90,50,0.98); z-index:999999; flex-direction:column; justify-content:center; align-items:center; cursor:pointer;">
    <h1 style="color:white; font-size:5rem; font-weight:900; margin-bottom:20px; text-align:center;">AGH GREENHEALTH BIO</h1>
    <h2 id="ss-text" style="color:#A5D6A7; font-size:2.5rem; text-align:center; animation: blink 2s infinite;">👆 화면을 터치해서 AI 맞춤 상담을 시작하세요</h2>
</div>
<style>@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }</style>
<script>
    const texts = ["👆 화면을 터치해서 AI 맞춤 상담을 시작하세요", "👆 Touch the screen to start AI consultation", "👆 点击屏幕开始AI智能咨询", "👆 画面をタッチしてAI相談を開始してください"];
    let textIdx = 0;
    setInterval(() => { textIdx = (textIdx + 1) % texts.length; let el = document.getElementById('ss-text'); if(el) el.innerText = texts[textIdx]; }, 3000); 
    let timeout, resetTimeout;
    function resetTimer() {
        document.getElementById('screensaver').style.display = 'none';
        clearTimeout(timeout); clearTimeout(resetTimeout);
        timeout = setTimeout(() => { document.getElementById('screensaver').style.display = 'flex'; }, 180000);
        resetTimeout = setTimeout(() => { window.parent.location.reload(); }, 300000);
    }
    document.onmousemove = document.onkeypress = document.ontouchstart = document.onclick = resetTimer;
    resetTimer();
</script>
""", height=0)

# --- 단단한 번역 데이터 매칭 (0.1초 우회 폴백) ---
PRODUCT_TRANSLATIONS = {
    "마누카꿀 MGO 850+": {"GB": "Manuka Honey MGO 850+", "CN": "麦卢卡蜂蜜 MGO 850+", "JP": "マヌカハニー MGO 850+"},
    "초록입홍합 21000": {"GB": "Green Lipped Mussel 21000", "CN": "绿唇贻贝 21000", "JP": "緑イ貝 21000"},
    "리트리플 폴리코사놀": {"GB": "Re-Triple Policosanol", "CN": "三重多醇", "JP": "リトリプル ポリコサノール"},
    "리버케어 간영양제": {"GB": "Liver Care Supplement", "CN": "护肝宝", "JP": "肝臓ケア サプリ"},
    "프리미엄 빌베리 안구건조": {"GB": "Premium Bilberry Eye Care", "CN": "高级越橘干眼素", "JP": "プレミアム ビルベリー ドライアイ"},
    "유칼립투스 프로폴리스": {"GB": "Eucalyptus Propolis", "CN": "桉树蜂胶", "JP": "ユーカリ プロポリス"},
    "아이젠 눈건강": {"GB": "EyeGen Vision Guard", "CN": "EyeGen 护眼灵", "JP": "EyeGen 目の健康"},
    "알티지 오메가3": {"GB": "rTG Omega-3", "CN": "rTG 欧米伽-3", "JP": "rTG オメガ3"}
}

def get_translated_product(korean_name, korean_eff, lang):
    if lang == "KR": return korean_name, korean_eff
    
    # 이름 번역 매칭
    t_name = PRODUCT_TRANSLATIONS.get(korean_name, {}).get(lang, korean_name) # 없으면 한국어 원문 유지
    
    # 설명(Efficacy) 폴백 (번역본이 없으면 AI에게 물어보라는 안내문구로 대체)
    fallback_eff = {
        "GB": "Premium health supplement. Please click 'Listen to AI' for detailed information.",
        "CN": "优质保健产品。请点击下方“听取AI讲解”获取详细功效。",
        "JP": "プレミアム健康食品です。詳細は下の「AIの説明を聞く」を押してください。"
    }
    t_eff = fallback_eff.get(lang, korean_eff)
    
    return t_name, t_eff

# 가상 가격 및 스마트 태그 생성기 (제품명 기반으로 항상 동일한 결과 반환)
def get_mock_data(product_name):
    hash_val = sum(ord(c) for c in product_name)
    price = (hash_val % 70) + 30 # $30 ~ $100 사이
    is_vegan = hash_val % 2 == 0
    is_preg = hash_val % 3 == 0
    is_gluten = hash_val % 5 != 0
    return price, is_vegan, is_preg, is_gluten

# --- 4개 국어 UI 딕셔너리 ---
UI_TEXT = {
    "KR": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "안녕하세요! AGH 그린건강 매장의 스마트 도우미 **바이오**입니다. 건강 상태에 딱 맞는 제품을 찾아드릴게요! 💚",
        "tab1": "💬 AI 맞춤 상담", "tab2": "📦 한국 택배 규정", "tab3": "🗺️ 시드니 여행 꿀팁", "tab4": "🛒 장바구니 & TRS 계산기", "tab5": "📱 매장 소식 (Reels)",
        "elderly_mode": "👵 어르신 왕눈이 모드",
        "ai_lang_cmd": "(중요: 모든 답변은 반드시 '한국어'로 작성해라.)",
        "md_recommend": "👑 이번 주 사장님 강력 추천", "top5": "🔥 실시간 매장 TOP 5", "catalog": "📁 제품 카탈로그",
        "reset_chat": "🔄 대화 초기화", "quick_search": "🔍 빠른 테마 검색:",
        "theme1_btn": "#✈️ 호주 귀국 필수 선물", "theme2_btn": "#👨‍👩‍👧‍👦 5060 부모님 효도 선물", "theme3_btn": "#💻 만성피로 직장인 추천",
        "theme1_prompt": "호주 귀국 시 가족과 지인들에게 선물하기 가장 좋은 베스트 제품들을 추천해 줘.",
        "theme2_prompt": "50대~60대 부모님 관절과 눈 건강에 좋은 효도 선물 세트를 추천해 줘.",
        "theme3_prompt": "야근하는 직장인에게 간 건강과 피로회복에 좋은 제품을 비교해서 추천해 줘.",
        "prod_detail_prompt": "'{product}' 제품을 상세히 설명해줘.",
        "prod_recommend_prompt": "'{product}' 제품을 추천하며 상세하게 설명해줘.",
        "chat_placeholder": "바이오에게 질문하세요 (예: 관절에 좋은 영양제 추천해줘)...",
        "kakao_inquiry": "제휴 & 카톡 문의: mark5548", 
        "close_btn": "❌ 닫기", "ai_listen_btn": "🔍 AI 설명 듣기", "add_to_cart": "🛒 장바구니 담기",
        "filter_title": "🎯 성분 스마트 필터:", "f_vegan": "🌱 글루텐 프리", "f_preg": "🤰 임산부 안심", "f_gluten": "🚫 락토 프리",
        "cart_title": "내 장바구니 및 TRS(텍스 리펀) 계산기", "cart_empty": "장바구니가 비어 있습니다. 카탈로그에서 제품을 담아보세요!",
        "total_price": "총 예상 금액: ${total}", "trs_success": "🎉 $300 달러 달성! 공항에서 약 **${trs}** 달러를 환급받으실 수 있습니다.", "trs_short": "💡 ${short} 달러만 더 담으시면 공항에서 9% 세금 환급이 가능합니다!",
        "tips_title": "🇦🇺 시드니 여행 & 쇼핑 꿀팁", "tips_content": "✔️ **TRS 환급 앱 미리 깔기:** 공항 가기 전 휴대폰에 TRS 어플을 깔아두면 쾌속 라인으로 통과 가능합니다!<br>✔️ **인생샷 명소:** 오페라 하우스 앞 바에서 노을 질 때 맥주 한 잔은 국룰입니다.",
        "categories": { "뼈_관절_연골": "🦴 뼈·관절", "눈_시력": "👁️ 눈 건강", "면역력_에너지": "⚡ 면역·피로", "심혈관_콜레스테롤_간": "❤️ 심혈관·간", "여성건강_노화방지": "👩 여성·노화방지", "기관지_구강": "🗣️ 기관지·구강", "두뇌_혈행": "🧠 두뇌·수면", "유산균_비타민": "💊 장·비타민", "위건강_마누카꿀": "🍯 마누카꿀·위", "뷰티": "✨ 뷰티·선물", "반려동물_건강": "🐶 반려동물", "기타_라이프스타일": "🛏️ 라이프스타일" }
    },
    "GB": {
        "title": "🍀 AGH GREENHEALTH AI : Bio",
        "greeting": "Hello! I am **Bio**, the smart assistant at AGH Green Health. Ask me anything! 💚",
        "tab1": "💬 AI Consultation", "tab2": "📦 Shipping Guide", "tab3": "🗺️ Sydney Travel Tips", "tab4": "🛒 Cart & TRS Calc", "tab5": "📱 Store Reels",
        "elderly_mode": "👵 Large Font Mode",
        "ai_lang_cmd": "(CRITICAL: Translate all your responses into English.)",
        "md_recommend": "👑 Top Picks", "top5": "🔥 Store TOP 5", "catalog": "📁 Catalog",
        "reset_chat": "🔄 Reset Chat", "quick_search": "🔍 Quick Theme Search:",
        "theme1_btn": "#✈️ Must-buy Gifts", "theme2_btn": "#👨‍👩‍👧‍👦 Gifts for Parents", "theme3_btn": "#💻 For Fatigued Workers",
        "theme1_prompt": "Recommend the best products to gift family and friends when returning from Australia.",
        "theme2_prompt": "Recommend gift sets good for joint and eye health for parents.",
        "theme3_prompt": "Recommend products good for liver health and fatigue recovery.",
        "prod_detail_prompt": "Please explain the product '{product}' in detail.",
        "prod_recommend_prompt": "Recommend and explain the product '{product}' in detail.",
        "chat_placeholder": "Ask Bio anything...",
        "kakao_inquiry": "Kakao Inquiry: mark5548", 
        "close_btn": "❌ Close", "ai_listen_btn": "🔍 Listen to AI", "add_to_cart": "🛒 Add to Cart",
        "filter_title": "🎯 Smart Filters:", "f_vegan": "🌱 Gluten Free", "f_preg": "🤰 Pregnancy Safe", "f_gluten": "🚫 Lactose Free",
        "cart_title": "My Cart & TRS Calculator", "cart_empty": "Your cart is empty. Add products from the catalog!",
        "total_price": "Total Estimated: ${total}", "trs_success": "🎉 $300 reached! You can get approx **${trs}** refunded at the airport.", "trs_short": "💡 Add ${short} more to be eligible for a 9% tax refund at the airport!",
        "tips_title": "🇦🇺 Sydney Travel & Shopping Tips", "tips_content": "✔️ **Download TRS App:** Pre-enter your details in the TRS app before heading to the airport for a faster queue!<br>✔️ **Must-Do:** Enjoy a beer at the Opera House bar during sunset.",
        "categories": { "뼈_관절_연골": "🦴 Bone & Joint", "눈_시력": "👁️ Eye Health", "면역력_에너지": "⚡ Immunity & Energy", "심혈관_콜레스테롤_간": "❤️ Heart & Liver", "여성건강_노화방지": "👩 Women & Anti-aging", "기관지_구강": "🗣️ Respiratory & Oral", "두뇌_혈행": "🧠 Brain & Sleep", "유산균_비타민": "💊 Vitamins", "위건강_마누카꿀": "🍯 Manuka Honey", "뷰티": "✨ Beauty", "반려동물_건강": "🐶 Pet Health", "기타_라이프스타일": "🛏️ Lifestyle" }
    }
}
UI_TEXT["CN"] = UI_TEXT["GB"].copy()
UI_TEXT["CN"].update({
    "greeting": "您好！我是AGH的智能助手 **Bio**。随时问我吧！💚", "ai_lang_cmd": "(重要：请将所有回答完全翻译成中文。)",
    "tab1": "💬 AI 智能咨询", "tab2": "📦 韩国直邮指南", "tab3": "🗺️ 悉尼旅游提示", "tab4": "🛒 购物车与退税", "tab5": "📱 门店动态",
    "add_to_cart": "🛒 加入购物车", "filter_title": "🎯 智能筛选:", "cart_title": "购物车 & TRS 退税计算器", "cart_empty": "购物车是空的，请从目录中添加！",
    "total_price": "预计总计: ${total}", "trs_success": "🎉 满 $300！您可在机场退税约 **${trs}**。", "trs_short": "💡 再买 ${short} 即可在机场享受9%退税！",
    "tips_title": "🇦🇺 悉尼旅游 & 退税提示", "tips_content": "✔️ **提前下载TRS App:** 去机场前填好信息可走快速通道哦！"
})
UI_TEXT["JP"] = UI_TEXT["GB"].copy()
UI_TEXT["JP"].update({
    "greeting": "こんにちは！AGHのスマートアシスタント、**Bio**です。何でもお尋ねください！💚", "ai_lang_cmd": "(重要：すべての回答を日本語に翻訳してください。)",
    "tab1": "💬 AI 相談", "tab2": "📦 配送ガイド", "tab3": "🗺️ シドニー旅行のヒント", "tab4": "🛒 カート & 免税計算", "tab5": "📱 店舗ニュース",
    "add_to_cart": "🛒 カートに追加", "filter_title": "🎯 スマートフィルター:", "cart_title": "カート & 免税計算機", "cart_empty": "カートは空です。カタログから追加してください！",
    "total_price": "予想合計: ${total}", "trs_success": "🎉 $300達成！空港で約 **${trs}** の払い戻しが受けられます。", "trs_short": "💡 あと ${short} で空港での9%免税対象になります！",
    "tips_title": "🇦🇺 シドニー旅行 & 免税のヒント", "tips_content": "✔️ **TRSアプリをダウンロード:** 空港に向かう前に情報を入力しておくと専用レーンが使えます！"
})

# 5. API 설정 (2026년 gemini-3.6-flash)
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- 6. 상태 관리 (장바구니 추가) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "selected_category" not in st.session_state: st.session_state.selected_category = None
if "chat_query" not in st.session_state: st.session_state.chat_query = None
if "chat_img" not in st.session_state: st.session_state.chat_img = None
if "cart" not in st.session_state: st.session_state.cart = {} # 장바구니 딕셔너리 {상품명: 수량}

if "current_md_picks" not in st.session_state:
    st.session_state.current_md_picks = random.sample(["마누카꿀 MGO 850+", "초록입홍합 21000", "리트리플 폴리코사놀", "리버케어 간영양제"], 2)

def set_category(cat_name): st.session_state.selected_category = cat_name
def trigger_ai_consultation(query, img_path=None):
    st.session_state.chat_query, st.session_state.chat_img, st.session_state.selected_category = query, img_path, None
def add_to_cart(p_name):
    st.session_state.cart[p_name] = st.session_state.cart.get(p_name, 0) + 1
    st.toast(f"🛒 '{p_name}' 담기 완료!")

# --- 7. JSON 데이터 로더 ---
@st.cache_data
def load_product_data():
    categories, flat = {}, []
    if os.path.exists('products.json'):
        try:
            with open('products.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for cat_name, items in data.items():
                    cat_list = []
                    for item in items:
                        link = item.get("link", "")
                        ext_id = re.search(r'document_srl=(\d+)', link).group(1) if re.search(r'document_srl=(\d+)', link) else "default"
                        item["image_file"] = f"{ext_id}.jpg"
                        cat_list.append(item); flat.append(item)
                    categories[cat_name] = cat_list
        except: pass
    return categories, flat

categories_db, products_db = load_product_data()

async def generate_audio(text, lang_choice):
    voice = {'GB': 'en-US-AriaNeural', 'CN': 'zh-CN-XiaoxiaoNeural', 'JP': 'ja-JP-NanamiNeural'}.get(lang_choice, 'ko-KR-SunHiNeural')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        await edge_tts.Communicate(text, voice).save(fp.name)
        return fp.name

def autoplay_audio(text, lang_choice):
    try:
        audio_file = asyncio.run(generate_audio(text, lang_choice))
        with open(audio_file, "rb") as f:
            st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{base64.b64encode(f.read()).decode()}" type="audio/mp3"></audio>', unsafe_allow_html=True)
        os.remove(audio_file)
    except: pass 

# ==========================================
# 🧹 [사이드바 구성]
# ==========================================
with st.sidebar:
    if logo_img_src: st.markdown(f'<img src="{logo_img_src}" style="width:100%; margin-bottom:10px;">', unsafe_allow_html=True)
    lang_code = st.radio("🌐 언어 (Language)", ["KR 한국어", "GB English", "CN 中文", "JP 日本語"], horizontal=True)[:2]
    t = UI_TEXT[lang_code]
    
    col_a, col_e = st.columns(2)
    audio_on, elderly_mode = col_a.toggle("🔊 Sound", False), col_e.toggle(t["elderly_mode"], False)
    if elderly_mode: st.markdown('<style>html, body, p, span, button { font-size: 1.25rem !important; }</style>', unsafe_allow_html=True)

    st.markdown(f'<div style="background: #005A32; color: white; padding: 10px; border-radius: 10px; text-align: center; font-weight: bold;">{t["md_recommend"]}</div>', unsafe_allow_html=True)
    for p in st.session_state.current_md_picks:
        t_name, _ = get_translated_product(p, "", lang_code)
        st.button(f"✨ {t_name}", on_click=trigger_ai_consultation, args=(t["prod_detail_prompt"].replace("{product}", p), None), use_container_width=True)

    st.markdown(f"### {t['top5']}")
    for idx, p in enumerate(["마누카꿀 MGO 850+", "초록입홍합 21000", "유칼립투스 프로폴리스", "아이젠 눈건강", "알티지 오메가3"]):
        t_name, _ = get_translated_product(p, "", lang_code)
        st.button(f"{['🥇','🥈','🥉','🏅','🏅'][idx]} {t_name}", on_click=trigger_ai_consultation, args=(t["prod_recommend_prompt"].replace("{product}", p), None), use_container_width=True)

    st.markdown(f"### {t['catalog']}")
    grid_cols = st.columns(2)
    for idx, cat_name in enumerate(categories_db.keys()):
        grid_cols[idx % 2].button(t["categories"].get(cat_name, f"📌 {cat_name[:6]}"), on_click=set_category, args=(cat_name,), use_container_width=True)

    model = genai.GenerativeModel(model_name='gemini-3.6-flash', system_instruction=f"호주 건강식품 매장 AI '바이오'야. 절대 HTML 태그 쓰지 마. 마크다운만 써. {t['ai_lang_cmd']}")

# ==========================================
# 📺 [메인 화면 탭 구성 (새 기능들 추가)]
# ==========================================
st.title(t["title"])
tab1, tab2, tab3, tab4, tab5 = st.tabs([t["tab1"], t["tab2"], t["tab3"], t["tab4"], t["tab5"]])

# ----------------- [탭 1: AI 챗봇 & 스마트 필터 카탈로그] -----------------
with tab1:
    if st.session_state.selected_category:
        st.markdown(f"### {t['categories'].get(st.session_state.selected_category, st.session_state.selected_category)}")
        
        # 🌱 성분 스마트 필터 UI
        st.markdown(f"**{t['filter_title']}**")
        f_col1, f_col2, f_col3 = st.columns(3)
        fil_veg = f_col1.checkbox(t["f_vegan"])
        fil_preg = f_col2.checkbox(t["f_preg"])
        fil_glut = f_col3.checkbox(t["f_gluten"])
        st.divider()

        target_products = categories_db.get(st.session_state.selected_category, [])
        cols = st.columns(3)
        drawn = 0
        for prod in target_products:
            p_name = prod.get("name", "No Name")
            p_img, p_eff = prod.get("image_file", ""), prod.get("efficacy", "")
            
            t_name, t_eff = get_translated_product(p_name, p_eff, lang_code)
            price, is_vegan, is_preg, is_gluten = get_mock_data(p_name)
            
            # 필터 로직 적용
            if (fil_veg and not is_vegan) or (fil_preg and not is_preg) or (fil_glut and not is_gluten):
                continue
            
            with cols[drawn % 3]:
                with st.container(border=True):
                    img_path = f"images/{p_img}" if os.path.exists(f"images/{p_img}") else None
                    if img_path: st.image(img_path, use_container_width=True)
                    
                    st.markdown(f'<span class="product-name">{t_name}</span>', unsafe_allow_html=True)
                    
                    # 태그 표시
                    tag_html = ""
                    if is_vegan: tag_html += f'<span class="tag-pill tag-vegan">{t["f_vegan"]}</span>'
                    if is_preg: tag_html += f'<span class="tag-pill tag-preg">{t["f_preg"]}</span>'
                    if is_gluten: tag_html += f'<span class="tag-pill tag-gluten">{t["f_gluten"]}</span>'
                    st.markdown(tag_html, unsafe_allow_html=True)
                    
                    st.caption(f"{t_eff[:50]}...")
                    st.markdown(f"**Est. Price: ${price}**")
                    
                    b_col1, b_col2 = st.columns(2)
                    b_col1.button(t["ai_listen_btn"], key=f"ai_{p_name}", on_click=trigger_ai_consultation, args=(t["prod_detail_prompt"].replace("{product}", p_name), img_path), use_container_width=True)
                    b_col2.button(t["add_to_cart"], key=f"cart_{p_name}", on_click=add_to_cart, args=(p_name,), use_container_width=True)
            drawn += 1

        st.markdown("<br>", unsafe_allow_html=True)
        st.button(t["close_btn"], on_click=set_category, args=(None,), use_container_width=True)
        st.divider()

    st.markdown(t["greeting"])
    if st.button(t["reset_chat"]): st.session_state.messages, st.session_state.cart = [], {}; st.rerun()

    st.markdown(f"**{t['quick_search']}**")
    h_col1, h_col2, h_col3 = st.columns(3)
    if h_col1.button(t["theme1_btn"], use_container_width=True): trigger_ai_consultation(t["theme1_prompt"])
    if h_col2.button(t["theme2_btn"], use_container_width=True): trigger_ai_consultation(t["theme2_prompt"])
    if h_col3.button(t["theme3_btn"], use_container_width=True): trigger_ai_consultation(t["theme3_prompt"])

    st.markdown("<br>", unsafe_allow_html=True)
    prompt = st.chat_input(t["chat_placeholder"])
    query = st.session_state.chat_query or prompt
    img_to_show = st.session_state.chat_img if st.session_state.chat_query else None
    
    if st.session_state.chat_query: st.session_state.chat_query, st.session_state.chat_img = None, None

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image"): st.image(msg["image"], width=300)
            st.markdown(re.sub(r'```(html)?\n?', '', msg["content"].replace(t["ai_lang_cmd"], "")), unsafe_allow_html=True)

    if query:
        injected = f"{query} \n\n{t['ai_lang_cmd']}"
        st.session_state.messages.append({"role": "user", "content": injected})
        with st.chat_message("user"): st.markdown(query)
        
        hist = [{"role": "model" if m["role"]=="assistant" else "user", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
        with st.chat_message("assistant"):
            if img_to_show: st.image(img_to_show, width=300)
            with st.spinner("🤖 AI..."):
                try:
                    res = re.sub(r'```(html)?\n?', '', model.start_chat(history=hist).send_message(injected).text)
                    st.markdown(res, unsafe_allow_html=True)
                    if audio_on: autoplay_audio(res, lang_code)
                    ast_msg = {"role": "assistant", "content": res}
                    if img_to_show: ast_msg["image"] = img_to_show
                    st.session_state.messages.append(ast_msg)
                except: st.error("⚠️ Error")

# ----------------- [탭 2: 한국 택배 안내] -----------------
with tab2:
    st.header("📦 Shipping")
    st.markdown(t.get("ship_desc", ""), unsafe_allow_html=True)

# ----------------- [탭 3: 여행 꿀팁 (새 기능)] -----------------
with tab3:
    st.header(t["tips_title"])
    st.info(t["tips_content"])

# ----------------- [탭 4: 장바구니 & TRS 계산기 (새 기능)] -----------------
with tab4:
    st.header(t["cart_title"])
    if not st.session_state.cart:
        st.warning(t["cart_empty"])
    else:
        total_sum = 0
        for p, qty in st.session_state.cart.items():
            t_name, _ = get_translated_product(p, "", lang_code)
            price, _, _, _ = get_mock_data(p)
            st.markdown(f"- **{t_name}** x {qty} = ${price * qty}")
            total_sum += (price * qty)
        
        st.divider()
        st.subheader(t["total_price"].replace("{total}", str(total_sum)))
        
        if total_sum >= 300:
            refund = round(total_sum / 11, 2)
            st.success(t["trs_success"].replace("{trs}", str(refund)))
        else:
            shortfall = 300 - total_sum
            st.error(t["trs_short"].replace("{short}", str(shortfall)))
        
        if st.button("🗑️ Clear Cart"): st.session_state.cart = {}; st.rerun()

# ----------------- [탭 5: 릴스 전용관] -----------------
with tab5:
    st.header("📸 Reels")
    mp4s = [f for f in os.listdir(".") if f.endswith(".mp4")]
    if mp4s:
        cols = st.columns(3)
        for i, f in enumerate(mp4s): cols[i%3].video(f)
