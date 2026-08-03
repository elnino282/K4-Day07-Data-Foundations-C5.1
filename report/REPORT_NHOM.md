# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** C5.1 (K4)  
**Thành viên:**
- Hoàng Văn Huy — 2A202601356
- Hồ Ngọc Quỳnh — 2A202501684
- Nguyễn Đình Liên Thành — 2A202601790

**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách hỗ trợ khách hàng của Shopee Việt Nam, bao gồm: chính sách trả hàng & hoàn tiền và phương thức thanh toán (dành cho Người Mua), quy định đăng bán và vận chuyển (dành cho Người Bán), điều khoản dịch vụ và bảo mật dữ liệu cá nhân (áp dụng cả hai vai trò).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|--------------------|----------|-----------------|
| 1 | Các phương thức thanh toán hiện có trên Shopee | https://help.shopee.vn/portal/4/article/79198 | 2026-08-03 / not-stated | 8,195 | `doc_id`, `customer_role: buyer`, `source_url`, `retrieved_at` |
| 2 | Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn | https://help.shopee.vn/portal/4/article/189473 | 2026-08-03 / not-stated | 5,444 | `doc_id`, `customer_role: buyer`, `source_url`, `retrieved_at` |
| 3 | Chính sách Trả hàng và Hoàn tiền Shopee | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / not-stated | 26,428 | `doc_id`, `customer_role: buyer`, `source_url`, `retrieved_at` |
| 4 | Quy định về đăng bán sản phẩm trên Shopee | https://help.shopee.vn/portal/4/article/77246 | 2026-08-03 / not-stated | 29,283 | `doc_id`, `customer_role: seller`, `source_url`, `retrieved_at` |
| 5 | Chính sách Vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / not-stated | 33,201 | `doc_id`, `customer_role: seller`, `source_url`, `retrieved_at` |
| 6 | Chính sách Cấm/Hạn chế Sản phẩm | https://help.shopee.vn/portal/4/article/77247 | 2026-08-03 / not-stated | 17,473 | `doc_id`, `customer_role: seller`, `source_url`, `retrieved_at` |
| 7 | Điều khoản Dịch vụ Shopee | https://help.shopee.vn/portal/4/article/77243 | 2026-08-03 / not-stated | 111,508 | `doc_id`, `customer_role: both`, `source_url`, `retrieved_at` |
| 8 | Chính sách Bảo mật Shopee Việt Nam | https://help.shopee.vn/portal/4/article/77244 | 2026-08-03 / 6/4/2026 | 58,067 | `doc_id`, `customer_role: both`, `source_url`, `retrieved_at`, `document_version` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|----------------------------------------------|
| `doc_id` | string | `shopee-buyer-return-refund-policy` | Nhận diện tài liệu gốc; dùng để lọc, xóa (`delete_document`) và truy vết chunk về nguồn. |
| `customer_role` | string | `buyer` / `seller` / `both` | Cho phép `search_with_filter` loại bỏ tài liệu sai đối tượng — câu hỏi Người Mua không trả về chunk chính sách Người Bán. |
| `source_url` | string | `https://help.shopee.vn/portal/4/article/77251` | Cung cấp liên kết nguồn để kiểm chứng nội dung khi cần xác minh tính chính xác. |
| `retrieved_at` | string | `2026-08-03` | Theo dõi thời điểm thu thập; đánh giá độ tươi dữ liệu và kích hoạt tái thu thập khi chính sách thay đổi. |
| `chunk_index` | int | `5` | Giúp tái tạo thứ tự đoạn văn gốc; hỗ trợ gộp context nhiều chunk liên tiếp khi cần. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` với `chunk_size=200` trên tài liệu `shopee-buyer-return-refund-policy.md` (26,428 ký tự):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------------------|---------------|-------------------|--------------------------|
| shopee-buyer-return-refund-policy | FixedSizeChunker (`fixed_size`) | ~178 | ~197 ký tự | Không — cắt ngang giữa câu/điều khoản |
| shopee-buyer-return-refund-policy | SentenceChunker (`by_sentences`) | ~77 | ~113 ký tự | Một phần — giữ nguyên câu nhưng mất cấu trúc đoạn |
| shopee-buyer-return-refund-policy | RecursiveChunker (`recursive`) | ~53 | ~170 ký tự | Tốt — ưu tiên tách theo đoạn trước, giữ ngữ nghĩa |

### Chiến lược của từng thành viên

**Thành viên 1 — Hoàng Văn Huy**
- **Loại chiến lược:** `SentenceChunker` (`by_sentences`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách thương mại điện tử thường được viết theo từng điều khoản ngắn, mỗi câu chứa một quy định hoàn chỉnh. Tách theo ranh giới câu (`re.split` trên dấu `.!?`) đảm bảo mỗi chunk không bao giờ bị cắt ngang giữa một quy định, giúp embedding phản ánh đúng ngữ nghĩa đơn vị nhỏ nhất. Gom 3 câu/chunk cân bằng ngữ cảnh cục bộ mà không làm chunk quá dài.
- **Code snippet:**
```python
sentences = [
    s.strip()
    for s in re.split(r"(?<=[.!?])(?:\s+|$)", text.strip())
    if s.strip()
]
return [
    " ".join(sentences[i : i + self.max_sentences_per_chunk])
    for i in range(0, len(sentences), self.max_sentences_per_chunk)
]
```

**Thành viên 2 — Hồ Ngọc Quỳnh**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=500`, separators `["\n\n", "\n", ". ", " ", ""]`)
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách Shopee được tổ chức theo cấu trúc phân cấp rõ ràng (chương → điều → khoản → câu), nên tách đệ quy từ mức lớn đến nhỏ giúp giữ tính nguyên vẹn của từng điều khoản. Nếu một đoạn văn đã đủ nhỏ thì không cần chia nhỏ thêm; chỉ khi vượt `chunk_size` mới tiếp tục cắt bằng separator có mức ưu tiên thấp hơn, tránh phá vỡ cấu trúc pháp lý.
- **Code snippet:**
```python
def _split(self, current_text, remaining_separators):
    if len(current_text) <= self.chunk_size:
        stripped = current_text.strip()
        return [stripped] if stripped else []
    separator = remaining_separators[0]
    # ghép các phần nhỏ hơn chunk_size, chia đệ quy nếu phần vẫn quá dài
    parts = current_text.split(separator)
    chunks, pending = [], ""
    for i, part in enumerate(parts):
        seg = part + separator if i < len(parts) - 1 else part
        if len(seg) > self.chunk_size:
            if pending.strip(): chunks.append(pending.strip())
            pending = ""
            chunks.extend(self._split(seg, remaining_separators[1:]))
        elif len(pending) + len(seg) <= self.chunk_size:
            pending += seg
        else:
            if pending.strip(): chunks.append(pending.strip())
            pending = seg
    if pending.strip(): chunks.append(pending.strip())
    return chunks
```

