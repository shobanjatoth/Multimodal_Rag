













# import time

# import requests
# import streamlit as st

# from api_client import api_client
# from config import config


# # -----------------------------------------------------------------------------
# # Page setup and session state
# # -----------------------------------------------------------------------------
# st.set_page_config(
#     page_title=config.PAGE_TITLE,
#     page_icon=config.PAGE_ICON,
#     layout="wide",
# )

# if "messages" not in st.session_state:
#     st.session_state.messages = []
# if "session_id" not in st.session_state:
#     st.session_state.session_id = None
# if "backend_reachable" not in st.session_state:
#     st.session_state.backend_reachable = False
# if "doc_list" not in st.session_state:
#     st.session_state.doc_list = []
# if "show_sources" not in st.session_state:
#     st.session_state.show_sources = True
# if "generating" not in st.session_state:
#     st.session_state.generating = False


# # -----------------------------------------------------------------------------
# # Helpers
# # -----------------------------------------------------------------------------
# def check_backend() -> bool:
#     """Return True only when the backend health endpoint responds successfully."""
#     health_url = config.API_BASE_url.replace("/api/v1", "/health")
#     try:
#         response = requests.get(health_url, timeout=3)
#         response.raise_for_status()
#         return True
#     except requests.RequestException:
#         return False


# def refresh_documents() -> bool:
#     """Refresh the document list from the backend; return whether it succeeded."""
#     try:
#         response = requests.get(
#             f"{config.API_BASE_url}/docs/documents",
#             timeout=10,
#         )
#         response.raise_for_status()
#         payload = response.json()
#         st.session_state.doc_list = payload.get("documents", [])
#         return True
#     except (requests.RequestException, ValueError) as exc:
#         st.warning(f"Could not load the document list: {exc}")
#         return False


# def delete_request(url: str, *, params: dict | None = None) -> None:
#     """Perform a delete request and raise an error for unsuccessful responses."""
#     response = requests.delete(url, params=params, timeout=15)
#     response.raise_for_status()


# # Check backend once per Streamlit session, and fetch documents on first load.
# if not st.session_state.get("backend_checked", False):
#     st.session_state.backend_reachable = check_backend()
#     st.session_state.backend_checked = True

# if not st.session_state.get("documents_loaded", False):
#     if st.session_state.backend_reachable:
#         refresh_documents()
#     st.session_state.documents_loaded = True


# # -----------------------------------------------------------------------------
# # Sidebar
# # -----------------------------------------------------------------------------
# with st.sidebar:
#     st.title("RAG Pipeline")

#     if st.button("Refresh Documents", use_container_width=True):
#         if refresh_documents():
#             st.toast("Document list refreshed")

#     st.markdown("### Ingest Documents")
#     existing_categories = {
#         str(doc.get("category") or "Uncategorized")
#         for doc in st.session_state.doc_list
#     }
#     existing_categories.update(
#         {"Uncategorized", "Legal", "Medical", "Financial", "Research"}
#     )
#     sorted_categories = sorted(existing_categories)

#     ingest_mode = st.radio(
#         "Category mode",
#         ["Existing", "New"],
#         horizontal=True,
#     )
#     if ingest_mode == "Existing":
#         target_category = st.selectbox("Select category", sorted_categories)
#     else:
#         target_category = st.text_input("New category", value="Financial")

#     uploaded_files = st.file_uploader(
#         "Choose files to upload",
#         accept_multiple_files=True,
#     )

#     if uploaded_files and st.button(
#         f"Upload to '{target_category}'",
#         use_container_width=True,
#     ):
#         if not target_category.strip():
#             st.error("Please enter a category name.")
#         else:
#             progress_bar = st.progress(0)
#             succeeded = 0
#             failed = 0

