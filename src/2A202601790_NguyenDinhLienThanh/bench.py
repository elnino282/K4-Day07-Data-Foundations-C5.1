from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import yaml


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PACKAGE_NAME = "src.2A202601790_NguyenDinhLienThanh"
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "k4_ecommerce"
OUTPUT_PATH = Path(__file__).with_name("bench_results.json")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

personal = importlib.import_module(PACKAGE_NAME)
Document = personal.Document
EmbeddingStore = personal.EmbeddingStore
LocalEmbedder = personal.LocalEmbedder
RecursiveChunker = personal.RecursiveChunker
compute_similarity = personal.compute_similarity


class ParagraphWindowChunker:
    """Chunk theo đoạn, giữ overlap một đoạn để tránh cắt mất ngữ cảnh bảng/chính sách."""

    def __init__(self, chunk_size: int = 650, overlap_blocks: int = 1) -> None:
        self.chunk_size = chunk_size
        self.overlap_blocks = overlap_blocks

    def chunk(self, text: str) -> list[str]:
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        chunks: list[str] = []
        start = 0
        while start < len(blocks):
            selected: list[str] = []
            length = 0
            end = start
            while end < len(blocks):
                block = blocks[end]
                projected = length + len(block) + (2 if selected else 0)
                if selected and projected > self.chunk_size:
                    break
                selected.append(block)
                length = projected
                end += 1
                if length >= self.chunk_size:
                    break

            if not selected:
                selected = [blocks[start][: self.chunk_size]]
                end = start + 1
            chunks.append("\n\n".join(selected))
            if end >= len(blocks):
                break
            start = max(start + 1, end - self.overlap_blocks)
        return chunks


TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)
STOPWORDS = {
    "bị",
    "có",
    "cho",
    "của",
    "đã",
    "được",
    "gì",
    "khi",
    "là",
    "một",
    "nào",
    "những",
    "phải",
    "sau",
    "thế",
    "thì",
    "trên",
    "trong",
    "và",
    "về",
    "với",
}


SIMILARITY_PAIRS = [
    {
        "a": "Người mua muốn trả hàng và nhận lại tiền.",
        "b": "Khách hàng yêu cầu hoàn tiền cho đơn hàng.",
        "prediction": "cao",
    },
    {
        "a": "Tiền hoàn được chuyển về thẻ đã thanh toán.",
        "b": "Khoản hoàn trả được gửi lại vào thẻ ngân hàng ban đầu.",
        "prediction": "cao",
    },
    {
        "a": "Người bán cần đăng ảnh thật của sản phẩm.",
        "b": "Người bán phải cung cấp bằng chứng vận chuyển.",
        "prediction": "thấp",
    },
    {
        "a": "Shopee chuyển tiền thanh toán cho người bán.",
        "b": "Hôm nay thời tiết có mưa không?",
        "prediction": "thấp",
    },
    {
        "a": "Người bán phải gửi bằng chứng khiếu nại trong 24 giờ.",
        "b": "Bằng chứng vận chuyển cần được cung cấp trong vòng một ngày.",
        "prediction": "cao",
    },
]


GOLDEN_SET = [
    {
        "id": 1,
        "query": (
            "Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với "
            "hàng thông thường và thực phẩm tươi sống hoặc đông lạnh?"
        ),
        "metadata_filter": {"customer_role": "buyer"},
        "expected_doc_id": "shopee-buyer-return-refund-policy",
        "evidence_terms": ["15 (mười lăm) ngày", "24 giờ"],
    },
    {
        "id": 2,
        "query": (
            "Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ "
            "được hoàn về đâu và trong bao lâu?"
        ),
        "metadata_filter": {"customer_role": "buyer"},
        "expected_doc_id": "shopee-buyer-refund-timeline",
        "evidence_terms": ["thẻ tín dụng/ghi nợ", "7 - 14 ngày làm việc"],
    },
    {
        "id": 3,
        "query": "Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào?",
        "metadata_filter": {"customer_role": "seller"},
        "expected_doc_id": "shopee-seller-listing-rules",
        "evidence_terms": ["40% diện tích toàn ảnh", "phông nền hình ảnh là tiếng Việt"],
    },
    {
        "id": 4,
        "query": (
            "Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào "
            "và những bằng chứng nào được Shopee khuyến khích?"
        ),
        "metadata_filter": {"customer_role": "seller"},
        "expected_doc_id": "shopee-seller-shipping-fulfillment-policy",
        "evidence_terms": ["video quá trình đóng gói", "trong vòng 24 giờ"],
    },
    {
        "id": 5,
        "query": (
            "Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán "
            "như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận?"
        ),
        "metadata_filter": {"customer_role": "both"},
        "expected_doc_id": "shopee-terms-of-service-vn",
        "evidence_terms": ["đã nhận được hàng", "điều chỉnh khoản"],
    },
]


