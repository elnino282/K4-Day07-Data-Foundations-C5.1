# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Văn Huy  
**Mã sinh viên:** 2A202601356  
**Nhóm:** K4  
**Ngày:** 03/08/2026

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) - Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity)

**Độ tương tự cosine cao nghĩa là gì?**  
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, tức hai đoạn văn bản thường có nội dung hoặc ý nghĩa gần nhau. Với văn bản, điều này cho thấy hệ thống có thể xem hai câu là liên quan về mặt ngữ nghĩa dù không dùng đúng cùng một từ.

**Ví dụ có độ tương tự cao:**
- Câu A: Shopee hỗ trợ thanh toán bằng ví ShopeePay.
- Câu B: Người mua có thể trả tiền đơn hàng bằng Ví ShopeePay.
- Tại sao tương đồng: Hai câu đều nói về việc dùng ShopeePay để thanh toán đơn hàng.

**Ví dụ có độ tương tự thấp:**
- Câu A: Người bán phải chọn đúng danh mục ngành hàng.
- Câu B: Thời tiết hôm nay có mưa lớn ở Hà Nội.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, một câu nói về quy định đăng bán, câu còn lại nói về thời tiết.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào hướng của vector, nên phù hợp để so sánh ý nghĩa văn bản. Euclidean distance bị ảnh hưởng nhiều bởi độ lớn vector, trong khi với embedding văn bản, hướng thường quan trọng hơn độ dài tuyệt đối.

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**  
Công thức: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`.

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100 thì số lượng chunk thay đổi thế nào?**  
Khi `overlap=100`, số chunk là `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`. Số chunk tăng vì mỗi lần trượt chỉ đi thêm 400 ký tự thay vì 450 ký tự. Tăng overlap giúp giữ thêm ngữ cảnh ở ranh giới giữa hai chunk, giảm nguy cơ tách mất ý quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) - Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` - hướng tiếp cận:**  
Tôi dùng regex `(?<=[.!?])(?:\s+|$)` để tách văn bản tại vị trí sau các dấu kết thúc câu như `.`, `!`, `?`, sau đó loại bỏ khoảng trắng thừa. Các câu được gom lại theo `max_sentences_per_chunk`, đồng thời xử lý trường hợp văn bản rỗng hoặc chỉ có khoảng trắng bằng cách trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split` - hướng tiếp cận:**  
Thuật toán thử tách văn bản theo thứ tự separator ưu tiên: đoạn văn, dòng, câu, từ, rồi cuối cùng là ký tự. Base case là khi đoạn hiện tại đã nhỏ hơn hoặc bằng `chunk_size`, lúc đó chỉ cần strip và trả về. Nếu một segment vẫn quá dài, hàm gọi đệ quy với separator tiếp theo để chia nhỏ hơn.

### Lớp EmbeddingStore

**`add_documents` + `search` - hướng tiếp cận:**  
Mỗi `Document` được chuyển thành một record gồm `id`, `content`, `metadata` và `embedding`. Nếu ChromaDB dùng được thì store sẽ thêm dữ liệu vào collection, còn nếu không thì lưu trong bộ nhớ bằng list. Khi search, tôi embed câu truy vấn rồi tính dot product với embedding của từng record, sau đó sắp xếp giảm dần theo score.

**`search_with_filter` + `delete_document` - hướng tiếp cận:**  
Tôi lọc metadata trước khi tính similarity để chỉ tìm trong các chunk phù hợp, ví dụ lọc `customer_role=seller` cho câu hỏi về người bán. Hàm `delete_document` tìm tất cả record có `metadata["doc_id"]` trùng với document cần xóa, xóa khỏi bộ nhớ và nếu đang dùng ChromaDB thì gọi thêm `collection.delete()`.

### Tác tử KnowledgeBaseAgent

**`answer` - hướng tiếp cận:**  
Agent lấy top-k chunk liên quan từ `EmbeddingStore`, ghép các chunk thành phần `Context`, rồi tạo prompt yêu cầu LLM trả lời chỉ dựa trên ngữ cảnh đó. Nếu không retrieve được context, prompt sẽ ghi rõ là không có ngữ cảnh liên quan để hạn chế việc trả lời bịa.

---

## 3. Hoàn thiện code (Core Implementation) - Cá nhân (30 điểm)

### Kết Quả Kiểm Thử

Lệnh đã chạy:

```bash
pytest tests/ -v
```

Kết quả tóm tắt:

```text
collected 42 items
42 passed in 0.18s
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) - Cá nhân (5 điểm)