#             for index, file_obj in enumerate(uploaded_files):
#                 result = api_client.ingest_file(
#                     file_obj,
#                     category=target_category.strip(),
#                 )
#                 if result.get("error"):
#                     failed += 1
#                     st.error(f"Failed to upload {file_obj.name}: {result['error']}")
#                 else:
#                     succeeded += 1
#                     st.toast(f"Uploaded {file_obj.name}")
#                 progress_bar.progress((index + 1) / len(uploaded_files))

#             st.info(f"Upload complete: {succeeded} succeeded, {failed} failed.")
#             refresh_documents()
#             time.sleep(0.5)
#             st.rerun()

#     st.markdown("### Knowledge Base")
#     selected_docs = []
#     docs_by_category = {}
#     for document in st.session_state.doc_list:
#         category = document.get("category") or "Uncategorized"
#         docs_by_category.setdefault(category, []).append(document)

#     if not docs_by_category:
#         st.caption("No documents found. Upload a document or refresh the list.")
#     else:
#         for category in sorted(docs_by_category):
#             documents = docs_by_category[category]
#             with st.expander(f"{category} ({len(documents)})", expanded=False):
#                 select_all = st.checkbox(
#                     "Select all in category",
#                     key=f"select_all_{category}",
#                 )
#                 if select_all:
#                     selected_docs.extend(
#                         doc.get("filename", "") for doc in documents
#                         if doc.get("filename")
#                     )

#                 if st.button(
#                     f"Delete category '{category}'",
#                     key=f"delete_category_{category}",
#                     use_container_width=True,
#                 ):
#                     try:
#                         delete_request(
#                             f"{config.API_BASE_url}/docs/category",
#                             params={"category": category},
#                         )
#                         st.toast(f"Deleted category {category}")
#                         refresh_documents()
#                         st.rerun()
#                     except requests.RequestException as exc:
#                         st.error(f"Could not delete category: {exc}")

#                 for document in documents:
#                     filename = document.get("filename", "Unknown")
#                     if st.checkbox(
#                         filename,
#                         key=f"select_doc_{category}_{filename}",
#                     ) and filename not in selected_docs:
#                         selected_docs.append(filename)

#     selected_docs = sorted(set(selected_docs))
#     if selected_docs:
#         st.caption(f"Selected documents: {len(selected_docs)}")
#         if st.button("Delete selected", use_container_width=True):
#             deleted = []
#             failures = []
#             for filename in selected_docs:
#                 try:
#                     delete_request(
#                         f"{config.API_BASE_url}/docs/delete",
#                         params={"filename": filename},
#                     )
#                     deleted.append(filename)
#                 except requests.RequestException as exc:
#                     failures.append(f"{filename}: {exc}")

#             if deleted:
#                 st.success(f"Deleted {len(deleted)} document(s).")
#             for failure in failures:
#                 st.error(f"Could not delete {failure}")
#             refresh_documents()
#             st.rerun()

#     st.markdown("---")
#     with st.expander("Advanced Settings"):
#         # Keep the selected model aligned with the backend's configured Groq model.
#         model_name = st.selectbox(
#             "Model",
#             ["openai/gpt-oss-120b"],
#             index=0,
#         )
#         temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
#         top_k = st.slider("Top-K documents", 1, 10, 3)
#         use_reranker = st.checkbox("Enable reranking", value=True)
#         citation_mode = st.checkbox("Show citations", value=True)
#         st.session_state.show_sources = citation_mode

#     col_new, col_clear = st.columns(2)
#     with col_new:
#         if st.button("New Chat", use_container_width=True):
#             st.session_state.messages = []
#             st.session_state.session_id = None
#             st.rerun()
#     with col_clear:
#         if st.button("Clear History", use_container_width=True):
#             st.session_state.messages = []
#             st.session_state.session_id = None
#             st.rerun()


# # -----------------------------------------------------------------------------
# # Main chat interface
# # -----------------------------------------------------------------------------
# st.title(f"{config.PAGE_ICON} {config.PAGE_TITLE}")

# if not st.session_state.backend_reachable:
#     st.error("Backend API is not reachable. Start the FastAPI server and refresh the page.")

