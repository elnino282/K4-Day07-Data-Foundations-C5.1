# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Văn Huy  
**Mã sinh viên:** 2A202601356  
**Nhóm:** C5.1 
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**  
Độ tương tự cosine cao nghĩa là hai vector embedding có góc giữa chúng rất nhỏ (hướng vector gần như trùng nhau), chỉ ra rằng hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa hoặc ý nghĩa biểu đạt. Với xử lý ngôn ngữ tự nhiên, điều này cho phép hệ thống nhận diện hai câu có nội dung liên quan chặt chẽ ngay cả khi chúng sử dụng các từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- **Câu A:** Shopee hỗ trợ thanh toán bằng ví ShopeePay.
- **Câu B:** Người mua có thể trả tiền đơn hàng bằng Ví ShopeePay.
- **Tại sao tương đồng:** Cả hai câu đều đề cập đến cùng một chủ đề thanh toán đơn hàng trên sàn Shopee thông qua dịch vụ ví điện tử ShopeePay.

**Ví dụ có độ tương tự THẤP:**
- **Câu A:** Người bán phải chọn đúng danh mục ngành hàng khi đăng sản phẩm.
- **Câu B:** Thời tiết hôm nay có mưa lớn ở Hà Nội.
- **Tại sao khác:** Hai câu thuộc hai phạm trù nội dung hoàn toàn tách biệt: một câu thuộc quy định bán hàng e-commerce, câu còn lại là thông tin dự báo thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**  
Cosine similarity đo mức độ cùng hướng giữa hai vector và ít bị ảnh hưởng bởi độ lớn của vector. Với text embeddings, hướng vector thường phản ánh nội dung ngữ nghĩa tốt hơn độ lớn tuyệt đối, vì vậy cosine similarity thường phù hợp để so sánh các câu hoặc đoạn văn có độ dài khác nhau. Khoảng cách Euclid vẫn có thể sử dụng, đặc biệt khi các vector đã được chuẩn hóa, nhưng cosine similarity thường dễ diễn giải hơn trong bài toán truy xuất văn bản.

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**  
- **Công thức:**  
  $$\text{Số chunks} = \left\lceil \frac{\text{Tổng độ dài} - \text{Overlap}}{\text{Chunk size} - \text{Overlap}} \right\rceil = \left\lceil \frac{10000 - 50}{500 - 50} \right\rceil = \left\lceil \frac{9950}{450} \right\rceil = \left\lceil 22.111 \right\rceil = 23$$
- **Đáp án:** **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**  
- **Khi `overlap=100`:**  
  $$\text{Số chunks} = \left\lceil \frac{10000 - 100}{500 - 100} \right\rceil = \left\lceil \frac{9900}{400} \right\rceil = \left\lceil 24.75 \right\rceil = 25$$
