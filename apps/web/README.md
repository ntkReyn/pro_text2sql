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

## Chạy local

Từ repository root:

```powershell
cd apps/web
npm install
npm run dev
```

Mở `http://localhost:3000`.

Build production:

```powershell
npm run build
npm run start
```

Kiểm tra TypeScript độc lập:

```powershell
npm run typecheck
```
