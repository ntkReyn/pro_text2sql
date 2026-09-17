# Web application — Frontend

Frontend cho sản phẩm analytics: nhập câu hỏi, hiển thị câu trả lời, bảng dữ liệu, biểu đồ, evidence, clarification prompt và lịch sử hội thoại.

```text
apps/web/
├── public/                    # Static assets, favicon, logo
└── src/
    ├── app/                   # App shell, routes, providers, layout
    ├── components/            # UI component dùng chung
    ├── features/
    │   ├── query/             # Query input, loading, result, SQL/evidence
    │   ├── conversations/     # Session và follow-up question
    │   └── visualizations/    # Chart/table/metric cards
    ├── lib/
    │   ├── api/               # API client và response mapper
    │   └── auth/              # Authentication/session client
    ├── state/                 # Client state và query state
    ├── styles/                # Theme, global style, design tokens
    └── types/                 # Type dùng chung phía frontend
```

Frontend chỉ chịu trách nhiệm trình bày và tương tác. Metric, business rule và SQL policy phải nằm ở backend/semantic layer, không đặt trong UI.

## Trạng thái triển khai

Frontend hiện dùng Next.js App Router, React, TypeScript, Tailwind CSS và Framer Motion. Route mặc định mở dashboard tại `#/dashboard`.

Chuyển cảnh giữa các màn hình dùng một motion wrapper chung với hiệu ứng nâng nhẹ, đồng thời tự tắt animation khi thiết bị bật chế độ giảm chuyển động.

Các màn hình đã có:

- Dashboard và điều hướng riêng cho 5 role: Workspace Admin, Metric Steward, Data Analyst, Business User và Auditor;
- workspace Cuộc trò chuyện với trạng thái xử lý, kết quả và evidence;
- thư viện metric;
- đánh giá/audit;
- đăng nhập theo role và đăng ký có chọn role mong muốn ở chế độ frontend demo;
- màn hình chặn truy cập khi mở route ngoài phạm vi role.

Authentication chưa kết nối backend hoặc identity provider. Form demo không gửi credential ra ngoài. Role được lưu trong `sessionStorage` chỉ để trình diễn UI; bản production phải lấy role/data scope từ session do backend xác thực và kiểm tra quyền ở server. Role chọn khi đăng ký là yêu cầu chờ Workspace Admin phê duyệt, không phải cơ chế tự cấp quyền.

Màn `Cuộc trò chuyện` nối vào Wren-first FastAPI route qua Next.js route
`/api/wren`. Câu hỏi được dùng để lấy MDL/knowledge context, sinh SQL theo Wren
model, chạy Wren embedded `dry_plan` và qua SQL policy. Execution vẫn tắt mặc định
nên UI không dựng một con số giả. SQL
chỉ được render cho role Data Analyst và Metric Steward trong demo; đây chưa phải
authorization enforcement phía server.

## Chạy local

Sau khi đã tạo `.venv-app` và cấu hình `.env`:

```powershell
cd apps/web
npm install
npm run dev
```

`npm run dev` khởi động FastAPI với Wren embedded tại `127.0.0.1:8000`, rồi mới
khởi động Next.js tại cổng `3000`. Nhấn `Ctrl+C` một lần để dừng cả hai.

Mở `http://localhost:3000`.

Next.js proxy mặc định gọi `http://localhost:8000`. Có thể đổi bằng biến server-side `ANALYTICS_API_BASE_URL`.

Nếu `/api/wren` báo backend thiếu endpoint, hãy dừng tiến trình API cũ và chạy
đúng entrypoint từ repository root. Uvicorn không có `--reload` sẽ không tự nhận
route mới sau khi source thay đổi:

```powershell
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Hydration warning có thuộc tính `bis_skin_checked` hoặc `bis_register` là do browser
extension chèn DOM trước khi React hydrate. Kiểm tra bằng cửa sổ Incognito không bật
extension hoặc tắt extension đó cho `localhost`; không thêm suppression vào component
để che lỗi DOM thật.

Build production:

```powershell
npm run build
npm run start
```

Kiểm tra TypeScript độc lập:

```powershell
npm run typecheck
```
