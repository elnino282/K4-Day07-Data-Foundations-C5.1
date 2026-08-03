# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Chunk/nguồn chứa thông tin |
|---|-----------------|-----------------|--------------------------------|-----------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền đối với hàng thông thường và thực phẩm tươi sống hoặc đông lạnh? | `{"customer_role": "buyer"}` | Hàng thông thường là 15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công; thực phẩm tươi sống hoặc đông lạnh là 24 giờ. Sau thời hạn này, Shopee vẫn có thể xem xét hỗ trợ trong phạm vi phù hợp với chính sách. | `shopee-buyer-return-refund-policy.md`, Điều 3.2 |
| 2 | Tiền hoàn của đơn thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ được hoàn về đâu và trong bao lâu? | `{"customer_role": "buyer"}` | Tiền được hoàn về đúng tài khoản thẻ tín dụng hoặc thẻ ghi nợ đã dùng để thanh toán đơn hàng trong vòng 7–14 ngày làm việc, tùy theo ngân hàng. | `shopee-buyer-refund-timeline.md`, bảng thời gian hoàn tiền và phần lưu ý |
| 3 | Hình ảnh sản phẩm đăng bán trên Shopee phải đáp ứng những yêu cầu cơ bản nào? | `{"customer_role": "seller"}` | Hình ảnh phải rõ và thể hiện chi tiết tình trạng sản phẩm, không chứa thông tin không liên quan. Phải có ít nhất một ảnh thật do người bán tự chụp, trong đó sản phẩm chiếm ít nhất 40% diện tích toàn ảnh; ngôn ngữ trên phông nền phải là tiếng Việt. | `shopee-seller-listing-rules.md`, mục Hình ảnh sản phẩm |
| 4 | Người bán phải cung cấp bằng chứng khiếu nại vận chuyển trong thời hạn nào và những bằng chứng nào được Shopee khuyến khích? | `{"customer_role": "seller"}` | Trừ khi Shopee có yêu cầu khác, bằng chứng phải được cung cấp trong vòng 24 giờ kể từ khi gửi khiếu nại hoặc nhận yêu cầu từ Shopee. Video quá trình đóng gói được khuyến khích là bằng chứng mạnh; vận đơn hoặc hóa đơn vận chuyển là bằng chứng vững chắc chứng minh người bán đã giao hàng. | `shopee-seller-shipping-fulfillment-policy.md`, mục Bằng chứng khiếu nại |
| 5 | Khi người mua xác nhận đã nhận hàng, Shopee xử lý khoản tiền thanh toán như thế nào nếu sau đó yêu cầu trả hàng/hoàn tiền được chấp thuận? | `{"customer_role": "both"}` | Shopee ban đầu chuyển tiền từ Tài khoản Đảm bảo Shopee sang Số dư tài khoản Shopee của người bán. Nếu thời gian trả hàng/hoàn tiền vẫn chưa kết thúc và yêu cầu sau đó được chấp thuận, Shopee có quyền điều chỉnh khoản tiền thanh toán để hoàn tiền cho người mua. | `shopee-terms-of-service-vn.md`, Điều 11.2(a) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
