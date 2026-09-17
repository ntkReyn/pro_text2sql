import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const apiBaseUrl = (
  process.env.ANALYTICS_API_BASE_URL
  ?? process.env.PUBLIC_API_BASE_URL
  ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");

export async function POST(request: NextRequest) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ detail: "Request body phải là JSON hợp lệ." }, { status: 400 });
  }

  const question = (payload as { question?: unknown })?.question;
  if (typeof question !== "string" || !question.trim()) {
    return NextResponse.json({ detail: "Câu hỏi không được để trống." }, { status: 422 });
  }

  try {
    const upstream = await fetch(`${apiBaseUrl}/api/v1/query/wren`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: question.trim() }),
      cache: "no-store",
      signal: AbortSignal.timeout(65_000),
    });
    const responseText = await upstream.text();
    let body: unknown;
    try {
      body = JSON.parse(responseText);
    } catch {
      body = { detail: responseText || `Analytics API trả HTTP ${upstream.status}.` };
    }

    if (upstream.status === 404) {
      return NextResponse.json(
        {
          detail: "Analytics API đang chạy nhưng thiếu POST /api/v1/query/wren. Hãy khởi động lại npm run dev từ repository root.",
        },
        { status: 502 },
      );
    }

    return NextResponse.json(body, { status: upstream.status });
  } catch {
    return NextResponse.json(
      {
        detail: "Không kết nối được Wren-first Analytics API. Hãy kiểm tra backend tại localhost:8000.",
      },
      { status: 502 },
    );
  }
}