# if not st.session_state.messages:
#     st.markdown(
#         """
#         ### Welcome to the Multimodal RAG Demo

#         Upload your documents from the sidebar, then ask questions about their contents.
#         Supported formats depend on the ingestion endpoint and may include PDFs, images,
#         audio, and video.
#         """
#     )

# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# input_disabled = st.session_state.generating or not st.session_state.backend_reachable
# prompt = st.chat_input("Ask about your documents...", disabled=input_disabled)

# if prompt:
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         message_placeholder = st.empty()
#         full_response = ""
#         st.session_state.generating = True

#         try:
#             options = {
#                 "model": model_name,
#                 "temperature": temperature,
#                 "top_k": top_k,
#                 "use_reranker": use_reranker,
#                 "citation_mode": citation_mode,
#                 "filters": {"source_filename": selected_docs} if selected_docs else None,
#             }

#             for packet in api_client.chat_stream(
#                 prompt,
#                 st.session_state.session_id,
#                 options=options,
#             ):
#                 if packet.get("error"):
#                     error_message = packet["error"]
#                     st.error(f"Backend error: {error_message}")
#                     if full_response:
#                         message_placeholder.markdown(full_response)
#                     else:
#                         message_placeholder.markdown("The response could not be generated.")
#                     break

#                 if packet.get("session_id"):
#                     if not st.session_state.session_id:
#                         st.session_state.session_id = packet["session_id"]
#                     continue

#                 if "sources" in packet and st.session_state.show_sources:
#                     sources = packet.get("sources") or []
#                     with st.expander("Retrieved Sources", expanded=False):
#                         if not sources:
#                             st.info("No relevant documents found.")
#                         for source in sources:
#                             score = source.get("score")
#                             score_text = f"{score:.2f}" if isinstance(score, (int, float)) else "N/A"
#                             st.markdown(
#                                 f"- **{source.get('source_filename', 'Document')}** "
#                                 f"(Page {source.get('page_number', '-')}) — Score: {score_text}"
#                             )
#                     continue

#                 content = packet.get("content")
#                 if content:
#                     full_response += content
#                     message_placeholder.markdown(full_response + "▌")

#             if full_response:
#                 message_placeholder.markdown(full_response)
#                 st.session_state.messages.append(
#                     {"role": "assistant", "content": full_response}
#                 )
#         except Exception as exc:
#             st.error(f"Application error: {exc}")
#             if full_response:
#                 message_placeholder.markdown(full_response)
#         finally:
#             st.session_state.generating = False














"""
Enterprise Multimodal RAG — interactive Streamlit frontend.
Uses the existing config.py and api_client.py interfaces.
"""
import time
from typing import Any

import requests
import streamlit as st

