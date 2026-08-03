# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hồ Ngọc Quỳnh  
**Mã sinh viên:** 2A202601684
**Nhóm:** C5.1  
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao cho thấy hai vector embedding có hướng gần nhau, nghĩa là hai đoạn văn bản có nội dung hoặc ý nghĩa ngữ nghĩa tương đồng. Hai câu không cần dùng đúng cùng từ ngữ nhưng vẫn có thể đạt điểm cao nếu cùng diễn đạt một ý.

**Ví dụ có độ tương tự CAO:**
- Câu A: Shopee hỗ trợ thanh toán qua ShopeePay.
- Câu B: Người dùng có thể trả tiền bằng ví điện tử trên Shopee.
- Tại sao tương đồng: Cả hai câu đều nói về việc thanh toán trên Shopee bằng ví điện tử ShopeePay.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Shopee bảo vệ người mua khỏi hàng giả.
- Câu B: Hôm nay trời Hà Nội nhiều mây có mưa.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, một câu nói về chính sách thương mại điện tử và một câu nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector nên phản ánh tốt mức độ giống nhau về ngữ nghĩa, ít bị ảnh hưởng bởi độ lớn của vector. Khoảng cách Euclid phụ thuộc cả hướng và độ lớn, vì vậy có thể đánh giá hai vector có cùng ý nghĩa là khác nhau chỉ do độ dài vector khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*  
> Số lượng chunk = `ceil((10000 - 50) / (500 - 50))`  
> = `ceil(9950 / 450)`  
> = `ceil(22.11)`  
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk là `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks`. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa hai chunk, hạn chế việc một ý hoặc điều kiện quan trọng bị chia tách, nhưng làm tăng số lượng chunk và chi phí embedding/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách văn bản theo ranh giới câu bằng biểu thức chính quy nhận diện dấu kết thúc câu như `.`, `!`, `?` và khoảng trắng phía sau, sau đó ghép lần lượt các câu vào chunk cho đến khi gần đạt `chunk_size`. Các trường hợp văn bản rỗng, câu dài hơn kích thước chunk và phần nội dung cuối không có dấu kết thúc câu được xử lý để không làm mất dữ liệu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán lần lượt thử các separator từ mức cấu trúc lớn đến nhỏ, ví dụ đoạn văn, xuống dòng, câu, khoảng trắng và cuối cùng là ký tự. Nếu một đoạn vẫn lớn hơn `chunk_size`, hàm `_split` tiếp tục gọi đệ quy với separator tiếp theo; base case là khi đoạn đã đủ nhỏ hoặc không còn separator, lúc đó cắt trực tiếp theo kích thước cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` tạo embedding cho từng `Document`, sau đó lưu nội dung, vector và metadata tương ứng trong store. Khi tìm kiếm, truy vấn được embedding bằng cùng một hàm, rồi tính điểm tương tự bằng dot product/cosine trên các vector đã chuẩn hóa và sắp xếp giảm dần để trả về top-k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` giới hạn tập ứng viên theo các điều kiện metadata trước khi xếp hạng tương tự, nhờ đó tránh trả về tài liệu sai vai trò hoặc sai danh mục. `delete_document` tìm tất cả chunk có cùng `doc_id` trong metadata và xóa đồng bộ nội dung, embedding và metadata của các chunk đó khỏi store.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` trước tiên truy xuất các chunk liên quan nhất từ `EmbeddingStore`, sau đó ghép chúng thành phần ngữ cảnh có đánh số hoặc phân tách rõ ràng. Prompt yêu cầu LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp, không tự suy diễn khi thiếu dữ liệu và đưa câu hỏi của người dùng ở cuối để mô hình tạo câu trả lời có căn cứ.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Quynh Ho\Documents\GitHub\K4-Day07-Data-Foundations
plugins: anyio-4.14.2
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.17s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Quy ước đánh giá sử dụng trong phần này: điểm cosine similarity từ **0.50 trở lên** được xem là tương tự cao; dưới **0.50** được xem là tương tự thấp.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hỗ trợ thanh toán qua ShopeePay. | Người dùng có thể trả tiền bằng ví điện tử trên Shopee. | cao | 0.8072 | Đúng |
| 2 | Chính sách đổi trả hàng trong 15 ngày. | Thời hạn hoàn tiền là hai tuần kể từ ngày nhận hàng. | cao | 0.4475 | Sai |
| 3 | Shopee bảo vệ người mua khỏi hàng giả. | Hôm nay trời Hà Nội nhiều mây có mưa. | thấp | -0.1068 | Đúng |
| 4 | Người bán cần xác minh danh tính để đăng sản phẩm. | Nhà bán hàng phải hoàn tất KYC trước khi niêm yết. | cao | 0.3813 | Sai |
| 5 | Điều khoản dịch vụ Shopee áp dụng theo luật Việt Nam. | Shopee cấm bán hàng giả, hàng nhái trên nền tảng. | thấp | 0.2969 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 4 chỉ đạt 0.3813 dù hai câu gần như cùng nói về việc người bán phải xác minh danh tính trước khi đăng bán. Điều này cho thấy embedding không chỉ dựa vào ý nghĩa con người nhận thấy mà còn chịu ảnh hưởng bởi cách dùng từ, từ viết tắt như “KYC”, dữ liệu huấn luyện và khả năng biểu diễn tiếng Việt của mô hình.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Lưu ý:** Cột điểm score cần lấy trực tiếp từ output chạy trên máy cá nhân. Không nên tự điền số ước lượng vì điểm phụ thuộc vào model embedding, dữ liệu đã ingest và chiến lược chunking.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với hàng thông thường và thực phẩm tươi sống hoặc đông lạnh? | Điều 3.2 nêu thời hạn 15 ngày đối với hàng thông thường và 24 giờ đối với thực phẩm tươi sống hoặc đông lạnh. | 0.9440 | Có | Hàng thông thường có thời hạn 15 ngày, thực phẩm tươi sống hoặc đông lạnh có thời hạn 24 giờ; trường hợp quá hạn vẫn có thể được Shopee xem xét hỗ trợ. |
| 2 | Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ được hoàn về đâu và trong bao lâu? | Bảng hoàn tiền nêu đúng phương thức thẻ tín dụng/ghi nợ và thời gian 7–14 ngày làm việc. | 0.8766 | Có | Tiền được hoàn về đúng tài khoản thẻ đã dùng để thanh toán trong 7–14 ngày làm việc, tùy ngân hàng. |
| 3 | Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào? | Mục hình ảnh sản phẩm nêu yêu cầu ảnh rõ, ảnh thật, tỷ lệ sản phẩm và ngôn ngữ phông nền. | 0.9432 | Có | Ảnh phải rõ và liên quan đến sản phẩm; có ít nhất một ảnh thật do người bán chụp, sản phẩm chiếm ít nhất 40% ảnh và ngôn ngữ trên phông nền là tiếng Việt. |
| 4 | Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào và những bằng chứng nào được Shopee khuyến khích? | Các chunk đầu chứa video đóng gói, vận đơn/hóa đơn và thời hạn cung cấp bằng chứng. | 0.9176 | Có | Trừ khi Shopee yêu cầu khác, bằng chứng cần được cung cấp trong 24 giờ; video đóng gói được khuyến khích và vận đơn/hóa đơn là bằng chứng vững chắc. |
| 5 | Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận? | Điều 11.2(a) mô tả việc chuyển tiền cho người bán và điều chỉnh khoản thanh toán nếu yêu cầu hoàn tiền được chấp thuận. | 0.9287 | Có | Shopee chuyển tiền từ Tài khoản Đảm bảo sang Số dư của người bán; nếu yêu cầu trả hàng/hoàn tiền sau đó được chấp thuận trong thời hạn, Shopee có thể điều chỉnh khoản tiền để hoàn cho người mua. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng không có một chiến lược chunking duy nhất tốt cho mọi loại câu hỏi. Việc giữ cấu trúc tiêu đề, chọn kích thước chunk phù hợp và dùng metadata để giới hạn đúng vai trò người mua/người bán có thể cải thiện chất lượng truy xuất rõ rệt hơn so với chỉ tăng số lượng chunk.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