**Thành viên 3 — Nguyễn Đình Liên Thành**
- **Loại chiến lược:** `ParagraphWindowChunker` (custom, `chunk_size=650`, `overlap_blocks=1`) + Hybrid Reranking (55% Dense Vector + 45% BM25)
- **Mô tả & lý do chọn cho chủ đề này:** Văn bản chính sách pháp lý thường chứa bảng tra cứu và các điều khoản có quan hệ liên tiếp chặt chẽ. Chunking theo đoạn với overlap 1 đoạn giữ được ngữ cảnh xuyên suốt giữa các chunk liền kề, tránh mất dữ liệu bảng bị cắt đứt. Kết hợp BM25 (45%) và Dense Vector (55%) giúp hệ thống tìm đúng chunk ngay cả khi query dùng từ viết tắt hoặc số liệu chính xác như "24 giờ", "7–14 ngày làm việc".
- **Code snippet:**
```python
class ParagraphWindowChunker:
    def chunk(self, text):
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        chunks, start = [], 0
        while start < len(blocks):
            selected, length, end = [], 0, start
            while end < len(blocks):
                block = blocks[end]
                projected = length + len(block) + (2 if selected else 0)
                if selected and projected > self.chunk_size: break
                selected.append(block); length = projected; end += 1
                if length >= self.chunk_size: break
            if not selected: selected, end = [blocks[start][:self.chunk_size]], start + 1
            chunks.append("\n\n".join(selected))
            if end >= len(blocks): break
            start = max(start + 1, end - self.overlap_blocks)
        return chunks

# Hybrid reranking: combined_score = 0.55 * dense_norm + 0.45 * bm25_norm
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------------------|---------------------|-----------|----------|
| Hoàng Văn Huy | SentenceChunker (max 3 câu) | 10/10 (5/5 câu hit top-3) | Không cắt ngang câu, đơn giản, tốc độ nhanh | Chunk ngắn, không có overlap, đôi khi thiếu ngữ cảnh liên điều khoản |
| Hồ Ngọc Quỳnh | RecursiveChunker (chunk_size=500) | 10/10 (5/5 câu hit top-3) | Giữ cấu trúc đoạn/điều khoản, linh hoạt với văn bản không đồng đều | Chunk kích thước không cố định, không có overlap rõ ràng |
| Nguyễn Đình Liên Thành | ParagraphWindowChunker + Hybrid BM25+Dense | 10/10 (5/5 nguồn hit, 5/5 evidence hit) | Kết hợp semantic + keyword; overlap giữ ngữ cảnh bảng; khắc phục điểm yếu dense | Phức tạp hơn khi triển khai; cần điều chỉnh trọng số BM25 tùy corpus |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `ParagraphWindowChunker` kết hợp Hybrid Reranking (55% Dense + 45% BM25) của Nguyễn Đình Liên Thành cho kết quả toàn diện nhất, đạt `source_hit@3 = 5/5` và `evidence_hit@3 = 5/5` theo benchmark thực tế trong `bench_results.json` (so với baseline RecursiveChunker(800) chỉ đạt `evidence_hit@3 = 2/5`). Đối với văn bản chính sách pháp lý chứa nhiều bảng và điều khoản có tính liên kết cao, overlap 1 đoạn ngăn mất thông tin ở ranh giới chunk; BM25 bù đắp điểm yếu của dense embedding khi query dùng số liệu chính xác hoặc từ chuyên ngành. Tuy nhiên, `SentenceChunker` và `RecursiveChunker` cũng đạt kết quả tốt trên bộ câu hỏi với điểm top-1 cosine similarity luôn trên 0.87.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk/nguồn chứa thông tin |
|---|-----------------|-----------------|--------------------------------|----------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với hàng thông thường và thực phẩm tươi sống hoặc đông lạnh? | `{"customer_role": "buyer"}` | Hàng thông thường là 15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công; thực phẩm tươi sống hoặc đông lạnh là 24 giờ. Sau thời hạn này, Shopee vẫn có thể xem xét hỗ trợ trong phạm vi phù hợp với chính sách. | `shopee-buyer-return-refund-policy.md`, Điều 3.2 |
| 2 | Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ được hoàn về đâu và trong bao lâu? | `{"customer_role": "buyer"}` | Tiền được hoàn về đúng tài khoản thẻ tín dụng hoặc thẻ ghi nợ đã dùng để thanh toán đơn hàng trong vòng 7–14 ngày làm việc, tùy theo ngân hàng. | `shopee-buyer-refund-timeline.md`, bảng thời gian hoàn tiền và phần lưu ý |
| 3 | Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào? | `{"customer_role": "seller"}` | Hình ảnh phải rõ và thể hiện chi tiết tình trạng sản phẩm, không chứa thông tin không liên quan. Phải có ít nhất một ảnh thật do người bán tự chụp, trong đó sản phẩm chiếm ít nhất 40% diện tích toàn ảnh; ngôn ngữ trên phông nền phải là tiếng Việt. | `shopee-seller-listing-rules.md`, mục Hình ảnh sản phẩm |
| 4 | Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào và những bằng chứng nào được Shopee khuyến khích? | `{"customer_role": "seller"}` | Trừ khi Shopee có yêu cầu khác, bằng chứng phải được cung cấp trong vòng 24 giờ kể từ khi gửi khiếu nại hoặc nhận yêu cầu từ Shopee. Video quá trình đóng gói được khuyến khích là bằng chứng mạnh; vận đơn hoặc hóa đơn vận chuyển là bằng chứng vững chắc chứng minh người bán đã giao hàng. | `shopee-seller-shipping-fulfillment-policy.md`, mục Bằng chứng khiếu nại |
| 5 | Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận? | `{"customer_role": "both"}` | Shopee ban đầu chuyển tiền từ Tài khoản Đảm bảo Shopee sang Số dư tài khoản Shopee của người bán. Nếu thời gian trả hàng/hoàn tiền vẫn chưa kết thúc và yêu cầu sau đó được chấp thuận, Shopee có quyền điều chỉnh khoản tiền thanh toán để hoàn tiền cho người mua. | `shopee-terms-of-service-vn.md`, Điều 11.2(a) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền | ParagraphWindowChunker + Hybrid | Có (cả 3 chiến lược đều hit top-1, score ≥ 0.84) | Câu hỏi trực tiếp, dense embedding đã đủ tốt |
| 2 | Thời gian hoàn tiền về thẻ tín dụng/ghi nợ | ParagraphWindowChunker + Hybrid | Có (BM25 bổ trợ từ khóa "thẻ tín dụng/ghi nợ" chính xác) | Hybrid giúp tìm đúng dòng bảng chứa thời gian 7–14 ngày |
| 3 | Yêu cầu hình ảnh sản phẩm | ParagraphWindowChunker + Hybrid | Có (cả 3 chiến lược hit top-1, score ≥ 0.94) | `customer_role: seller` filter loại bỏ chunk không liên quan |
| 4 | Thời hạn và bằng chứng khiếu nại vận chuyển | ParagraphWindowChunker + Hybrid | Có (cả 3 chiến lược hit top-1, score ≥ 0.91) | BM25 nhận diện từ khóa "video đóng gói", "vận đơn" chính xác |
| 5 | Xử lý tiền thanh toán sau hoàn tiền chấp thuận | ParagraphWindowChunker + Hybrid | Có (chunk từ `shopee-terms-of-service-vn` Điều 11.2) | Câu hỏi cần `customer_role: both`; Hybrid kết hợp ngữ nghĩa + từ khóa pháp lý |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc metadata theo `customer_role` có tác dụng rõ rệt nhất ở **Câu 3** (hình ảnh sản phẩm — lọc `seller`) và **Câu 4** (bằng chứng vận chuyển — lọc `seller`): nếu không lọc, các chunk từ chính sách Người Mua sẽ cạnh tranh điểm similarity và có thể chiếm top kết quả. Ở **Câu 5**, chiến lược lọc vai trò inclusive (chấp nhận `buyer`, `seller`, `both`) giúp không bỏ sót chunk trong Điều khoản Dịch vụ vốn áp dụng cho cả hai vai trò. Nhìn chung, metadata filter kết hợp với vector search là cặp đôi thiết yếu cho corpus đa vai trò.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - **Cosine similarity không phải tất cả:** Các cặp câu về "đổi trả 15 ngày" vs "hoàn tiền hai tuần" (score 0.4475) hay "xác minh danh tính" vs "KYC" (score 0.3813) đều dưới 0.50 dù ngữ nghĩa tương đồng — dense embedding đơn thuần chưa đủ cho RAG chuyên sâu trên chính sách pháp lý đặc thù.
> - **Hybrid Search lấp đầy khoảng trống của Dense:** BM25 (45%) bù đắp tốt khi câu hỏi chứa số liệu chính xác hoặc thuật ngữ pháp lý; `evidence_hit@3` của chiến lược Hybrid đạt 5/5 so với 2/5 của baseline RecursiveChunker(800) thuần dense (theo `bench_results.json`).
> - **Metadata filter là đòn bẩy hiệu quả nhất:** Phân loại `customer_role` loại bỏ hàng chục chunk nhiễu, tăng độ chính xác top-3 mà không cần tăng tài nguyên tính toán — đặc biệt hiệu quả với corpus đa vai trò như Shopee.

**Bài học rút ra khi so sánh trong nhóm:**
> Ba chiến lược chunking (`SentenceChunker`, `RecursiveChunker`, `ParagraphWindowChunker`) đều đạt 5/5 câu hit top-3 trên bộ câu hỏi đánh giá, nhưng điểm similarity thô và chất lượng câu trả lời của Agent khác nhau đáng kể. `SentenceChunker` tạo chunk ngắn, dễ match câu hỏi ngắn nhưng đôi khi thiếu ngữ cảnh khi câu trả lời trải dài nhiều điều khoản. Ngược lại, `ParagraphWindowChunker` với overlap giữ liền mạch cấu trúc bảng và điều khoản phức tạp, giúp Agent tổng hợp câu trả lời đầy đủ hơn và đạt `evidence_hit@3 = 5/5` theo cả hai tiêu chí source và nội dung bằng chứng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm trường metadata `policy_type` (ví dụ: `refund`, `listing`, `shipping`, `privacy`) để hỗ trợ lọc đa chiều, không chỉ dừng ở `customer_role`. Ngoài ra, nhóm sẽ thực hiện Query Expansion tự động (giải nghĩa từ viết tắt như KYC → "xác minh danh tính", COD → "thanh toán khi nhận hàng" trước khi embedding) để khắc phục điểm yếu của mô hình đa ngữ với thuật ngữ chuyên ngành. Cuối cùng, nhóm sẽ thêm bước re-ranking bằng cross-encoder nhỏ sau bước retrieval để tăng độ chính xác cho các câu hỏi phức tạp cần suy luận đa điều khoản.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40 (tự đánh giá)** |