from api_client import api_client
from config import config


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title=getattr(config, "PAGE_TITLE", "Enterprise Multimodal RAG"),
    page_icon=getattr(config, "PAGE_ICON", "🤖"),
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --rag-accent: #5b6cff; }
    .stApp { background: #f6f8fc; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10182b 0%, #17233b 100%);
    }
    [data-testid="stSidebar"] * { color: #eef2ff; }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        color: #172033 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="radio"] label { color: #eef2ff; }
    .hero {
        padding: 1.45rem 1.6rem;
        border-radius: 22px;
        color: white;
        background: linear-gradient(115deg, #202d52, #4b5ed7 68%, #7784ff);
        margin-bottom: 1.1rem;
        box-shadow: 0 12px 30px rgba(39, 55, 120, .14);
    }
    .hero h1 { color: white; margin: 0; font-size: 2rem; }
    .hero p { color: #e3e8ff; margin: .45rem 0 0 0; }
    .metric-card {
        border: 1px solid #e5e9f3;
        background: white;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        min-height: 100px;
        box-shadow: 0 4px 14px rgba(26, 38, 75, .04);
    }
    .metric-label { color: #66708a; font-size: .84rem; }
    .metric-value { color: #1b2540; font-size: 1.6rem; font-weight: 750; margin-top: .2rem; }
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        min-height: 2.55rem;
    }
    div[data-testid="stChatMessage"] {
        border: 1px solid #e8ebf4;
        border-radius: 16px;
        padding: .35rem .8rem;
        background: white;
    }
    .small-muted { color: #75809a; font-size: .85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
DEFAULTS = {
    "messages": [],
    "session_id": None,
    "backend_reachable": False,
    "backend_checked": False,
    "doc_list": [],
    "show_sources": True,
    "generating": False,
    "documents_loaded": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def api_base() -> str:
    return str(config.API_BASE_url).rstrip("/")


def check_backend() -> bool:
    """Check the health endpoint without crashing the UI if it is unavailable."""
    health_url = api_base().replace("/api/v1", "/health")
    try:
        response = requests.get(health_url, timeout=4)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def refresh_documents(show_error: bool = True) -> bool:
    """Load document metadata from the existing documents endpoint."""
    try:
        response = requests.get(f"{api_base()}/docs/documents", timeout=12)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            documents = payload
        elif isinstance(payload, dict):
            documents = payload.get("documents", [])
        else:
            documents = []
        if not isinstance(documents, list):
            raise ValueError("The documents endpoint did not return a document list.")
        st.session_state.doc_list = documents
        st.session_state.documents_loaded = True
        return True
    except (requests.RequestException, ValueError) as exc:
        if show_error:
            st.warning(f"Could not load the document list: {exc}")
        return False


def delete_request(url: str, params: dict[str, Any] | None = None) -> None:
    response = requests.delete(url, params=params, timeout=15)
    response.raise_for_status()


def get_filename(document: dict[str, Any]) -> str:
    return str(document.get("filename") or document.get("source_filename") or "Unknown")


def get_category(document: dict[str, Any]) -> str:
    return str(document.get("category") or "Uncategorized")


# Initial health check and document fetch
if not st.session_state.backend_checked:
    st.session_state.backend_reachable = check_backend()
    st.session_state.backend_checked = True
if st.session_state.backend_reachable and not st.session_state.documents_loaded:
    refresh_documents(show_error=False)


# ---------------------------------------------------------------------------
# Sidebar: connection, upload, and knowledge-base controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ◈ RAG Workspace")
    st.caption("Enterprise document assistant")

    if st.session_state.backend_reachable:
        st.success("API connected")
    else:
        st.error("API disconnected")
        if st.button("Retry connection", use_container_width=True):
            st.session_state.backend_reachable = check_backend()
            st.session_state.backend_checked = True
            if st.session_state.backend_reachable:
                refresh_documents(show_error=False)
            st.rerun()

    st.markdown("---")
    st.markdown("### Add documents")
    categories = sorted({get_category(d) for d in st.session_state.doc_list})
    categories = sorted(set(categories + ["Financial", "Research", "Legal", "Medical", "Uncategorized"]))
    category_mode = st.radio("Category", ["Existing category", "Create new"], horizontal=True)
    if category_mode == "Existing category":
        target_category = st.selectbox("Save to", categories, index=categories.index("Financial") if "Financial" in categories else 0)
    else:
        target_category = st.text_input("New category name", value="Financial")

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        help="Select one or more files supported by your backend ingestion endpoint.",
    )
    if st.button(
        f"Upload {len(uploaded_files)} file(s)" if uploaded_files else "Choose files to upload",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files or not st.session_state.backend_reachable or not target_category.strip(),
    ):
        progress = st.progress(0, text="Preparing uploads…")
        success_count, failure_count = 0, 0
        for i, file_obj in enumerate(uploaded_files):
            try:
                file_obj.seek(0)
                result = api_client.ingest_file(file_obj, category=target_category.strip())
                if not isinstance(result, dict) or result.get("error"):
                    failure_count += 1
                    st.error(f"{file_obj.name}: {result.get('error', 'Unexpected response') if isinstance(result, dict) else 'Unexpected response'}")
                else:
                    success_count += 1
            except Exception as exc:
                failure_count += 1
                st.error(f"{file_obj.name}: {exc}")
            progress.progress((i + 1) / len(uploaded_files), text=f"Processed {i + 1} of {len(uploaded_files)}")
        if refresh_documents(show_error=False):
            st.toast("Document list updated")
        st.info(f"Upload finished · {success_count} succeeded · {failure_count} failed")
        time.sleep(0.3)
        st.rerun()

    st.markdown("---")
    st.markdown("### Knowledge base")
    top_left, top_right = st.columns([1, 1])
    with top_left:
        st.caption(f"{len(st.session_state.doc_list)} listed")
    with top_right:
        if st.button("↻ Refresh", use_container_width=True):
            if refresh_documents():
                st.toast("Document list refreshed")

    search_docs = st.text_input("Search filenames", placeholder="Type to filter…")
    all_docs = st.session_state.doc_list
    if search_docs.strip():
        all_docs = [d for d in all_docs if search_docs.lower() in get_filename(d).lower()]

    grouped: dict[str, list[dict[str, Any]]] = {}
    for doc in all_docs:
        grouped.setdefault(get_category(doc), []).append(doc)

    selected_docs: list[str] = []
    if not grouped:
        st.caption("No matching documents. Upload a file or refresh the list.")
    else:
        for category in sorted(grouped):
            docs = grouped[category]
            with st.expander(f"{category} · {len(docs)}", expanded=False):
                select_all = st.checkbox("Select all", key=f"all_{category}")
                if select_all:
                    selected_docs.extend(get_filename(d) for d in docs if get_filename(d) != "Unknown")
                for doc in docs:
                    filename = get_filename(doc)
                    if filename == "Unknown":
                        st.caption("A document without a filename was returned by the API.")
                        continue
                    checked = st.checkbox(filename, key=f"doc_{category}_{filename}")
                    if checked and filename not in selected_docs:
                        selected_docs.append(filename)
                if st.button("Delete this category", key=f"delete_cat_{category}", use_container_width=True):
                    try:
                        delete_request(f"{api_base()}/docs/category", {"category": category})
                        st.toast(f"Deleted category: {category}")
                        refresh_documents(show_error=False)
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(f"Category delete failed: {exc}")

    selected_docs = sorted(set(selected_docs))
    if selected_docs:
        st.caption(f"{len(selected_docs)} document(s) selected")
        if st.button("Delete selected documents", use_container_width=True):
            failures = []
            for filename in selected_docs:
                try:
                    delete_request(f"{api_base()}/docs/delete", {"filename": filename})
                except requests.RequestException as exc:
                    failures.append(f"{filename}: {exc}")
            if failures:
                for failure in failures:
                    st.error(failure)
            else:
                st.toast("Selected documents deleted")
            refresh_documents(show_error=False)
            st.rerun()

    st.markdown("---")
    with st.expander("Chat settings", expanded=False):
        model_name = st.selectbox("Groq model", ["openai/gpt-oss-120b"], index=0)
        temperature = st.slider("Creativity", 0.0, 1.0, 0.2, 0.1)
        top_k = st.slider("Retrieved chunks (Top-K)", 1, 10, 3)
        use_reranker = st.toggle("Use reranker", value=True)
        citation_mode = st.toggle("Show source citations", value=True)
        st.session_state.show_sources = citation_mode

    left, right = st.columns(2)
    with left:
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
    with right:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()


# ---------------------------------------------------------------------------
# Main workspace
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
      <h1>Enterprise Multimodal RAG</h1>
      <p>Search your uploaded knowledge base and ask questions with grounded answers.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

doc_count = len(st.session_state.doc_list)
category_count = len({get_category(d) for d in st.session_state.doc_list})
chat_count = len([m for m in st.session_state.messages if m.get("role") == "user"])
m1, m2, m3, m4 = st.columns(4)
for col, label, value in [
    (m1, "Documents listed", doc_count),
    (m2, "Categories", category_count),
    (m3, "Questions this chat", chat_count),
    (m4, "API status", "Online" if st.session_state.backend_reachable else "Offline"),
]:
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")
chat_tab, guide_tab = st.tabs(["💬 Chat with documents", "ⓘ How to use"])

with chat_tab:
    if not st.session_state.backend_reachable:
        st.error("The API is unreachable. Start FastAPI, then use **Retry connection** in the sidebar.")
    elif doc_count == 0:
        st.info("Your document list is empty or could not be loaded. Upload a PDF or refresh the knowledge base. Chat may not have source material until ingestion succeeds.")

    if not st.session_state.messages:
        st.markdown("#### Start with a question")
        suggestions = [
            "Summarize the uploaded filing.",
            "What was the company's total revenue in 2025?",
            "What risks does the company describe?",
        ]
        suggestion_cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            with suggestion_cols[i]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.pending_prompt = suggestion
                    st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources") and st.session_state.show_sources:
                with st.expander("Sources used", expanded=False):
                    for source in message["sources"]:
                        st.markdown(
                            f"- **{source.get('source_filename', 'Document')}** · "
                            f"Page {source.get('page_number', '—')} · "
                            f"Score: {source.get('score', 'N/A')}"
                        )

    pending_prompt = st.session_state.pop("pending_prompt", None)
    prompt = st.chat_input(
        "Ask a question about your documents…",
        disabled=st.session_state.generating or not st.session_state.backend_reachable,
    )
    prompt = prompt or pending_prompt

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            response_text = ""
            source_items: list[dict[str, Any]] = []
            st.session_state.generating = True
            try:
                options = {
                    "model": model_name,
                    "temperature": temperature,
                    "top_k": top_k,
                    "use_reranker": use_reranker,
                    "citation_mode": citation_mode,
                    "filters": {"source_filename": selected_docs} if selected_docs else None,
                }
                for packet in api_client.chat_stream(prompt, st.session_state.session_id, options=options):
                    if not isinstance(packet, dict):
                        continue
                    if packet.get("error"):
                        st.error(f"Backend error: {packet['error']}")
                        break
                    if packet.get("session_id"):
                        st.session_state.session_id = packet["session_id"]
                        continue
                    if "sources" in packet:
                        source_items = packet.get("sources") or []
                        continue
                    chunk = packet.get("content")
                    if chunk:
                        response_text += str(chunk)
                        placeholder.markdown(response_text + " ▌")
                placeholder.markdown(response_text or "I couldn't generate a response. Check the backend logs and try again.")
                if response_text:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response_text, "sources": source_items}
                    )
                if source_items and st.session_state.show_sources:
                    with st.expander("Retrieved sources", expanded=False):
                        for source in source_items:
                            score = source.get("score")
                            score_text = f"{score:.3f}" if isinstance(score, (int, float)) else "N/A"
                            st.markdown(
                                f"- **{source.get('source_filename', 'Document')}** · "
                                f"Page {source.get('page_number', '—')} · Score: {score_text}"
                            )
            except Exception as exc:
                st.error(f"Chat request failed: {exc}")
            finally:
                st.session_state.generating = False

with guide_tab:
    st.markdown("### Quick start")
    st.markdown(
        """
        1. **Connect the backend** — start your FastAPI server and confirm the API status is Online.
        2. **Upload documents** — choose a category in the sidebar, select your PDF or other supported files, and upload.
        3. **Refresh the knowledge base** — confirm your documents appear under Knowledge base.
        4. **Ask grounded questions** — use a suggested question or type your own in the chat box.
        5. **Inspect citations** — expand the source panel to see which documents and pages were retrieved.

        **Note:** A successful upload response does not always guarantee that document chunks were indexed. If the knowledge base stays empty, inspect the FastAPI ingestion logs and Qdrant point count.
        """
    )
    st.markdown("### Current chat")
    st.write(f"Session ID: `{st.session_state.session_id or 'Not created yet'}`")
    st.write(f"Messages in this chat: {len(st.session_state.messages)}")