- **Thay đổi:** Số lượng chunk tăng từ **23** lên **25** (tăng 2 chunks).
- **Lý do tăng overlap:** Tăng độ chồng chéo giúp duy trì ngữ cảnh liên tục ở ranh giới giữa hai chunk kế tiếp, tránh việc ngắt đoạn làm mất thông tin điều kiện quan trọng (ví dụ: mệnh đề "nếu...", "ngoại trừ..."). Tuy nhiên, đánh đổi lại là tăng số lượng chunk và chi phí tính toán embedding/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**  
Tôi áp dụng biểu thức chính quy `re.split(r"(?<=[.!?])(?:\s+|$)", text.strip())` để phân tách văn bản dựa trên các dấu kết thúc câu (`.`, `!`, `?`). Các câu sau khi được tách và làm sạch khoảng trắng sẽ được gom nhóm thành các chunk, trong đó mỗi chunk chứa tối đa `max_sentences_per_chunk` câu. Hàm cũng kiểm tra và xử lý an toàn đối với văn bản rỗng hoặc chỉ chứa khoảng trắng (trả về danh sách rỗng `[]`).

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**  
Tôi xây dựng thuật toán phân tách đệ quy sử dụng danh sách các separator theo thứ tự ưu tiên từ lớn đến nhỏ: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `) và ký tự (`""`). 
- **Base case:** Nếu độ dài văn bản hiện tại $\le$ `chunk_size`, thực hiện `strip()` và trả về chunk.
- **Recursive step:** Nếu đoạn vượt quá `chunk_size`, thuật toán thử split theo separator đầu tiên trong danh sách. Các phần nhỏ hơn sẽ được ghép lại cho đến khi đạt `chunk_size`. Nếu một segment đơn lẻ vẫn quá dài, hàm sẽ gọi đệ quy `_split` với danh sách separator còn lại.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**  
- **`add_documents`:** Duyệt qua từng đối tượng `Document`, sinh vector embedding bằng `embedding_fn`, đóng gói thông tin gồm `id`, `content`, `metadata`, `embedding`. Nếu ChromaDB khả dụng, dữ liệu được nạp trực tiếp vào collection; nếu không, lưu trữ trong danh sách bộ nhớ tạm (`self._in_memory_docs`).
- **`search`:** Nhúng câu truy vấn `query` thành vector, sau đó tính điểm tương tự bằng hàm `compute_similarity` (hoặc dot product trên vector chuẩn hóa) đối với từng document trong store. Kết quả được sắp xếp giảm dần theo `score` và lấy ra `top_k` kết quả có điểm cao nhất.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**  
- **`search_with_filter`:** Trước khi tính toán độ tương tự vector, hàm thực hiện lọc danh sách ứng viên dựa trên dictionary `metadata`. Chỉ những chunk có metadata khớp hoàn toàn với các tiêu chí lọc (ví dụ: `customer_role == "seller"`) mới được đưa vào bước xếp hạng.
- **`delete_document`:** Tìm và xóa toàn bộ các chunk trong bộ nhớ tạm có `metadata["doc_id"]` khớp với ID tài liệu cần xóa. Nếu đang sử dụng ChromaDB, hàm đồng thời gọi `collection.delete(where={"doc_id": doc_id})` để đảm bảo dữ liệu được đồng bộ triệt để.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**  
Hàm `answer` thực hiện quy trình RAG 3 bước:
1. Gọi `store.search(query, top_k=top_k)` để lấy danh sách các chunk liên quan nhất.
2. Trích xuất nội dung các chunk và ghép thành đoạn `Context` có cấu trúc rõ ràng.
3. Xây dựng prompt hoàn chỉnh kết hợp ngữ cảnh và câu hỏi, truyền vào `llm_fn` để tạo câu trả lời. Nếu không tìm thấy ngữ cảnh phù hợp, prompt yêu cầu LLM thông báo rõ ràng thiếu thông tin để tránh tình trạng hallucination (trả lời bịa).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

Lệnh thực thi bộ kiểm thử trong môi trường ảo:

```powershell
$env:LAB_SOLUTION_PACKAGE="src.2A202601356_HoangVanHuy"
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Kết quả:

```text
42 passed in 0.12s
```

**Số lượng bài test vượt qua (pass):** **42 / 42** (Đạt điểm tối đa 30/30)

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Quy ước đánh giá sử dụng trong phần này: Điểm Cosine Similarity từ **0.50 trở lên** được xem là tương tự **cao** ($\ge 0.50$); dưới **0.50** được xem là tương tự **thấp** ($< 0.50$).

| Cặp | Câu A | Câu B | Dự đoán ngữ nghĩa | Điểm thực tế | Đánh giá khớp? |
|:---:|-------|-------|:------------------:|:------------:|:--------------:|
| **1** | Shopee hỗ trợ thanh toán qua ShopeePay. | Người dùng có thể trả tiền bằng ví điện tử trên Shopee. | cao | **0.8072** | Đúng |
| **2** | Chính sách đổi trả hàng trong 15 ngày. | Thời hạn hoàn tiền là hai tuần kể từ ngày nhận hàng. | cao | **0.4475** | Sai |
| **3** | Shopee bảo vệ người mua khỏi hàng giả. | Hôm nay trời Hà Nội nhiều mây có mưa. | thấp | **-0.1068** | Đúng |
| **4** | Người bán cần xác minh danh tính để đăng sản phẩm. | Nhà bán hàng phải hoàn tất KYC trước khi niêm yết. | cao | **0.3813** | Sai |
| **5** | Điều khoản dịch vụ Shopee áp dụng theo luật Việt Nam. | Shopee cấm bán hàng giả, hàng nhái trên nền tảng. | thấp | **0.2969** | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**  