def parse_document(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            loaded = yaml.safe_load(parts[1]) or {}
            if isinstance(loaded, dict):
                metadata = {str(key): value for key, value in loaded.items()}
            body = parts[2].lstrip()

    doc_id = str(metadata.get("doc_id") or path.stem)
    metadata.setdefault("doc_id", doc_id)
    metadata.setdefault("source", path.name)
    return Document(id=doc_id, content=body, metadata=metadata)


def build_store(
    embedder: LocalEmbedder,
    *,
    chunker: Any,
    collection_name: str,
    enrich_for_embedding: bool = False,
) -> tuple[EmbeddingStore, int]:
    chunks: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        document = parse_document(path)
        for index, content in enumerate(chunker.chunk(document.content)):
            metadata = dict(document.metadata)
            metadata["parent_doc_id"] = document.id
            metadata["chunk_index"] = index
            metadata["raw_content"] = content
            embedded_content = content
            if enrich_for_embedding:
                embedded_content = (
                    f"Tiêu đề tài liệu: {metadata.get('title', '')}\n"
                    f"Chủ đề: {metadata.get('category', '')}\n"
                    f"Vai trò khách hàng: {metadata.get('customer_role', '')}\n\n"
                    f"{content}"
                )
            chunks.append(
                Document(
                    id=f"{document.id}::chunk_{index}",
                    content=embedded_content,
                    metadata=metadata,
                )
            )

    store = EmbeddingStore(collection_name=collection_name, embedding_fn=embedder)
    store.add_documents(chunks)
    return store, len(chunks)


def run_similarity(embedder: LocalEmbedder) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, pair in enumerate(SIMILARITY_PAIRS, start=1):
        score = compute_similarity(embedder(pair["a"]), embedder(pair["b"]))
        results.append({"pair": index, **pair, "score": round(score, 4)})
    return results


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def expand_query_for_lexical_search(query: str) -> str:
    """Mở rộng ý định, không thêm dữ kiện/con số từ gold answer."""
    normalized = query.lower()
    expansions: list[str] = []
    if "bao lâu" in normalized or "thời hạn" in normalized:
        expansions.append("thời gian thời hạn ngày giờ ngày làm việc")
    if "hoàn về đâu" in normalized:
        expansions.append("phương thức nhận tiền hoàn tài khoản nhận tiền tiền hoàn trả được gửi qua")
    if "hình ảnh" in normalized:
        expansions.append("ảnh chụp ảnh thật hình ảnh sản phẩm")
    if "bằng chứng" in normalized:
        expansions.append("chứng minh khiếu nại video vận đơn hóa đơn")
    return " ".join([query, *expansions])


def bm25_scores(query: str, matches: list[dict[str, Any]]) -> list[float]:
    query_tokens = set(tokenize(expand_query_for_lexical_search(query)))
    documents = [tokenize(match["content"]) for match in matches]
    if not query_tokens or not documents:
        return [0.0] * len(matches)

    average_length = sum(map(len, documents)) / len(documents) or 1.0
    document_frequency = {
        token: sum(token in set(document) for document in documents)
        for token in query_tokens
    }
    scores: list[float] = []
    k1 = 1.5
    b = 0.75
    for document in documents:
        frequencies = {token: document.count(token) for token in query_tokens}
        score = 0.0
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            frequency_in_docs = document_frequency[token]
            inverse_frequency = math.log(
                1 + (len(documents) - frequency_in_docs + 0.5) / (frequency_in_docs + 0.5)
            )
            denominator = frequency + k1 * (
                1 - b + b * len(document) / average_length
            )
            score += inverse_frequency * (frequency * (k1 + 1) / denominator)
        scores.append(score)
    return scores


def retrieve(
    store: EmbeddingStore,
    query: str,
    metadata_filter: dict[str, str],
    *,
    role_inclusive: bool,
    hybrid: bool,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    if role_inclusive and set(metadata_filter) == {"customer_role"}:
        requested_role = metadata_filter["customer_role"]
        accepted_roles = (
            {requested_role, "both"} if requested_role in {"buyer", "seller"} else {requested_role}
        )
        candidates = [
            result
            for result in store.search(query, top_k=store.get_collection_size())
            if result["metadata"].get("customer_role") in accepted_roles
        ]
    else:
        candidates = store.search_with_filter(
            query,
            top_k=store.get_collection_size(),
            metadata_filter=metadata_filter,
        )

    if not hybrid or not candidates:
        return candidates[:top_k]

    lexical_scores = bm25_scores(query, candidates)
    maximum_lexical = max(lexical_scores) or 1.0
    reranked: list[dict[str, Any]] = []
    for result, lexical_score in zip(candidates, lexical_scores):
        dense_score = float(result["score"])
        dense_normalized = (dense_score + 1.0) / 2.0
        lexical_normalized = lexical_score / maximum_lexical
        combined_score = 0.55 * dense_normalized + 0.45 * lexical_normalized
        reranked.append(
            {
                **result,
                "dense_score": dense_score,
                "lexical_score": lexical_normalized,
                "score": combined_score,
            }
        )
    reranked.sort(key=lambda result: result["score"], reverse=True)
    return reranked[:top_k]


def run_retrieval(
    store: EmbeddingStore,
    *,
    role_inclusive: bool = False,
    hybrid: bool = False,
) -> list[dict[str, Any]]:
    benchmark: list[dict[str, Any]] = []
    for item in GOLDEN_SET:
        matches = retrieve(
            store,
            item["query"],
            item["metadata_filter"],
            role_inclusive=role_inclusive,
            hybrid=hybrid,
            top_k=3,
        )
        top_three = [
            {
                "rank": rank,
                "score": round(float(match["score"]), 4),
                "doc_id": match["metadata"].get("parent_doc_id"),
                "chunk_doc_id": match["metadata"].get("doc_id"),
                "source": match["metadata"].get("source"),
                "chunk_index": match["metadata"].get("chunk_index"),
                "content_preview": " ".join(
                    str(match["metadata"].get("raw_content") or match["content"]).split()
                )[:600],
                "content": str(match["metadata"].get("raw_content") or match["content"]),
                "dense_score": round(float(match.get("dense_score", match["score"])), 4),
                "lexical_score": round(float(match.get("lexical_score", 0.0)), 4),
            }
            for rank, match in enumerate(matches, start=1)
        ]
        expected_rank = next(
            (
                result["rank"]
                for result in top_three
                if result["doc_id"] == item["expected_doc_id"]
            ),
            None,
        )
        combined_context = " ".join(
            " ".join(
                str(match["metadata"].get("raw_content") or match["content"]).lower().split()
            )
            for match in matches
        )
        evidence_found = [
            term for term in item["evidence_terms"] if term.lower() in combined_context
        ]
        evidence_hit = len(evidence_found) == len(item["evidence_terms"])
        benchmark.append(
            {
                **item,
                "expected_rank": expected_rank,
                "source_hit_at_3": expected_rank is not None,
                "evidence_found": evidence_found,
                "evidence_hit_at_3": evidence_hit,
                "top_3": top_three,
            }
        )
    return benchmark


def extractive_llm(prompt: str) -> str:
    """LLM callable cục bộ: chọn các cửa sổ bằng chứng liên quan, không dùng gold answer."""
    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:", 1)[0]
    question = prompt.split("Question:", 1)[-1].rsplit("\nAnswer:", 1)[0]
    units = [
        re.sub(r"^\[\d+\]\s*", "", unit).strip()
        for unit in re.split(r"\n+|(?<=[.!?])\s+", context)
        if unit.strip()
    ]
    query_terms = set(tokenize(expand_query_for_lexical_search(question)))
    if not units or not query_terms:
        return "Không đủ ngữ cảnh để trả lời."

    candidates: list[tuple[float, int, str]] = []
    time_intent = any(
        intent in question.lower() for intent in ("bao lâu", "thời hạn", "bao nhiêu")
    )
    destination_intent = "hoàn về đâu" in question.lower()
    for index in range(len(units)):
        window = units[index : index + 3]
        window_text = " ".join(window)
        window_terms = set(tokenize(window_text))
        overlap = len(query_terms & window_terms)
        score = float(overlap)
        if time_intent and any(character.isdigit() for character in window_text):
            score += 1.0
        if time_intent and any(unit in window_text.lower() for unit in ("ngày", "giờ")):
            score += 0.5
        if destination_intent and any(
            unit in window_text.lower() for unit in ("tài khoản", "thẻ", "ví")
        ):
            score += 0.5
        candidates.append((score, index, window_text))

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected: list[tuple[int, str]] = []
    for score, index, text in candidates:
        if score <= 0:
            continue
        if any(abs(index - chosen_index) < 3 for chosen_index, _ in selected):
            continue
        candidate_terms = set(tokenize(text))
        if any(
            len(candidate_terms & set(tokenize(chosen_text)))
            / max(1, len(candidate_terms | set(tokenize(chosen_text))))
            > 0.8
            for _, chosen_text in selected
        ):
            continue
        selected.append((index, text))
        if len(selected) == 6:
            break
    if not selected:
        return "Không đủ ngữ cảnh để trả lời."
    selected.sort(key=lambda item: item[0])
    return " ".join(text for _, text in selected)


def add_agent_answers(
    retrieval: list[dict[str, Any]],
    embedder: LocalEmbedder,
) -> None:
    for item in retrieval:
        evidence_store = EmbeddingStore(
            collection_name=f"lienthanh_agent_q{item['id']}",
            embedding_fn=embedder,
        )
        evidence_store.add_documents(
            [
                Document(
                    id=f"q{item['id']}::rank_{result['rank']}",
                    content=result["content"],
                    metadata={
                        "source": result["source"],
                        "parent_doc_id": result["doc_id"],
                    },
                )
                for result in item["top_3"]
            ]
        )
        agent = personal.KnowledgeBaseAgent(store=evidence_store, llm_fn=extractive_llm)
        item["agent_answer"] = agent.answer(item["query"], top_k=3)


def main() -> int:
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Không tìm thấy corpus: {DATA_DIR}")

    embedder = LocalEmbedder()
    baseline_store, baseline_chunk_count = build_store(
        embedder,
        chunker=RecursiveChunker(chunk_size=800),
        collection_name="lienthanh_baseline",
    )
    tuned_store, tuned_chunk_count = build_store(
        embedder,
        chunker=ParagraphWindowChunker(chunk_size=650, overlap_blocks=1),
        collection_name="lienthanh_tuned",
        enrich_for_embedding=True,
    )
    similarity = run_similarity(embedder)
    baseline_retrieval = run_retrieval(baseline_store)
    tuned_dense_retrieval = run_retrieval(tuned_store, role_inclusive=True)
    tuned_retrieval = run_retrieval(tuned_store, role_inclusive=True, hybrid=True)
    add_agent_answers(tuned_retrieval, embedder)

    def summarize(retrieval: list[dict[str, Any]]) -> dict[str, str]:
        source_hits = sum(item["source_hit_at_3"] for item in retrieval)
        evidence_hits = sum(item["evidence_hit_at_3"] for item in retrieval)
        return {
            "source_hit_at_3": f"{source_hits}/{len(retrieval)}",
            "evidence_hit_at_3": f"{evidence_hits}/{len(retrieval)}",
        }

    output = {
        "embedding_backend": embedder._backend_name,
        "corpus": str(DATA_DIR.relative_to(REPO_ROOT)),
        "similarity": similarity,
        "strategies": {
            "baseline": {
                "description": "RecursiveChunker(800) + exact role filter + dense retrieval",
                "chunk_count": baseline_chunk_count,
                **summarize(baseline_retrieval),
                "retrieval": baseline_retrieval,
            },
            "paragraph_dense": {
                "description": (
                    "ParagraphWindowChunker(650, overlap=1) + title/metadata enrichment "
                    "+ inclusive customer_role + dense retrieval"
                ),
                "chunk_count": tuned_chunk_count,
                **summarize(tuned_dense_retrieval),
                "retrieval": tuned_dense_retrieval,
            },
            "paragraph_hybrid": {
                "description": (
                    "ParagraphWindowChunker(650, overlap=1) + title/metadata enrichment "
                    "+ inclusive customer_role + 55% dense/45% BM25"
                ),
                "chunk_count": tuned_chunk_count,
                **summarize(tuned_retrieval),
                "retrieval": tuned_retrieval,
            },
        },
        "selected_strategy": "paragraph_hybrid",
        "retrieval": tuned_retrieval,
        **summarize(tuned_retrieval),
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Embedding: {output['embedding_backend']}")
    print("\nSimilarity:")
    for item in similarity:
        print(f"  Pair {item['pair']}: predicted={item['prediction']} score={item['score']:.4f}")
    print("\nStrategy comparison:")
    for name, strategy in output["strategies"].items():
        print(
            f"  {name}: chunks={strategy['chunk_count']} "
            f"source_hit@3={strategy['source_hit_at_3']} "
            f"evidence_hit@3={strategy['evidence_hit_at_3']}"
        )
    print("\nSelected retrieval results:")
    for item in tuned_retrieval:
        rank = item["expected_rank"] if item["expected_rank"] is not None else "miss"
        print(
            f"  Q{item['id']}: expected_rank={rank} "
            f"source_hit@3={item['source_hit_at_3']} "
            f"evidence_hit@3={item['evidence_hit_at_3']}"
        )
        for result in item["top_3"]:
            print(
                f"    {result['rank']}. score={result['score']:.4f} "
                f"doc={result['doc_id']} chunk={result['chunk_index']}"
            )
    print(f"\nSource Hit@3: {output['source_hit_at_3']}")
    print(f"Evidence Hit@3: {output['evidence_hit_at_3']}")
    print(f"Saved: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
