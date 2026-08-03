# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đình Liên Thành
**Mã sinh viên:** 2A202601790
**Nhóm:** C5.1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau, cho thấy hai đoạn văn có nội dung hoặc ý nghĩa ngữ nghĩa tương đồng. Giá trị similarity này càng gần 1 thì mức độ tương đồng càng cao

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua có thể yêu cầu hoàn tiền khi sản phẩm không đúng mô tả
- Câu B: Khách hàng được phép đề nghị hoàn lại tiền nếu hàng nhận được khác với thông tin đăng bán
- Tại sao tương đồng: Hai câu cùng diễn đạt quyền yêu cầu hoàn tiền của người mua khi sản phẩm thực tế không khớp với mô tả, nhưng ý nghĩa chung đều giống nhau

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người bán phải giao hàng cho đơn vị vận chuyển đúng thời hạn
- Câu B: Người bán phải chuẩn bị hàng hóa ngay khi nhận được yêu cầu đơn hàng của người mùa
- Tại sao khác: Hai câu thuộc cùng một chủ đề về vai trò của người bán hàng online nhưng ý nghĩa khác nhau, nằm ở hai giai đoạn khác nhau của người bán. Dù đọc sơ qua có vẻ giống nhưng đây là 2 câu có độ tương đồng không cao về ngữ nghĩa

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
Cosine similarity tập trung vào hướng của vector nên phản ánh mức độ tương đồng ngữ nghĩa mà ít bị ảnh hưởng bởi độ lớn của vector hoặc độ dài văn bản. Trong khi khoảng cách Euclid chịu ảnh hưởng trực tiếp bởi độ lớn của vector, vì vậy hai vector cùng hướng nhưng khác độ lớn vẫn có thể bị đánh giá là cách xa nhau

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
Khoảng dịch giữa hai chunk liên tiếp là 500 - 50 = 450. Số chunk (cuối - đầu, tất cả chia k.cách rồi + 1) ((10,000 - 500) / 450) + 1 = (21.11) + 1 = làm tròn thành 23
Đáp án: 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Khi overlap tăng lên 100, khoảng dịch chuyển giảm còn 500 - 100 = 400 và số chunk là (10,000 - 500) / 400 + 1 = 25, tăng thêm 2 chunk. Overlap lớn hơn giúp giữ lại ngữ cảnh nằm ở ranh giới giữa hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí embedding cũng cao hơn

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
Tôi dùng biểu thức chính quy `(?<=[.!?])(?:\s+|$)` để tách câu sau các dấu chấm, chấm than hoặc chấm hỏi khi phía sau là khoảng trắng hay cuối chuỗi. Các câu được strip, phần tử rỗng bị loại bỏ và sau đó được ghép theo `max_sentences_per_chunk`. Hàm trả về danh sách rỗng với văn bản rỗng hoặc chỉ chứa khoảng trắng, đồng thời bảo đảm số câu tối đa mỗi chunk luôn ít nhất là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
Thuật toán lần lượt thử các separator theo mức ưu tiên từ đoạn văn, dòng, câu, từ đến ký tự; các đoạn nhỏ được ghép vào biến `pending` nếu tổng độ dài chưa vượt `chunk_size`. Nếu một đoạn vẫn quá dài, hàm tiếp tục chia đệ quy bằng separator có mức ưu tiên thấp hơn. Base case là khi nội dung đã ngắn hơn hoặc bằng `chunk_size`; nếu hết separator thì văn bản được cắt trực tiếp theo kích thước cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
`add_documents` chuyển mỗi `Document` thành một record gồm ID duy nhất, nội dung, bản sao metadata có thêm `doc_id` và vector embedding. Record luôn được lưu trong bộ nhớ và được ghi thêm vào ChromaDB nếu backend này khả dụng; nếu ChromaDB lỗi thì hệ thống tiếp tục dùng in-memory store. Khi tìm kiếm, truy vấn được embedding, điểm được tính bằng tích vô hướng với từng vector đã lưu, sau đó kết quả được sắp xếp giảm dần và lấy `top_k` phần tử.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
`search_with_filter` lọc record theo tất cả cặp key-value trong `metadata_filter` trước khi tính điểm và xếp hạng, nhờ đó tài liệu ngoài phạm vi không thể lọt vào kết quả. `delete_document` tìm toàn bộ record có metadata `doc_id` tương ứng, xóa chúng khỏi in-memory store và gửi danh sách ID sang ChromaDB nếu đang sử dụng backend này. Hàm trả về `True` khi có ít nhất một record bị xóa và `False` nếu không tìm thấy tài liệu.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
Hàm `answer` truy xuất `top_k` chunk liên quan rồi đánh số từng chunk và nối chúng thành phần `Context` trong prompt. Prompt yêu cầu mô hình chỉ trả lời dựa trên ngữ cảnh được cung cấp và phải nói rõ khi ngữ cảnh không đủ; nếu không truy xuất được chunk nào thì dùng thông báo `No relevant context retrieved.`. Cuối cùng câu hỏi được đặt sau phần ngữ cảnh và prompt hoàn chỉnh được chuyển cho `llm_fn`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
42 passed in 0.12s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua muốn trả hàng và nhận lại tiền. | Khách hàng yêu cầu hoàn tiền cho đơn hàng. | Cao | 0.6677 | Có |
| 2 | Tiền hoàn được chuyển về thẻ đã thanh toán. | Khoản hoàn trả được gửi lại vào thẻ ngân hàng ban đầu. | Cao | 0.8292 | Có |
| 3 | Người bán cần đăng ảnh thật của sản phẩm. | Người bán phải cung cấp bằng chứng vận chuyển. | Thấp | 0.5824 | Không |
| 4 | Shopee chuyển tiền thanh toán cho người bán. | Hôm nay thời tiết có mưa không? | Thấp | -0.0471 | Có |
| 5 | Người bán phải gửi bằng chứng khiếu nại trong 24 giờ. | Bằng chứng vận chuyển cần được cung cấp trong vòng một ngày. | Cao | 0.4126 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 có điểm cao hơn dự đoán dù nói về hai yêu cầu khác nhau. Có vẻ như embedding đã chú ý nhiều đến các từ chung như “người bán” và cùng bối cảnh là vai trò của "người bán" hơn là sự khác biệt thật sự của chúng. Tuy nhiên, điểm số đo được cũng chỉ là 0.5824, thật ra không quá cao nhưng cũng là một chỉ số cao hơn dự đoán
---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với hàng thông thường và thực phẩm tươi sống hoặc đông lạnh? | Điều 3.2 nêu thời hạn 15 ngày đối với hàng thông thường và 24 giờ đối với thực phẩm tươi sống hoặc đông lạnh. | 0.9440 | Có | Hàng thông thường có thời hạn 15 ngày, thực phẩm tươi sống hoặc đông lạnh có thời hạn 24 giờ; trường hợp quá hạn vẫn có thể được Shopee xem xét hỗ trợ. |
| 2 | Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ được hoàn về đâu và trong bao lâu? | Bảng hoàn tiền nêu đúng phương thức thẻ tín dụng/ghi nợ và thời gian 7–14 ngày làm việc. | 0.8766 | Có | Tiền được hoàn về đúng tài khoản thẻ đã dùng để thanh toán trong 7–14 ngày làm việc, tùy ngân hàng. |
| 3 | Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào? | Mục hình ảnh sản phẩm nêu yêu cầu ảnh rõ, ảnh thật, tỷ lệ sản phẩm và ngôn ngữ phông nền. | 0.9432 | Có | Ảnh phải rõ và liên quan đến sản phẩm; có ít nhất một ảnh thật do người bán chụp, sản phẩm chiếm ít nhất 40% ảnh và ngôn ngữ trên phông nền là tiếng Việt. |
| 4 | Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào và những bằng chứng nào được Shopee khuyến khích? | Các chunk đầu chứa video đóng gói, vận đơn/hóa đơn và thời hạn cung cấp bằng chứng. | 0.9176 | Có | Trừ khi Shopee yêu cầu khác, bằng chứng cần được cung cấp trong 24 giờ; video đóng gói được khuyến khích và vận đơn/hóa đơn là bằng chứng vững chắc. |
| 5 | Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận? | Điều 11.2(a) mô tả việc chuyển tiền cho người bán và điều chỉnh khoản thanh toán nếu yêu cầu hoàn tiền được chấp thuận. | 0.9287 | Có | Shopee chuyển tiền từ Tài khoản Đảm bảo sang Số dư của người bán; nếu yêu cầu trả hàng/hoàn tiền sau đó được chấp thuận trong thời hạn, Shopee có thể điều chỉnh khoản tiền để hoàn cho người mua. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

Chiến thuật sử dụng: ParagraphWindowChunker với kích thước 650 ký tự và overlap 1 đoạn, bổ sung title/category/customer_role khi embedding, lọc role theo ngữ nghĩa bao gồm `both`, sau đó rerank bằng 55% dense similarity và 45% BM25. Kết quả chi tiết được lưu trong `bench_results.json`.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 10/ 10 |
| Hoàn thiện code (Core Implementation — tests) | 30/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **/ 60** |
