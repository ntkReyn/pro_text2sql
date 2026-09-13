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
