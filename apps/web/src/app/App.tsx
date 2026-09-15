import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft, ArrowRight, Bell, BookOpen, Bot, Check, CheckCircle2,
  ChevronDown, CircleHelp, Clock3, Code2, Database, Eye, EyeOff,
  Gauge, KeyRound, LayoutDashboard, LoaderCircle, LockKeyhole, Mail,
  MessageSquareText, PackageCheck, Search, SendHorizontal, ShieldCheck,
  Sparkles, TableProperties, TriangleAlert, TrendingDown, TrendingUp,
  User, UsersRound,
} from "lucide-react";

type Period = "7" | "30" | "90";
type View = "dashboard" | "query" | "conversations" | "metrics" | "audit" | "login" | "register";

const periodData: Record<Period, { values: number[]; labels: string[] }> = {
  "7": { values: [91, 93, 92, 95, 94, 96, 96.4], labels: ["T2", "T3", "T4", "T5", "T6", "T7", "CN"] },
  "30": { values: [89, 91, 90, 93, 92, 94, 95, 94, 96, 96.4], labels: ["16/08", "19/08", "22/08", "25/08", "28/08", "31/08", "03/09", "06/09", "10/09", "14/09"] },
  "90": { values: [84, 86, 85, 88, 89, 91, 90, 92, 94, 95, 96.4], labels: ["T6", "", "", "T7", "", "", "T8", "", "", "", "T9"] },
};

const navItems: Array<{ id: View; label: string; icon: typeof LayoutDashboard }> = [
  { id: "dashboard", label: "Tổng quan", icon: LayoutDashboard },
  { id: "query", label: "Hỏi dữ liệu", icon: Sparkles },
  { id: "conversations", label: "Cuộc hội thoại", icon: MessageSquareText },
  { id: "metrics", label: "Thư viện metric", icon: BookOpen },
  { id: "audit", label: "Đánh giá & audit", icon: ShieldCheck },
];

const alerts = [
  ["Vina Components", "Tỷ lệ giao trễ tăng 4,8 điểm", "43 / 231 đơn · 90 ngày", "danger"],
  ["Kho Hà Nội", "12 SKU dưới reorder point", "Cập nhật 18 phút trước", "warning"],
  ["Pacific Parts", "Độ đúng hạn cải thiện liên tục", "+6,2 điểm so với quý trước", "positive"],
];

const suppliers = [
  ["Vina Components", "18,6%", "43 / 231"], ["Eastbridge", "15,8%", "31 / 196"],
  ["Pacific Parts", "13,2%", "27 / 204"], ["Mekong Supply", "11,0%", "19 / 173"],
  ["Northstar", "8,9%", "16 / 180"],
];

function go(view: View) { window.location.hash = `/${view}`; }

