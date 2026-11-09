import hashlib
import html
import os
import uuid
from pathlib import Path

from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
from data_loader import embed_texts, load_and_chunk_pdf
from vector_db import QdrantStorage

load_dotenv()
try:
    for secret_name, secret_value in dict(st.secrets).items():
        if isinstance(secret_value, str):
            os.environ.setdefault(secret_name, secret_value)
except Exception:
    pass

st.set_page_config(page_title="Orbit | Document AI", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #edf3ff;
        --muted: #9caec8;
        --cyan: #66e8dc;
        --violet: #a68aff;
        --surface: rgba(18, 26, 49, .78);
    }
    html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
    .stApp {
        color: var(--ink);
        background:
            radial-gradient(ellipse at 14% 5%, rgba(53, 88, 173, .25), transparent 35%),
            radial-gradient(ellipse at 91% 24%, rgba(90, 54, 158, .19), transparent 31%),
            linear-gradient(145deg, #080d1b 0%, #0b1122 48%, #101329 100%);
    }
    .stApp::before {
        content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 0;
        opacity: .18;
        background-image: radial-gradient(rgba(172, 194, 255, .42) .7px, transparent .7px);
        background-size: 28px 28px;
        mask-image: linear-gradient(to bottom, black, transparent 76%);
    }
    .block-container { max-width: 1220px; padding: 2.2rem 2rem 4rem; position: relative; z-index: 1; }
    #MainMenu, footer, header { visibility: hidden; }
    h1, h2, h3, p { color: var(--ink); }
    .hero {
        position: relative; overflow: hidden; display: flex; align-items: center;
        min-height: 292px; padding: 2.5rem 3rem; margin: .4rem 0 1.8rem;
        border: 1px solid rgba(167, 190, 255, .19); border-radius: 28px;
        background: linear-gradient(115deg, rgba(24, 39, 75, .96), rgba(18, 27, 53, .91) 54%, rgba(34, 31, 72, .9));
        box-shadow: 0 28px 70px rgba(0,0,0,.36), inset 0 1px 0 rgba(255,255,255,.12), inset 0 -1px 0 rgba(116,143,222,.08);
        transform-style: preserve-3d;
    }
    .hero::before { content:''; position:absolute; inset:0; background:linear-gradient(110deg, transparent 35%, rgba(164,185,255,.045), transparent 68%); pointer-events:none; }
    .hero-copy { position:relative; z-index:2; max-width:620px; transform:translateZ(32px); }
    .eyebrow, .micro-label { font:500 11px 'DM Mono',monospace; letter-spacing:.18em; text-transform:uppercase; color:var(--cyan); }
    .eyebrow { display:flex; align-items:center; gap:10px; margin-bottom:18px; }
    .eyebrow::before { content:''; width:22px; height:1px; background:var(--cyan); box-shadow:0 0 10px var(--cyan); }
    .hero h1 { font-size:clamp(2.45rem,5vw,4.2rem); line-height:1.02; letter-spacing:-.065em; margin:0; font-weight:800; }
    .hero h1 span { color:var(--cyan); text-shadow:0 0 28px rgba(102,232,220,.22); }
    .hero p { color:#aebbd2; font-size:1rem; line-height:1.7; max-width:510px; margin:17px 0 22px; }
    .hero-badges { display:flex; gap:9px; flex-wrap:wrap; }
    .hero-badge { padding:7px 11px; border:1px solid rgba(164,190,255,.16); border-radius:999px; background:rgba(255,255,255,.045); color:#c4d0e5; font:11px 'DM Mono',monospace; }
    .hero-badge b { color:var(--cyan); font-weight:500; }

    .scene { width:300px; height:250px; margin-left:auto; margin-right:2%; position:relative; perspective:800px; transform-style:preserve-3d; }
    .doc-stack { position:absolute; width:162px; height:205px; top:17px; left:70px; transform-style:preserve-3d; transform:rotateX(56deg) rotateZ(-34deg); animation:float 6s ease-in-out infinite; }
    .sheet { position:absolute; inset:0; border-radius:12px; border:1px solid rgba(193,210,255,.54); background:linear-gradient(145deg,#f4f6ff,#cbd7f6); box-shadow:0 20px 30px rgba(0,0,0,.24); }
    .sheet:nth-child(1) { transform:translateZ(-24px) translate(21px,17px); background:linear-gradient(145deg,#7182b7,#414f83); }
    .sheet:nth-child(2) { transform:translateZ(-12px) translate(11px,9px); background:linear-gradient(145deg,#9aa9db,#6879af); }
    .sheet:nth-child(3) { transform:translateZ(0); overflow:hidden; }
    .sheet:nth-child(3)::before { content:''; position:absolute; left:20px; right:19px; top:25px; height:6px; border-radius:5px; background:#6275b4; box-shadow:0 18px 0 #b1bddf,0 36px 0 #b1bddf,0 54px 0 #b1bddf,0 72px 0 #b1bddf,0 90px 0 #d1d9ed; }
    .sheet:nth-child(3)::after { content:'RAG / 01'; position:absolute; left:20px; bottom:17px; color:#6275b4; font:10px 'DM Mono',monospace; }
    .orb { position:absolute; width:62px; height:62px; right:8px; top:17px; border-radius:50%; background:radial-gradient(circle at 30% 25%,#e0fffc 0,#65e7dc 13%,#38889e 41%,#6241a3 70%,#271c59 100%); box-shadow:inset -10px -12px 22px rgba(0,0,0,.45),inset 5px 6px 10px rgba(255,255,255,.35),0 0 45px rgba(102,232,220,.25); transform:translateZ(74px); animation:orb 5s ease-in-out infinite; }
    .orb::after { content:''; position:absolute; inset:-12px -18px; border:1px solid rgba(116,235,228,.55); border-radius:50%; transform:rotateX(65deg) rotateZ(-26deg); }
    @keyframes float { 0%,100%{transform:rotateX(56deg) rotateZ(-34deg) translateY(0)} 50%{transform:rotateX(56deg) rotateZ(-34deg) translateY(-9px)} }
    @keyframes orb { 0%,100%{transform:translateZ(74px) translateY(0)} 50%{transform:translateZ(88px) translateY(-7px)} }

    [class*="st-key-upload_panel"], [class*="st-key-query_panel"], [class*="st-key-info_panel"], [class*="st-key-answer_panel"] {
        background:linear-gradient(145deg, rgba(25,35,63,.88), rgba(14,21,41,.92));
        border:1px solid rgba(163,184,235,.14); border-radius:23px; padding:1.45rem 1.5rem 1.55rem;
        box-shadow:0 18px 38px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08), inset 0 -1px 0 rgba(120,146,218,.08);
        transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease;
    }
    [class*="st-key-upload_panel"]:hover, [class*="st-key-query_panel"]:hover {
        transform:translateY(-3px); border-color:rgba(102,232,220,.34);
        box-shadow:0 25px 50px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.1);
    }
    .panel-heading { display:flex; align-items:center; gap:13px; margin-bottom:1.2rem; }
    .panel-icon { display:grid; place-items:center; width:42px; height:42px; border-radius:13px; color:var(--cyan); font-size:19px; background:linear-gradient(145deg,rgba(102,232,220,.16),rgba(111,128,255,.1)); border:1px solid rgba(102,232,220,.22); box-shadow:inset 0 1px rgba(255,255,255,.12),0 7px 16px rgba(0,0,0,.2); }
    .panel-heading h2 { font-size:1.12rem; letter-spacing:-.03em; margin:0; }
    .panel-heading small { display:block; color:var(--muted); font-size:.78rem; margin-top:3px; }
    .stMarkdown, label, .stCaption, [data-testid="stWidgetLabel"] { color:var(--ink); }
    [data-testid="stFileUploader"] { background:rgba(7,13,27,.43); border:1px dashed rgba(128,161,218,.4); border-radius:16px; padding:.7rem; transition:border-color .2s ease,background .2s ease; }
    [data-testid="stFileUploader"]:hover { border-color:var(--cyan); background:rgba(24,65,79,.2); }
    [data-testid="stFileUploaderDropzone"] { background:transparent; border:0; }
    [data-testid="stFileUploaderDropzone"] button { color:#d5e4ff; border:1px solid rgba(137,166,226,.34); background:linear-gradient(145deg,#24385d,#182744); border-radius:10px; }
    .stTextInput input, .stNumberInput input, textarea { color:var(--ink)!important; background:rgba(7,13,27,.72)!important; border:1px solid rgba(137,166,226,.23)!important; border-radius:12px!important; }
    .stTextInput input:focus, .stNumberInput input:focus { border-color:var(--cyan)!important; box-shadow:0 0 0 1px rgba(102,232,220,.18)!important; }
    .stButton button, [data-testid="stFormSubmitButton"] button { color:#081221; font-weight:800; border:0; border-radius:12px; padding:.65rem 1.2rem; background:linear-gradient(110deg,#72f2df,#93d8ff 65%,#c0a9ff); box-shadow:0 8px 18px rgba(74,201,195,.2),inset 0 1px rgba(255,255,255,.7); transition:transform .18s ease,box-shadow .18s ease; }
    .stButton button:hover, [data-testid="stFormSubmitButton"] button:hover { transform:translateY(-2px); box-shadow:0 12px 25px rgba(74,201,195,.28),inset 0 1px rgba(255,255,255,.8); }
    .hint { color:#90a2bf; font-size:.78rem; line-height:1.55; margin:.6rem 0 0; }
    .status-line { display:flex; align-items:center; gap:9px; color:#b8c8df; font-size:.78rem; margin-top:1.1rem; }
    .status-dot { width:7px; height:7px; border-radius:50%; background:#6de6c4; box-shadow:0 0 10px #6de6c4; }
    .step { display:flex; gap:13px; margin:1rem 0; color:#aab9d1; font-size:.83rem; line-height:1.55; }
    .step-num { flex:none; display:grid; place-items:center; width:25px; height:25px; border-radius:8px; color:var(--cyan); background:rgba(102,232,220,.1); border:1px solid rgba(102,232,220,.2); font:11px 'DM Mono',monospace; }
    .answer-card { border-radius:16px; border:1px solid rgba(102,232,220,.2); background:linear-gradient(140deg,rgba(16,50,60,.42),rgba(24,30,59,.62)); padding:1.15rem 1.25rem; margin-top:1rem; box-shadow:inset 0 1px 0 rgba(255,255,255,.07); }
    .answer-label { color:var(--cyan); font:500 10px 'DM Mono',monospace; letter-spacing:.15em; text-transform:uppercase; margin-bottom:.6rem; }
    .source-chip { display:inline-block; color:#b9c9e5; border:1px solid rgba(159,180,224,.2); background:rgba(255,255,255,.045); border-radius:999px; padding:5px 9px; margin:4px 4px 0 0; font:10px 'DM Mono',monospace; }
    [data-testid="stAlert"] { border-radius:12px; }
    @media (max-width: 760px) {
        .block-container { padding:1rem 1rem 3rem; }
        .hero { min-height:250px; padding:1.8rem 1.45rem; }
        .hero h1 { font-size:2.55rem; }
        .scene { position:absolute; right:-48px; bottom:-65px; opacity:.37; transform:scale(.8); }
        [class*="st-key-upload_panel"], [class*="st-key-query_panel"], [class*="st-key-info_panel"], [class*="st-key-answer_panel"] { padding:1.1rem; }
    }
    </style>

    <section class="hero">
      <div class="hero-copy">
        <div class="eyebrow">ORBIT · PRIVATE KNOWLEDGE ENGINE</div>
        <h1>Your documents,<br>in a <span>new dimension.</span></h1>
        <p>Bring your PDFs into focus. Ask naturally, explore the right context, and get grounded answers from your own library.</p>
        <div class="hero-badges"><span class="hero-badge"><b>01</b> &nbsp; INGEST</span><span class="hero-badge"><b>02</b> &nbsp; RETRIEVE</span><span class="hero-badge"><b>03</b> &nbsp; DISCOVER</span></div>
      </div>
      <div class="scene" aria-hidden="true"><div class="doc-stack"><div class="sheet"></div><div class="sheet"></div><div class="sheet"></div></div><div class="orb"></div></div>
    </section>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_vector_store() -> QdrantStorage:
    return QdrantStorage()


def ingest_pdf(file_name: str, pdf_bytes: bytes) -> int:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / Path(file_name).name
    file_path.write_bytes(pdf_bytes)

    chunks = load_and_chunk_pdf(str(file_path))
    vectors = embed_texts(chunks)
    source_id = file_path.name
    ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_id}:{i}")) for i in range(len(chunks))]
    payloads = [{"source": source_id, "text": chunks[i]} for i in range(len(chunks))]
    get_vector_store().upsert(ids, vectors, payloads)
    return len(chunks)


def answer_question(question: str, top_k: int) -> dict:
    query_vector = embed_texts([question])[0]
    found = get_vector_store().search(query_vector, top_k)
    if not found["contexts"]:
        return {"answer": "I couldn't find relevant text. Upload a PDF and wait for indexing to finish.", "sources": []}

    context_block = "\n\n".join(f"- {context}" for context in found["contexts"])
    response = OpenAI().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "Answer using only the provided document context. If the answer is not in the context, say so."},
            {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"},
        ],
    )
    return {"answer": response.choices[0].message.content or "No answer was returned.", "sources": found["sources"]}


upload_col, query_col = st.columns([0.92, 1.08], gap="large")

with upload_col:
    with st.container(border=True, key="upload_panel"):
        st.markdown(
            '<div class="panel-heading"><div class="panel-icon">↥</div><div><h2>Build your library</h2><small>Drop in a PDF to make it searchable</small></div></div>',
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False, label_visibility="collapsed")
        st.markdown('<p class="hint">Your file is chunked, embedded, and indexed for semantic search.</p>', unsafe_allow_html=True)
        if uploaded is not None:
            pdf_bytes = uploaded.getvalue()
            upload_digest = hashlib.sha256(pdf_bytes).hexdigest()
            if st.session_state.get("ingested_pdf_digest") != upload_digest:
                try:
                    with st.spinner("Reading, embedding, and indexing your document..."):
                        chunk_count = ingest_pdf(uploaded.name, pdf_bytes)
                    st.session_state["ingested_pdf_digest"] = upload_digest
                    st.success(f"Indexed {uploaded.name} into {chunk_count} searchable chunks.")
                except Exception as error:
                    st.error(str(error))
                    if "no credits remaining" in str(error).lower():
                        st.markdown("[OpenAI billing settings](https://platform.openai.com/settings/organization/billing/)")
            else:
                st.success(f"{uploaded.name} is ready in your library.")

    with st.container(border=True, key="info_panel"):
        st.markdown('<div class="micro-label">HOW IT WORKS</div>', unsafe_allow_html=True)
        st.markdown('<div class="step"><span class="step-num">01</span><span><b>Ground your workspace</b><br>Upload a PDF and let Orbit index its content.</span></div><div class="step"><span class="step-num">02</span><span><b>Ask in plain language</b><br>Choose how much context to retrieve.</span></div><div class="step"><span class="step-num">03</span><span><b>Explore sourced answers</b><br>Get a concise response linked to your files.</span></div><div class="status-line"><span class="status-dot"></span>STREAMLIT CLOUD READY</div>', unsafe_allow_html=True)

with query_col:
    with st.container(border=True, key="query_panel"):
        st.markdown(
            '<div class="panel-heading"><div class="panel-icon">⌕</div><div><h2>Talk to your documents</h2><small>Answers stay grounded in retrieved context</small></div></div>',
            unsafe_allow_html=True,
        )
        with st.form("rag_query_form"):
            question = st.text_input("Ask anything", placeholder="e.g. What are the key ideas in this document?")
            controls = st.columns([0.55, 1.45], vertical_alignment="bottom")
            with controls[0]:
                top_k = st.number_input("Context chunks", min_value=1, max_value=20, value=5, step=1)
            with controls[1]:
                submitted = st.form_submit_button("Explore answer  →", use_container_width=True)

        if submitted and question.strip():
            try:
                with st.spinner("Searching your library and composing an answer..."):
                    output = answer_question(question.strip(), int(top_k))
            except Exception as error:
                st.error(str(error))
                if "no credits remaining" in str(error).lower():
                    st.markdown("[OpenAI billing settings](https://platform.openai.com/settings/organization/billing/)")
            else:
                with st.container(border=True, key="answer_panel"):
                    st.markdown('<div class="answer-label">ORBIT RESPONSE</div>', unsafe_allow_html=True)
                    st.write(output.get("answer") or "No answer was returned.")
                sources = output.get("sources", [])
                if sources:
                    st.markdown('<div class="micro-label" style="margin-top:1rem">SOURCES</div>', unsafe_allow_html=True)
                    st.markdown("".join(f'<span class="source-chip">{html.escape(str(source))}</span>' for source in sources), unsafe_allow_html=True)