Các điểm dưới đây được chạy bằng mock embedder mặc định của lab. Mock embedder dùng để kiểm thử tính xác định, không phản ánh đầy đủ chất lượng ngữ nghĩa tiếng Việt.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hỗ trợ thanh toán bằng ví ShopeePay. | Người mua có thể trả tiền bằng Ví ShopeePay. | cao | -0.2191 | Không |
| 2 | Hoàn tiền qua thẻ tín dụng mất 7 đến 14 ngày làm việc. | Tiền hoàn về thẻ ghi nợ thường cần vài ngày làm việc. | cao | 0.1228 | Có |
| 3 | Người bán phải chọn đúng danh mục ngành hàng. | Thời tiết hôm nay có mưa lớn ở Hà Nội. | thấp | -0.0668 | Có |
| 4 | Chính sách bảo mật mô tả cách Shopee xử lý dữ liệu cá nhân. | Quy định đăng bán yêu cầu hình ảnh sản phẩm rõ ràng. | thấp | -0.2030 | Có |
| 5 | Apple Pay không áp dụng cho một số đơn hàng ShopeeFood. | Google Pay không áp dụng cho đơn hàng ShopeeFood. | cao | -0.0126 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**  
Cặp 1 và cặp 5 khá bất ngờ vì nội dung rất gần nhau nhưng điểm thực tế lại âm. Điều này cho thấy mock embedder trong lab không thật sự hiểu ngữ nghĩa, mà chủ yếu tạo vector xác định để phục vụ unit test. Khi đánh giá retrieval thật, nên dùng local multilingual embedder hoặc OpenAI embedder để kết quả có ý nghĩa hơn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) - Cá nhân (10 điểm)

Chiến lược cá nhân tôi chọn: `RecursiveChunker(chunk_size=700)`. Lý do chọn là dữ liệu chính sách Shopee có nhiều tiêu đề, đoạn, danh sách và điều khoản; cách tách đệ quy giúp ưu tiên giữ nguyên đoạn văn trước khi phải tách nhỏ theo câu hoặc từ.

Dữ liệu dùng thử: `data/k4_ecommerce`. Embedding dùng thử: mock embedder mặc định. Vì vậy score dưới đây chỉ mang tính tham khảo kỹ thuật, không phải kết luận cuối về chất lượng ngữ nghĩa.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Shopee hỗ trợ những phương thức thanh toán nào? | `shopee-buyer-return-refund-policy::chunk_1` - phần phạm vi/chính sách trả hàng hoàn tiền | 0.4434 | Không | Context top-1 chưa đúng; câu trả lời nên dựa vào tài liệu payment-methods, gồm ShopeePay, thẻ, trả góp, QR, app ngân hàng, NAPAS, Apple Pay, Google Pay, COD, SPayLater. |
| 2 | Hoàn tiền về thẻ tín dụng hoặc thẻ ghi nợ mất bao lâu? | `shopee-privacy-policy-vn::chunk_50` - phần chính sách bảo mật | 0.3581 | Không | Context top-1 chưa đúng; câu trả lời chuẩn là hoàn về thẻ tín dụng/ghi nợ trong khoảng 7-14 ngày làm việc tùy ngân hàng. |
| 3 | Người bán cần lưu ý gì khi đặt tên sản phẩm? | `shopee-seller-shipping-fulfillment-policy::chunk_14`, top-3 có `shopee-seller-listing-rules` | 0.2825 | Có trong top-3 | Tên sản phẩm cần mô tả đúng hàng hóa, là tiếng Việt có dấu, rõ nghĩa, không dùng ký tự đặc biệt/viết tắt và không chứa từ khóa fake/nhái. |
| 4 | Người bán có được đăng sản phẩm cấm hoặc hạn chế không? | `shopee-seller-shipping-fulfillment-policy::chunk_31`, top-3 có `shopee-seller-prohibited-restricted-products` | 0.3314 | Có trong top-3 | Người bán không được đăng sản phẩm thuộc danh sách cấm/hạn chế hoặc nội dung vi phạm quy định Shopee/pháp luật. |
| 5 | Chính sách bảo mật nói gì về việc Shopee xử lý dữ liệu cá nhân? | `shopee-privacy-policy-vn::chunk_24` - phần chính sách bảo mật | 0.3456 | Có | Shopee xử lý dữ liệu cá nhân theo chính sách bảo mật, phục vụ cung cấp dịch vụ, quản lý tài khoản/giao dịch và các mục đích được nêu trong chính sách. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:**  
Cùng một bộ tài liệu nhưng chiến lược chunking và metadata có thể làm kết quả retrieval khác nhau rất nhiều. Với dữ liệu chính sách dài, metadata như `customer_role` và `category` giúp thu hẹp phạm vi tìm kiếm tốt hơn, đặc biệt khi câu hỏi chỉ dành cho người bán hoặc người mua.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation - tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