Kết quả bất ngờ nhất là **Cặp 4**, vì hai câu cùng nói về việc người bán phải xác minh danh tính trước khi đăng hoặc niêm yết sản phẩm nhưng điểm thực tế chỉ đạt `0.3813`. Điều này cho thấy embedding có thể chưa liên kết tốt từ viết tắt chuyên ngành như `KYC` với cụm tiếng Việt “xác minh danh tính”. Riêng **Cặp 2**, điểm dưới `0.50` tương đối hợp lý vì “đổi trả trong 15 ngày” và “hoàn tiền trong hai tuần” có liên quan nhưng không hoàn toàn đồng nghĩa; embedding phản ánh mức liên quan ngữ nghĩa chứ không tự suy luận rằng hai quy trình hoặc hai mốc thời gian là giống nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Lưu ý:** Cột điểm score cần lấy trực tiếp từ output chạy trên máy cá nhân. Không nên tự điền số ước lượng vì điểm phụ thuộc vào model embedding, dữ liệu đã ingest và chiến lược chunking.

- **Thử nghiệm truy xuất:** Dưới đây là kết quả đánh giá trên 5 câu hỏi chính sách thương mại điện tử:

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt nội dung & nguồn) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|:---:|-------|--------------------------------|:-------:|:-----------:|------------------------|
| **1** | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với hàng thông thường và thực phẩm tươi sống hoặc đông lạnh? | `shopee-buyer-return-refund-policy` — Điều 3.2 quy định thời hạn 15 ngày với hàng thông thường và 24 giờ với hàng tươi sống/đông lạnh. | 0.9440 | Có | Hàng thông thường có thời hạn 15 ngày kể từ khi nhận hàng, thực phẩm tươi sống hoặc đông lạnh có thời hạn 24 giờ; trường hợp quá hạn Shopee có thể xem xét hỗ trợ riêng. |
| **2** | Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ được hoàn về đâu và trong bao lâu? | `shopee-buyer-refund-timeline` — Bảng quy định thời gian hoàn tiền theo phương thức thẻ tín dụng/ghi nợ từ 7–14 ngày làm việc. | 0.8766 | Có | Tiền sẽ được hoàn trực tiếp về tài khoản thẻ tín dụng/ghi nợ đã dùng để thanh toán trong khoảng 7–14 ngày làm việc tùy thuộc vào ngân hàng phát hành. |
| **3** | Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào? | `shopee-seller-listing-rules` — Quy định tiêu chuẩn hình ảnh sản phẩm (ảnh rõ nét, ảnh thật, tỷ lệ diện tích sản phẩm $\ge 40\%$). | 0.9432 | Có | Hình ảnh phải rõ nét, liên quan trực tiếp đến sản phẩm; có ít nhất một ảnh thật của sản phẩm và sản phẩm chiếm tối thiểu 40% diện tích ảnh. |
| **4** | Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào và những bằng chứng nào được Shopee khuyến khích? | `shopee-seller-shipping-fulfillment-policy` — Điều khoản quy định thời hạn 24h và các loại bằng chứng (video đóng gói, hóa đơn/vận đơn). | 0.9176 | Có | Người bán cần cung cấp bằng chứng trong vòng 24 giờ kể từ khi được yêu cầu; video đóng gói nguyên vẹn là bằng chứng được khuyến khích nhất và hóa đơn/vận đơn là bằng chứng hợp lệ. |
| **5** | Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận? | `shopee-buyer-return-refund-policy` — Điều 11.2(a) quy định cơ chế chuyển tiền cho Người bán và khấu trừ điều chỉnh nếu hoàn tiền phát sinh. | 0.9287 | Có | Shopee chuyển tiền từ Tài khoản Đảm bảo sang Số dư tài khoản Người bán; nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận, Shopee sẽ thực hiện điều chỉnh/khấu trừ để hoàn tiền lại cho Người mua. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**. Theo kết quả đã ghi nhận, cả năm câu hỏi đều có ít nhất một chunk liên quan trong ba kết quả đầu tiên.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**  
Việc thiết kế schema metadata bài bản (như phân loại `customer_role`, `policy_type`, `category`) giúp tối ưu hiệu năng và độ chính xác của tìm kiếm vector khi kết hợp cơ chế `search_with_filter`. Kỹ thuật này giúp giảm đáng kể nhiễu từ các tài liệu không cùng phạm vi, chẳng hạn hạn chế nhầm lẫn giữa chính sách dành cho Người bán và Người mua.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|:---------|:----------------:|
| 1. Khởi động (Warm-up) | 5 / 5 |
| 2. Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| 3. Hoàn thiện code (Core Implementation - 42 tests pass) | 30 / 30 |
| 4. Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| 5. Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng điểm phần cá nhân** | **60 / 60 (tự đánh giá)** |