function currentView(): View {
  const value = window.location.hash.replace(/^#\//, "") as View;
  return ["dashboard", "query", "conversations", "metrics", "audit", "login", "register"].includes(value) ? value : "dashboard";
}

function makeLine(values: number[]) {
  return values.map((value, index) => {
    const x = (index / (values.length - 1)) * 700;
    const y = 210 - ((value - 80) / 20) * 210;
    return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function BrandMark() { return <span className="brand-mark" aria-hidden="true"><span /></span>; }

function ProductShell({ view, children }: { view: View; children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand-lockup brand-button" type="button" onClick={() => go("dashboard")}>
          <BrandMark /><span><strong>AtlasIQ</strong><small>Semantic analytics</small></span>
        </button>
        <button className="workspace-switcher" type="button">
          <span className="workspace-avatar">VN</span><span><small>Workspace</small><strong>Vietnam Operations</strong></span><ChevronDown />
        </button>
        <nav className="primary-nav" aria-label="Điều hướng chính">
          {navItems.map((item) => {
            const Icon = item.icon;
            return <button className={view === item.id ? "active" : ""} type="button" key={item.id} onClick={() => go(item.id)}><Icon /><span>{item.label}</span></button>;
          })}
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-trust"><span className="trust-icon"><ShieldCheck /></span><div><strong>Dữ liệu được bảo vệ</strong><span>Quyền truy cập đang hoạt động</span></div></div>
        <button className="profile-button" type="button" onClick={() => go("login")}><span className="profile-avatar">MA</span><span><strong>Minh Anh</strong><small>Supply Chain Lead</small></span><ChevronDown /></button>
      </aside>
      <main className="main-surface">
        <header className="topbar">
          <label className="global-search"><Search /><input type="search" placeholder="Tìm metric, hội thoại hoặc câu hỏi…" aria-label="Tìm kiếm" /><kbd>Ctrl K</kbd></label>
          <div className="topbar-actions"><span className="freshness-status"><span /> Dữ liệu mới · 08:35</span><button className="icon-button" type="button" aria-label="Trợ giúp"><CircleHelp /></button><button className="icon-button notification-button" type="button" aria-label="Thông báo"><Bell /><span /></button></div>
        </header>
        {children}
      </main>
    </div>
  );
}

function Dashboard() {
  const [period, setPeriod] = useState<Period>("30");
  const chart = periodData[period];
  const line = useMemo(() => makeLine(chart.values), [chart.values]);
  const lastY = 210 - ((chart.values.at(-1)! - 80) / 20) * 210;

  return (
    <div className="dashboard-wrap content-view">
      <section className="dashboard-heading">
        <div><span className="eyebrow">Thứ Hai · 14 tháng 9</span><h1>Tổng quan vận hành</h1><p>Tập trung vào những thay đổi cần quyết định hôm nay.</p></div>
        <button className="primary-button" type="button" onClick={() => go("query")}><Sparkles />Đặt câu hỏi mới<ArrowRight /></button>
      </section>
      <section className="metric-grid" aria-label="Chỉ số chính">
        <MetricCard featured icon={<PackageCheck />} label="Tỷ lệ giao đúng hạn" value="96,4%" footer={<><TrendingUp />+2,1 điểm <span>so với kỳ trước</span></>} />
        <MetricCard icon={<Clock3 />} tone="warm" label="Đơn hàng giao trễ" value="128" footer={<><TrendingDown />−18 đơn <span>trong 30 ngày</span></>} />
        <MetricCard icon={<TriangleAlert />} tone="danger" label="Supplier cần chú ý" value="07" footer={<><TrendingUp />+2 supplier <span>vượt ngưỡng</span></>} negative />
        <MetricCard icon={<Gauge />} tone="blue" label="Metric đang theo dõi" value="24" footer={<><Check />100% hợp lệ <span>theo catalog v1.2</span></>} neutral />
      </section>
      <section className="dashboard-grid primary-row">
        <article className="panel performance-panel">
          <div className="panel-heading"><div><span className="panel-kicker">Hiệu suất giao hàng</span><h2>Xu hướng giao đúng hạn</h2></div><div className="period-control">{(["7", "30", "90"] as Period[]).map((item) => <button key={item} type="button" className={period === item ? "active" : ""} onClick={() => setPeriod(item)}>{item} ngày</button>)}</div></div>
          <div className="chart-summary"><strong>96,4%</strong><span><TrendingUp /> Tăng 2,1 điểm</span></div>
          <div className="line-chart" role="img" aria-label={`Biểu đồ tỷ lệ giao đúng hạn trong ${period} ngày`}>
            <div className="y-axis"><span>100%</span><span>95%</span><span>90%</span><span>85%</span><span>80%</span></div>
            <svg viewBox="0 0 700 230" preserveAspectRatio="none" aria-hidden="true">
              <defs><linearGradient id="area-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--brand-indigo)" stopOpacity=".24" /><stop offset="100%" stopColor="var(--brand-indigo)" stopOpacity="0" /></linearGradient><linearGradient id="line-stroke" x1="0" x2="1"><stop offset="0%" stopColor="var(--brand-indigo)" /><stop offset="100%" stopColor="var(--brand-teal)" /></linearGradient></defs>
              <g className="chart-grid-lines">{[0, 52.5, 105, 157.5, 210].map((y) => <line key={y} x1="0" y1={y} x2="700" y2={y} />)}</g>
              <path className="area-path" d={`${line} L700,210 L0,210 Z`} /><path className="line-path" d={line} /><circle className="last-point-ring" cx="700" cy={lastY} r="9" /><circle className="last-point" cx="700" cy={lastY} r="4" />
            </svg>
            <div className="x-axis">{chart.labels.map((label, i) => <span key={`${label}-${i}`}>{label}</span>)}</div>
          </div>
        </article>
        <article className="panel attention-panel">
          <div className="panel-heading"><div><span className="panel-kicker">Ưu tiên hôm nay</span><h2>Cần bạn chú ý</h2></div><span className="count-badge">3</span></div>
          <div className="attention-list">{alerts.map(([title, detail, meta, tone]) => <button className="attention-item" type="button" key={title} onClick={() => go("query")}><span className={`attention-dot ${tone}`} /><span className="attention-copy"><strong>{title}</strong><span>{detail}</span><small>{meta}</small></span><ArrowRight /></button>)}</div>
          <button className="panel-link" type="button" onClick={() => go("audit")}>Xem toàn bộ cảnh báo <ArrowRight /></button>
        </article>
      </section>
      <section className="dashboard-grid secondary-row">
        <article className="panel query-panel"><div className="panel-heading"><div><span className="panel-kicker">Bắt đầu nhanh</span><h2>Hỏi dữ liệu của bạn</h2></div><Bot /></div><p>Đặt câu hỏi tự nhiên, hệ thống sẽ dùng metric đã phê duyệt và trả kết quả có bằng chứng.</p><button className="ask-box" type="button" onClick={() => go("query")}><span>Ví dụ: Supplier nào có tỷ lệ giao trễ cao nhất?</span><span className="ask-action"><Sparkles />Hỏi ngay</span></button></article>
        <article className="panel coverage-panel"><div className="panel-heading"><div><span className="panel-kicker">Phạm vi dữ liệu</span><h2>Độ phủ hiện tại</h2></div><UsersRound /></div><Coverage label="Supplier performance" value="100%" /><Coverage label="Inventory status" value="68%" /></article>
      </section>
    </div>
  );
}

function MetricCard({ featured, icon, tone = "", label, value, footer, negative, neutral }: { featured?: boolean; icon: ReactNode; tone?: string; label: string; value: string; footer: ReactNode; negative?: boolean; neutral?: boolean }) {
  return <article className={`metric-card ${featured ? "featured" : ""}`}><div className="metric-card-head"><span>{label}</span><span className={`metric-icon ${tone}`}>{icon}</span></div><strong className="metric-value">{value}</strong><div className={`metric-foot ${negative ? "negative" : neutral ? "neutral" : "positive"}`}>{footer}</div></article>;
}

function Coverage({ label, value }: { label: string; value: string }) {
  return <><div className="coverage-row"><span>{label}</span><strong>{value}</strong></div><div className="coverage-track"><span style={{ width: value }} /></div></>;
}

function QueryWorkspace() {
  const [question, setQuestion] = useState("Top 5 nhà cung cấp có tỷ lệ giao hàng trễ cao nhất trong 90 ngày gần đây?");
  const [stage, setStage] = useState(-1);
  const [complete, setComplete] = useState(true);

  function submit(event: FormEvent) { event.preventDefault(); if (!question.trim() || stage >= 0) return; setComplete(false); setStage(0); }
  useEffect(() => {
    if (stage < 0) return;
    const timer = window.setTimeout(() => stage < 3 ? setStage(stage + 1) : (setStage(-1), setComplete(true)), stage < 3 ? 470 : 560);
    return () => window.clearTimeout(timer);
  }, [stage]);

  return (
    <div className="workspace-wrap content-view">
      <section className="workspace-heading"><span className="eyebrow">Phân tích có kiểm chứng</span><h1>Hỏi dữ liệu</h1><p>Đặt câu hỏi tự nhiên và theo dõi cách AtlasIQ kiểm tra câu trả lời.</p></section>
      <form className="query-composer-large" onSubmit={submit}>
        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} aria-label="Câu hỏi phân tích" />
        <div className="query-composer-foot"><div className="suggestion-row">{["So sánh theo khu vực", "Xem xu hướng theo tuần", "So với quý trước"].map((text) => <button type="button" key={text} onClick={() => setQuestion(text)}>{text}</button>)}</div><button className="primary-button" type="submit" disabled={stage >= 0}>{stage >= 0 ? <LoaderCircle className="spin" /> : <SendHorizontal />}{stage >= 0 ? "Đang phân tích" : "Phân tích"}</button></div>
        <div className={`stage-progress ${stage >= 0 ? "visible" : ""}`} aria-live="polite">{["Hiểu câu hỏi", "Kiểm tra metric", "Tạo truy vấn", "Xác minh kết quả"].map((text, i) => <span key={text} className={stage > i ? "done" : stage === i ? "current" : ""}><Check />{text}</span>)}</div>
      </form>
      <section className={`query-result-layout ${complete ? "ready" : "loading"}`} aria-live="polite">
        <article className="panel result-panel-large">
          <div className="result-heading"><div><span>Kết quả · 90 ngày gần đây</span><h2>Nhà cung cấp có tỷ lệ giao hàng trễ cao nhất</h2></div><span className="verified-label"><ShieldCheck />Đã xác minh</span></div>
          <div className="result-highlight"><strong>18,6%</strong><span>Vina Components · 43 / 231 đơn hàng</span></div>
          <div className="supplier-bars">{suppliers.map(([name, value, sample], i) => <div className="supplier-bar" key={name}><span>{i + 1}</span><strong>{name}</strong><span className="bar-track"><span style={{ width: `${100 - i * 13}%` }} /></span><b>{value}</b><small>{sample}</small></div>)}</div>
          <div className="result-insight"><Sparkles /><p><strong>Điểm đáng chú ý:</strong> Vina Components cao hơn mức trung bình nhóm 6,1 điểm phần trăm. Nên xem thêm theo warehouse và nhóm sản phẩm.</p></div>
        </article>
        <aside className="panel evidence-panel-large"><div className="evidence-title"><span><Database />Bằng chứng</span><CheckCircle2 /></div><dl><Evidence label="Metric" value="Late delivery rate · v1.2" /><Evidence label="Công thức" value="Đơn giao trễ / đơn đủ điều kiện" /><Evidence label="Bộ lọc" value="90 ngày · Không gồm đơn hủy" /><Evidence label="Grain" value="Supplier" /><Evidence label="Độ mới dữ liệu" value="08:35 · 14/09/2026" /></dl><button className="secondary-button" type="button"><Code2 />Xem truy vấn đã kiểm tra</button></aside>
      </section>
    </div>
  );
}

function Evidence({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }

const collectionCopy = {
  conversations: ["Lịch sử phân tích", "Cuộc hội thoại", "Tiếp tục các câu hỏi trước mà không mất ngữ cảnh đã xác nhận."],
  metrics: ["Nguồn sự thật nghiệp vụ", "Thư viện metric", "Theo dõi công thức, phiên bản và phạm vi sử dụng của từng KPI."],
  audit: ["Tin cậy & quản trị", "Đánh giá và audit", "Kiểm tra trạng thái validation, chất lượng dữ liệu và dấu vết truy vấn."],
};

function CollectionPage({ type }: { type: "conversations" | "metrics" | "audit" }) {
  const [eyebrow, title, description] = collectionCopy[type];
  return <div className="workspace-wrap content-view"><section className="collection-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div><button className="primary-button" type="button" onClick={() => go("query")}><Sparkles />Đặt câu hỏi mới</button></section>{type === "conversations" ? <ConversationList /> : type === "metrics" ? <MetricTable /> : <AuditView />}</div>;
}

function ConversationList() {
  const items = ["Top supplier giao trễ trong 90 ngày", "So sánh hiệu suất theo khu vực", "Xu hướng giao đúng hạn theo tuần", "SKU dưới reorder point tại Hà Nội"];
  return <div className="collection-grid">{items.map((item, i) => <button className="collection-card" type="button" key={item} onClick={() => go("query")}><span className="collection-icon"><MessageSquareText /></span><span><strong>{item}</strong><small>{i ? `${i + 1} ngày trước` : "Hôm nay · 09:12"}</small></span><ArrowRight /></button>)}</div>;
}

function MetricTable() {
  const rows = [["Tỷ lệ giao đúng hạn", "Supply Chain", "v1.2"], ["Tỷ lệ giao trễ", "Procurement", "v1.2"], ["Số lượng giao trễ", "Operations", "v1.0"], ["Tồn kho dưới reorder point", "Warehouse", "v0.8"]];
  return <div className="panel table-panel"><div className="table-header"><span>Metric</span><span>Owner</span><span>Phiên bản</span><span>Trạng thái</span></div>{rows.map(([name, owner, version]) => <div className="table-row" key={name}><span><TableProperties /><strong>{name}</strong></span><span>{owner}</span><span>{version}</span><span className="approved"><CheckCircle2 />Đã duyệt</span></div>)}</div>;
}

function AuditView() {
  const items = ["Metric late_delivery_rate v1.2 được sử dụng", "Query #AT-1048 đã xác minh kết quả", "Freshness check hoàn tất", "Catalog supplier-performance được cập nhật"];
  return <div className="audit-grid"><article className="panel audit-summary"><span className="metric-icon"><ShieldCheck /></span><strong>100%</strong><h2>Truy vấn hợp lệ</h2><p>24/24 truy vấn gần nhất đã qua policy và semantic validation.</p></article><article className="panel audit-feed"><h2>Hoạt động gần đây</h2>{items.map((item, i) => <div key={item}><span className={i === 0 ? "live" : ""} /><p><strong>{item}</strong><small>{i * 14 + 3} phút trước</small></p></div>)}</article></div>;
}

function AuthPage({ mode }: { mode: "login" | "register" }) {
  const [showPassword, setShowPassword] = useState(false);
  const [status, setStatus] = useState("");
  const register = mode === "register";
  function submit(e: FormEvent) { e.preventDefault(); setStatus(register ? "Tài khoản demo đã sẵn sàng để kết nối backend xác thực." : "Đăng nhập giao diện thành công. Đang mở dashboard…"); if (!register) window.setTimeout(() => go("dashboard"), 900); }
  return (
    <main className="auth-page content-view">
      <section className="auth-story"><button className="auth-brand" type="button" onClick={() => go("dashboard")}><BrandMark /><span><strong>AtlasIQ</strong><small>Semantic analytics</small></span></button><div className="auth-story-copy"><span className="auth-eyebrow">{register ? "Bắt đầu có kiểm soát" : "Từ câu hỏi đến quyết định"}</span><h1>{register ? <>Một không gian chung.<br />Một định nghĩa KPI.</> : <>Dữ liệu phức tạp.<br />Câu trả lời rõ ràng.</>}</h1><p>{register ? "Tạo workspace cho đội ngũ và bắt đầu từ các metric đã được phê duyệt." : "Khám phá hiệu suất chuỗi cung ứng với câu trả lời có thể kiểm tra."}</p></div><div className="auth-proof"><span><ShieldCheck />Truy cập theo quyền</span><span><Check />SQL được kiểm tra</span><span><Clock3 />Hiển thị độ mới dữ liệu</span></div></section>
      <section className="auth-form-side"><div className="auth-form-wrap"><button className="back-button" type="button" onClick={() => go("dashboard")}><ArrowLeft />Quay lại dashboard</button><form className="auth-form" onSubmit={submit}><span className="eyebrow">{register ? "Tạo workspace" : "Chào mừng trở lại"}</span><h2>{register ? "Tạo tài khoản" : "Đăng nhập"}</h2><p>{register ? "Dùng email công việc để bắt đầu." : "Tiếp tục không gian phân tích của bạn."}</p>{register && <AuthField id="full-name" label="Họ và tên" icon={<User />} type="text" placeholder="Nguyễn Minh Anh" />}<AuthField id="auth-email" label="Email công việc" icon={<Mail />} type="email" placeholder="ban@company.vn" /><div className="auth-field"><label htmlFor="auth-password">Mật khẩu</label><div><KeyRound /><input id="auth-password" required minLength={8} type={showPassword ? "text" : "password"} placeholder="Tối thiểu 8 ký tự" /><button type="button" aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff /> : <Eye />}</button></div></div>{register ? <label className="terms-check"><input required type="checkbox" />Tôi đồng ý với Điều khoản sử dụng và Chính sách bảo mật.</label> : <div className="auth-options"><label><input type="checkbox" />Ghi nhớ đăng nhập</label><button type="button">Quên mật khẩu?</button></div>}<button className="auth-submit" type="submit">{register ? "Tạo tài khoản" : "Đăng nhập"}<ArrowRight /></button><div className="auth-status" aria-live="polite">{status}</div><p className="auth-switch">{register ? "Đã có tài khoản?" : "Chưa có tài khoản?"} <button type="button" onClick={() => go(register ? "login" : "register")}>{register ? "Đăng nhập" : "Đăng ký ngay"}</button></p></form><div className="demo-note"><LockKeyhole />Giao diện xác thực đang ở chế độ demo; chưa gửi thông tin ra ngoài.</div></div></section>
    </main>
  );
}

function AuthField({ id, label, icon, type, placeholder }: { id: string; label: string; icon: ReactNode; type: string; placeholder: string }) {
  return <div className="auth-field"><label htmlFor={id}>{label}</label><div>{icon}<input id={id} required type={type} placeholder={placeholder} /></div></div>;
}

export default function App() {
  const [view, setView] = useState<View>(currentView);
  useEffect(() => { if (!window.location.hash) window.location.hash = "/dashboard"; const update = () => setView(currentView()); window.addEventListener("hashchange", update); return () => window.removeEventListener("hashchange", update); }, []);
  if (view === "login" || view === "register") return <AuthPage mode={view} />;
  return <ProductShell view={view}>{view === "dashboard" ? <Dashboard /> : view === "query" ? <QueryWorkspace /> : <CollectionPage type={view} />}</ProductShell>;
}
