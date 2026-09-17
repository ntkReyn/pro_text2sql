"use client";

import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft, ArrowRight, Bell, BookMarked, BookOpen, Bot, Check, CheckCircle2,
  ChevronDown, CircleHelp, ClipboardCheck, Clock3, Code2, Database, DatabaseZap,
  Eye, EyeOff, FileSearch, Gauge, KeyRound, LayoutDashboard, LoaderCircle,
  LockKeyhole, Mail, Menu, MessageSquareText, PackageCheck, Plus, SendHorizontal,
  Settings2, ShieldCheck, Sparkles, TableProperties, Trash2, TriangleAlert, TrendingUp,
  User, UserCheck, UserCog, UsersRound, X,
} from "lucide-react";

type Role = "admin" | "metric_steward" | "analyst" | "business_user" | "auditor";
type Period = "7" | "30" | "90";
type View =
  | "dashboard" | "query" | "conversations" | "metrics" | "audit"
  | "members" | "workspace_settings" | "quality" | "approvals" | "glossary"
  | "query_log" | "policy_decisions" | "access_reviews" | "login" | "register";
type SectionView = Exclude<View, "dashboard" | "query" | "conversations" | "metrics" | "audit" | "login" | "register">;
type AppIcon = typeof LayoutDashboard;
type NavItem = { id: View; label: string; icon: AppIcon };
type ConversationItem = { id: string; title: string; preview: string; updated: string; question: string };
type WrenResponse = {
  status: "planned" | "executed" | "needs_clarification" | "unanswerable" | "failed";
  question: string;
  message: string | null;
  sql: string | null;
  planned_sql: string | null;
  assumptions: string[];
  context: {
    project: string;
    models: Array<{ name: string; description: string | null; columns: string[] }>;
    knowledge_files: string[];
    confirmed_query_count: number;
  };
  security: {
    decision: "pass" | "reject";
    referenced_relations: string[];
    checks: string[];
    error_code: string | null;
  } | null;
  execution: {
    columns: string[];
    rows: Array<Record<string, unknown>>;
    row_count: number;
    truncated: boolean;
    duration_ms: number;
  } | null;
  trace: {
    workflow_version: string;
    context_loaded: boolean;
    dry_plan_attempts: number;
    repair_attempts: number;
    stages: string[];
  };
};

const DEMO_ROLE_STORAGE_KEY = "atlasiq_demo_role_v2";

const roles: Record<Role, { label: string; short: string; description: string; area: string; person: string; initials: string; job: string; icon: AppIcon }> = {
  admin: { label: "Workspace Admin", short: "Admin", description: "Quản lý thành viên, role và cấu hình workspace.", area: "Quản trị workspace", person: "Lan Phương", initials: "LP", job: "Workspace Admin", icon: UserCog },
  metric_steward: { label: "Metric Steward", short: "Steward", description: "Chuẩn hóa metric, glossary và chất lượng dữ liệu.", area: "Quản trị metric", person: "Quang Huy", initials: "QH", job: "Data & Metric Steward", icon: BookMarked },
  analyst: { label: "Data Analyst", short: "Analyst", description: "Phân tích chuyên sâu và kiểm tra truy vấn theo phạm vi.", area: "Phân tích dữ liệu", person: "Minh Anh", initials: "MA", job: "Senior Data Analyst", icon: DatabaseZap },
  business_user: { label: "Business User", short: "Business", description: "Theo dõi KPI và đặt câu hỏi bằng ngôn ngữ tự nhiên.", area: "Ra quyết định vận hành", person: "Thu Hà", initials: "TH", job: "EV Operations Lead", icon: UsersRound },
  auditor: { label: "Auditor", short: "Audit", description: "Rà soát policy, lịch sử truy vấn và quyền truy cập.", area: "Kiểm soát & tuân thủ", person: "Hải Nam", initials: "HN", job: "Data Governance Auditor", icon: FileSearch },
};

const navigation: Record<Role, NavItem[]> = {
  admin: [
    { id: "dashboard", label: "Tổng quan workspace", icon: LayoutDashboard },
    { id: "members", label: "Thành viên & quyền", icon: UsersRound },
    { id: "workspace_settings", label: "Cấu hình workspace", icon: Settings2 },
    { id: "audit", label: "Nhật ký quản trị", icon: ShieldCheck },
  ],
  metric_steward: [
    { id: "dashboard", label: "Tổng quan metric", icon: LayoutDashboard },
    { id: "metrics", label: "Thư viện metric", icon: BookOpen },
    { id: "quality", label: "Chất lượng dữ liệu", icon: Gauge },
    { id: "approvals", label: "Hàng chờ phê duyệt", icon: ClipboardCheck },
    { id: "glossary", label: "Business glossary", icon: BookMarked },
    { id: "query", label: "Kiểm thử metric", icon: Sparkles },
  ],
  analyst: [
    { id: "dashboard", label: "Tổng quan phân tích", icon: LayoutDashboard },
    { id: "query", label: "Cuộc trò chuyện", icon: MessageSquareText },
    { id: "metrics", label: "Thư viện metric", icon: BookOpen },
    { id: "audit", label: "Hoạt động của tôi", icon: ShieldCheck },
  ],
  business_user: [
    { id: "dashboard", label: "Tổng quan vận hành", icon: LayoutDashboard },
    { id: "query", label: "Cuộc trò chuyện", icon: MessageSquareText },
    { id: "metrics", label: "Định nghĩa KPI", icon: BookOpen },
  ],
  auditor: [
    { id: "dashboard", label: "Tổng quan audit", icon: LayoutDashboard },
    { id: "query_log", label: "Nhật ký truy vấn", icon: FileSearch },
    { id: "policy_decisions", label: "Quyết định policy", icon: ShieldCheck },
    { id: "access_reviews", label: "Rà soát truy cập", icon: UserCheck },
    { id: "audit", label: "Dấu vết hệ thống", icon: Database },
  ],
};

const views: View[] = ["dashboard", "query", "conversations", "metrics", "audit", "members", "workspace_settings", "quality", "approvals", "glossary", "query_log", "policy_decisions", "access_reviews", "login", "register"];
const chartData: Record<Period, { values: number[]; labels: string[] }> = {
  "7": { values: [91, 93, 92, 95, 94, 96, 96.4], labels: ["T2", "T3", "T4", "T5", "T6", "T7", "CN"] },
  "30": { values: [89, 91, 90, 93, 92, 94, 95, 94, 96, 96.4], labels: ["16/08", "19/08", "22/08", "25/08", "28/08", "31/08", "03/09", "06/09", "10/09", "14/09"] },
  "90": { values: [84, 86, 85, 88, 89, 91, 90, 92, 94, 95, 96.4], labels: ["T6", "", "", "T7", "", "", "T8", "", "", "", "T9"] },
};

type DashboardConfig = {
  eyebrow: string; title: string; description: string; action: string; actionView: View;
  trend: string; delta: string; offset: number;
  kpis: Array<[string, string, string, AppIcon, string?]>;
  alerts: Array<[string, string, string, string]>; alertView: View;
  quick: [string, string, string, string, View]; coverage: Array<[string, string]>;
};

const dashboards: Record<Role, DashboardConfig> = {
  admin: {
    eyebrow: "Workspace control center", title: "Quản trị workspace", description: "Theo dõi thành viên, quyền truy cập và cấu hình cần xử lý hôm nay.", action: "Quản lý thành viên", actionView: "members", trend: "Yêu cầu truy cập đúng SLA", delta: "+3,4 điểm trong tháng", offset: -1.6,
    kpis: [["Thành viên hoạt động", "48", "+4 trong tháng này", UsersRound], ["Yêu cầu chờ duyệt", "03", "2 yêu cầu sắp quá SLA", Clock3, "warm"], ["Tài khoản đặc quyền", "07", "Đã rà soát 6/7", UserCog, "blue"], ["Policy đã áp dụng", "100%", "12/12 policy hoạt động", ShieldCheck]],
    alerts: [["3 yêu cầu role mới", "Cần kiểm tra phạm vi dữ liệu", "Cũ nhất · 6 giờ trước", "warning"], ["Service account ETL", "Khoá truy cập hết hạn sau 5 ngày", "Owner · Data Platform", "danger"], ["Quarterly access review", "Đã hoàn tất 86%", "Còn 7 tài khoản", "positive"]], alertView: "members",
    quick: ["Kiểm tra quyền theo role", "Xem nhanh màn hình và data scope một role được phép sử dụng.", "Data Analyst đang truy cập được những domain nào?", "Mở danh sách quyền", "members"], coverage: [["Role đã chuẩn hóa", "100%"], ["Data scope đã gán", "86%"]],
  },
  metric_steward: {
    eyebrow: "Semantic governance", title: "Sức khỏe hệ metric", description: "Tập trung vào metric cần duyệt, dữ liệu giảm chất lượng và định nghĩa chưa hoàn chỉnh.", action: "Mở hàng chờ duyệt", actionView: "approvals", trend: "Metric đạt chuẩn chất lượng", delta: "+1,8 điểm trong tháng", offset: 0.8,
    kpis: [["Metric đã phê duyệt", "24", "+3 từ kỳ trước", BookOpen], ["Đang chờ review", "03", "1 metric ưu tiên cao", ClipboardCheck, "warm"], ["Quality score", "97,2%", "+1,8 điểm", Gauge, "blue"], ["Độ trễ dữ liệu", "11 phút", "Trong SLA 30 phút", Clock3]],
    alerts: [["Battery watch candidates v0.9", "Thiếu owner và acceptance test", "Gửi bởi An Trần", "warning"], ["charging_success_rate", "Freshness giảm dưới ngưỡng", "EV charging domain", "danger"], ["Completed energy v1.0", "Đã vượt toàn bộ quality gate", "Sẵn sàng publish", "positive"]], alertView: "approvals",
    quick: ["Kiểm thử định nghĩa metric", "Xác nhận grain, bộ lọc và kết quả mẫu trước khi publish.", "Tỷ lệ phiên sạc thành công theo khu vực trong quý 3", "Chạy kiểm thử", "query"], coverage: [["EV charging analytics", "100%"], ["Battery & service", "82%"]],
  },
  analyst: {
    eyebrow: "Verified analytics", title: "Không gian phân tích", description: "Theo dõi hiệu quả truy vấn, câu hỏi đang mở và insight cần đào sâu.", action: "Bắt đầu phân tích", actionView: "query", trend: "Tỷ lệ truy vấn được xác minh", delta: "+1,2 điểm trong tháng", offset: 1.2,
    kpis: [["Truy vấn tháng này", "248", "+32 so với tháng trước", DatabaseZap], ["Được xác minh", "97,6%", "+1,2 điểm", ShieldCheck, "blue"], ["Thời gian phản hồi", "1,8s", "Nhanh hơn 0,4 giây", Clock3], ["Phân tích đã lưu", "16", "4 được chia sẻ", MessageSquareText]],
    alerts: [["Trạm Hà Nội 02", "Tỷ lệ phiên sạc thất bại tăng", "1 / 1 phiên đủ điều kiện", "danger"], ["Dòng xe VF6_LAB", "Có phiên sạc thất bại cần kiểm tra", "Dữ liệu quý 3/2026", "warning"], ["Khu vực phía Nam", "Điện năng sạc thành công cao nhất", "403,4 kWh trong dữ liệu mẫu", "positive"]], alertView: "query",
    quick: ["Mở một hướng phân tích mới", "Hỏi tự nhiên, xem SQL đã kiểm tra và lưu lại ngữ cảnh.", "Khu vực nào có tỷ lệ sạc thành công thấp nhất?", "Phân tích ngay", "query"], coverage: [["EV charging analytics", "100%"], ["Battery & service", "68%"]],
  },
  business_user: {
    eyebrow: "Thứ Hai · 14 tháng 9", title: "Tổng quan vận hành", description: "Tập trung vào những thay đổi cần quyết định hôm nay.", action: "Đặt câu hỏi mới", actionView: "query", trend: "Xu hướng phiên sạc thành công", delta: "+2,1 điểm trong tháng", offset: 0,
    kpis: [["Tỷ lệ phiên sạc thành công", "76,9%", "10 / 13 phiên đủ điều kiện", PackageCheck], ["Phiên sạc thất bại", "03", "Quý 3 năm 2026", Clock3, "warm"], ["Xe cần theo dõi pin", "01", "SOH dưới 80%", TriangleAlert, "danger"], ["KPI sạc đang theo dõi", "05", "100% theo catalog v1.0", Gauge, "blue"]],
    alerts: [["Trạm Hà Nội 02", "Tỷ lệ phiên sạc thất bại tăng", "1 / 1 phiên đủ điều kiện", "danger"], ["Dòng xe VF6_LAB", "Có phiên sạc thất bại cần kiểm tra", "Dữ liệu quý 3/2026", "warning"], ["Khu vực phía Nam", "Điện năng sạc thành công cao nhất", "403,4 kWh trong dữ liệu mẫu", "positive"]], alertView: "query",
    quick: ["Hỏi dữ liệu của bạn", "Dùng metric đã phê duyệt để nhận kết quả có bằng chứng.", "Khu vực nào có tỷ lệ sạc thành công thấp nhất?", "Hỏi ngay", "query"], coverage: [["EV charging analytics", "100%"], ["Battery & service", "68%"]],
  },
  auditor: {
    eyebrow: "Governance assurance", title: "Trung tâm kiểm soát", description: "Rà soát dấu vết truy vấn, quyết định policy và ngoại lệ truy cập trên toàn workspace.", action: "Mở nhật ký truy vấn", actionView: "query_log", trend: "Truy vấn tuân thủ policy", delta: "+0,6 điểm trong tháng", offset: 2.6,
    kpis: [["Sự kiện audit", "1.248", "+184 trong tháng", FileSearch], ["Policy đã đánh giá", "100%", "Không có lượt bị bỏ qua", ShieldCheck, "blue"], ["Ngoại lệ đang mở", "03", "1 ngoại lệ sắp hết hạn", TriangleAlert, "warm"], ["Vi phạm nghiêm trọng", "00", "30 ngày liên tục", CheckCircle2]],
    alerts: [["Export raw rows", "Ngoại lệ hết hạn sau 2 ngày", "Analyst · Procurement", "warning"], ["Query #AT-1048", "Policy masking đã được áp dụng", "PII fields · 09:12", "positive"], ["Service account legacy-bi", "Chưa có owner xác nhận", "Rà soát quý III", "danger"]], alertView: "policy_decisions",
    quick: ["Theo dấu một truy vấn", "Tìm policy, metric version và data scope tạo nên kết quả.", "Tra cứu dấu vết Query #AT-1048", "Mở nhật ký", "query_log"], coverage: [["Query có audit trail", "100%"], ["Access review hoàn tất", "86%"]],
  },
};

type SectionConfig = { eyebrow: string; title: string; description: string; stats: Array<[string, string]>; items: Array<[string, string, string, string, "positive" | "warning" | "neutral"]> };
const sections: Record<SectionView, SectionConfig> = {
  members: { eyebrow: "Workspace access", title: "Thành viên & quyền", description: "Gán role theo nhiệm vụ và giới hạn data scope độc lập cho từng thành viên.", stats: [["Thành viên", "48"], ["Role đang dùng", "5"], ["Chờ duyệt", "3"]], items: [["Nguyễn Minh Anh", "Data Analyst · EV charging, Battery", "Hoạt động 8 phút trước", "Đang hoạt động", "positive"], ["Lê Thu Hà", "Business User · EV charging analytics", "Hoạt động 26 phút trước", "Đang hoạt động", "positive"], ["Trần An", "Yêu cầu Data Analyst · Service", "Gửi 2 giờ trước", "Chờ phê duyệt", "warning"], ["Service · legacy-bi", "Service account · Read only", "Owner chưa xác nhận", "Cần rà soát", "neutral"]] },
  workspace_settings: { eyebrow: "Workspace configuration", title: "Cấu hình workspace", description: "Các chính sách nền tảng áp dụng cho toàn bộ thành viên và dữ liệu.", stats: [["Policy hoạt động", "12"], ["SSO domain", "2"], ["Data domain", "4"]], items: [["Đăng nhập doanh nghiệp", "Bắt buộc SSO cho company.vn", "Cập nhật 12/09/2026", "Đã bật", "positive"], ["Phê duyệt role", "Role mới cần Workspace Admin duyệt", "Áp dụng toàn workspace", "Đã bật", "positive"], ["Xuất dữ liệu thô", "Yêu cầu lý do và thời hạn", "Policy · export-raw-row", "Có điều kiện", "warning"], ["Session timeout", "Tự kết thúc sau 8 giờ", "Khuyến nghị · 4 giờ", "Cần rà soát", "neutral"]] },
  quality: { eyebrow: "Data observability", title: "Chất lượng dữ liệu", description: "Theo dõi freshness, completeness và quality gate gắn với metric.", stats: [["Quality score", "97,2%"], ["Trong SLA", "18/20"], ["Sự cố mở", "2"]], items: [["charging_session_analytics", "Freshness · 11 phút / SLA 30 phút", "5 metric phụ thuộc", "Khỏe mạnh", "positive"], ["battery_health_snapshot", "Completeness · 99,8%", "Thiếu 2 / 12.480 records", "Theo dõi", "warning"], ["charging_sessions", "Schema contract · 12/12 checks", "Cập nhật 08:31", "Khỏe mạnh", "positive"], ["service_visits", "Freshness · 74 phút / SLA 60 phút", "Ảnh hưởng 2 metric", "Ngoài SLA", "neutral"]] },
  approvals: { eyebrow: "Maker–checker workflow", title: "Hàng chờ phê duyệt", description: "Review thay đổi metric trước khi publish vào nguồn sự thật nghiệp vụ.", stats: [["Đang chờ", "3"], ["Ưu tiên cao", "1"], ["Duyệt tuần này", "8"]], items: [["Battery watch candidates · v0.9", "Cập nhật công thức và grain", "An Trần · 2 giờ trước", "Thiếu test", "warning"], ["Charging failure rate · v1.0", "Metric mới cho vận hành sạc", "Mai Linh · 5 giờ trước", "Sẵn sàng review", "positive"], ["Charging success rate · v1.1", "Làm rõ denominator", "Minh Anh · hôm qua", "Cần đối chiếu", "neutral"], ["Completed energy · v1.0", "Đã vượt 12/12 quality gate", "Duyệt bởi Quang Huy", "Đã publish", "positive"]] },
  glossary: { eyebrow: "Shared business language", title: "Business glossary", description: "Giữ thuật ngữ, owner và metric liên quan nhất quán giữa các đội ngũ.", stats: [["Thuật ngữ", "86"], ["Có owner", "96%"], ["Cần cập nhật", "4"]], items: [["Phiên sạc đủ điều kiện", "Phiên hoàn tất hoặc thất bại", "Liên kết 2 metric", "Đã duyệt", "positive"], ["Sạc thành công", "Hoàn tất và energy_delivered_kwh > 0", "Owner · Charging Operations", "Đã duyệt", "positive"], ["Hiệu quả sạc", "Chưa thống nhất metric đại diện", "Đề xuất bởi Operations", "Cần định nghĩa", "warning"], ["Sức khỏe pin hiện tại", "Snapshot hợp lệ mới nhất của mỗi xe", "Liên kết 2 metric", "Đã duyệt", "positive"]] },
  query_log: { eyebrow: "Immutable query trail", title: "Nhật ký truy vấn", description: "Theo dấu actor, metric version, data scope và kết quả policy.", stats: [["30 ngày", "1.248"], ["Đã xác minh", "97,6%"], ["Bị chặn", "14"]], items: [["Query #AT-1048", "charging_success_rate v1.0 · Analyst", "Minh Anh · 09:12", "Cho phép + masking", "positive"], ["Query #AT-1047", "completed_energy_delivered_kwh v1.0 · Business", "Thu Hà · 08:56", "Cho phép", "positive"], ["Query #AT-1046", "customer_contact v1.0 · Analyst", "Ngoài data scope · 08:41", "Đã chặn", "warning"], ["Query #AT-1045", "failed_charging_session_count v1.0 · Analyst", "Quang Nam · 08:33", "Cho phép", "positive"]] },
  policy_decisions: { eyebrow: "Authorization evidence", title: "Quyết định policy", description: "Kiểm tra lý do một hành động được cho phép, masking hoặc từ chối.", stats: [["Cho phép", "1.191"], ["Có masking", "43"], ["Từ chối", "14"]], items: [["mask-customer-contact", "Ẩn định danh trực tiếp khỏi Business User", "Query #AT-1048 · 09:12", "Đã áp dụng", "positive"], ["deny-cross-domain-query", "Domain HR nằm ngoài data scope", "Query #AT-1046 · 08:41", "Đã chặn", "warning"], ["allow-verified-metric", "Metric v1.0 đã duyệt", "Query #AT-1045 · 08:33", "Đã áp dụng", "positive"], ["export-raw-row", "Ngoại lệ tạm thời cho EV Operations", "Hết hạn 16/09/2026", "Cần rà soát", "neutral"]] },
  access_reviews: { eyebrow: "Periodic access certification", title: "Rà soát truy cập", description: "Xác nhận role và data scope vẫn phù hợp với nhiệm vụ thực tế.", stats: [["Đã rà soát", "86%"], ["Còn lại", "7"], ["Quá hạn", "1"]], items: [["Data Analyst · EV Operations", "12 thành viên · raw rows giới hạn", "Owner · Phạm Quốc Bảo", "10/12 đã duyệt", "warning"], ["Business User · Charging Analytics", "18 thành viên · aggregate only", "Owner · Lê Thu Hà", "Hoàn tất", "positive"], ["Metric Steward", "4 thành viên · catalog write", "Owner · Quang Huy", "Hoàn tất", "positive"], ["Service accounts", "5 tài khoản · 1 thiếu owner", "Quá hạn 1 ngày", "Cần xử lý", "neutral"]] },
};

const chargingGroups = [["Khu vực phía Nam", "100%", "5 / 5"], ["Khu vực miền Trung", "66,7%", "2 / 3"], ["Khu vực phía Bắc", "60%", "3 / 5"]];

function go(view: View) { if (typeof window !== "undefined") window.location.hash = `/${view}`; }
function currentView(): View { if (typeof window === "undefined") return "dashboard"; const value = window.location.hash.replace(/^#\//, "") as View; return views.includes(value) ? value : "dashboard"; }
function storedRole(): Role { if (typeof window === "undefined") return "analyst"; const value = window.sessionStorage.getItem(DEMO_ROLE_STORAGE_KEY) as Role | null; return value && Object.hasOwn(roles, value) ? value : "analyst"; }
function roleFromAccount(email: string): Role {
  const account = email.trim().toLowerCase();
  if (account.includes("admin")) return "admin";
  if (account.includes("steward") || account.includes("metric")) return "metric_steward";
  if (account.includes("analyst")) return "analyst";
  if (account.includes("audit")) return "auditor";
  return "business_user";
}
function linePath(values: number[]) { return values.map((value, index) => `${index ? "L" : "M"}${((index / (values.length - 1)) * 700).toFixed(1)},${(210 - ((value - 80) / 20) * 210).toFixed(1)}`).join(" "); }
function BrandMark() { return <span className="brand-mark" aria-hidden="true"><span /></span>; }

function RouteMotion({ motionKey, children }: { motionKey: string; children: ReactNode }) {
  return <motion.div key={motionKey} className="route-motion" initial={{ opacity: 0, y: 14, scale: 0.995 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.div>;
}

function ProductShell({ view, role, pending, children }: { view: View; role: Role; pending: boolean; children: ReactNode }) {
  const profile = roles[role]; const RoleIcon = profile.icon; const [mobileNavOpen, setMobileNavOpen] = useState(false);
  return <div className={`app-shell role-${role}`}>
    <aside className={`sidebar ${mobileNavOpen ? "mobile-open" : ""}`}>
      <button className="brand-lockup brand-button" type="button" onClick={() => go("dashboard")}><BrandMark /><span><strong>AtlasIQ</strong><small>Semantic analytics</small></span></button>
      <button className="mobile-menu-trigger" type="button" onClick={() => setMobileNavOpen((open) => !open)} aria-expanded={mobileNavOpen} aria-controls="role-navigation">{mobileNavOpen ? <X /> : <Menu />}<span>{mobileNavOpen ? "Đóng" : "Menu"}</span></button>
      <nav id="role-navigation" className="primary-nav" aria-label={`Điều hướng cho ${profile.label}`}>{navigation[role].map(({ id, label, icon: Icon }) => <button className={view === id ? "active" : ""} type="button" key={id} onClick={() => { go(id); setMobileNavOpen(false); }}><Icon /><span>{label}</span></button>)}</nav>
      <div className="sidebar-spacer" />
      <button className="profile-button" type="button" onClick={() => go("login")}><span className="profile-avatar">{profile.initials}</span><span><strong>{profile.person}</strong><small>{profile.short} · {profile.job}</small></span><ChevronDown /></button>
    </aside>
    <main className="main-surface">
      <div className="workspace-ambient" aria-hidden="true"><span className="ambient-orb ambient-orb-one" /><span className="ambient-orb ambient-orb-two" /><span className="ambient-orb ambient-orb-three" /></div>
      <header className="topbar"><div className="topbar-actions"><button className="icon-button" type="button" aria-label="Trợ giúp"><CircleHelp /></button><button className="icon-button notification-button" type="button" aria-label="Thông báo"><Bell /><span /></button></div></header>
      {pending && <div className="pending-role-banner"><Clock3 /><span><strong>Chế độ xem trước:</strong> role đăng ký chưa có hiệu lực cho đến khi Workspace Admin phê duyệt.</span></div>}
      {children}
    </main>
  </div>;
}

function Dashboard({ role }: { role: Role }) {
  const [period, setPeriod] = useState<Period>("30"); const config = dashboards[role]; const RoleIcon = roles[role].icon;
  const source = chartData[period]; const values = useMemo(() => source.values.map((value) => Math.min(99.6, Math.max(80.5, value + config.offset))), [source.values, config.offset]);
  const path = useMemo(() => linePath(values), [values]); const last = values.at(-1) ?? 0; const lastY = 210 - ((last - 80) / 20) * 210;
  const welcomeTitle = role === "admin" ? "Mọi quyền truy cập, trong tầm kiểm soát." : role === "metric_steward" ? "Một catalog sạch bắt đầu từ một định nghĩa đúng." : role === "analyst" ? "Từ câu hỏi tự nhiên đến insight có thể kiểm tra." : role === "auditor" ? "Mọi quyết định đều để lại một dấu vết rõ ràng." : "Một câu hỏi rõ ràng cho một quyết định nhanh.";
  const welcomeDescription = role === "admin" ? "Workspace đang vận hành theo đúng policy. Bạn có thể xử lý các yêu cầu role và data scope còn mở." : role === "metric_steward" ? "Các metric đã duyệt là nền tảng để mọi đội ngũ nói cùng một ngôn ngữ dữ liệu." : role === "analyst" ? "Semantic layer đã sẵn sàng để bạn đi sâu vào nguyên nhân, không chỉ xem một con số." : role === "auditor" ? "Theo dõi policy result, metric version và actor trong cùng một luồng kiểm soát." : "AtlasIQ đã chuẩn bị các metric được phê duyệt để bạn bắt đầu từ điều quan trọng nhất.";
  return <div className="dashboard-wrap content-view">
    <section className="dashboard-heading role-dashboard-heading"><div><div className="dashboard-title-line"><h1>{config.title}</h1>{role !== "business_user" && <span className="dashboard-role-chip"><RoleIcon />{roles[role].label}</span>}</div><p>{config.description}</p></div>{role !== "business_user" && <button className="primary-button" type="button" onClick={() => go(config.actionView)}><Sparkles />{config.action}<ArrowRight /></button>}</section>
    <section className="dashboard-welcome" aria-label="Tóm tắt workspace"><div className="welcome-copy"><h2>{welcomeTitle}</h2><p>{welcomeDescription}</p><div className="welcome-pills"><span><CheckCircle2 />Metric layer sẵn sàng</span><span><Database />4 data domain</span><span><Clock3 />Cập nhật 08:35</span></div></div><div className="welcome-signal"><span className="signal-icon"><RoleIcon /></span><small>Role đang hoạt động</small><strong>{roles[role].label}</strong><span>Data scope đã áp dụng</span></div></section>
    <section className="metric-grid" aria-label={`Chỉ số cho ${roles[role].label}`}>{config.kpis.map(([label, value, detail, Icon, tone], index) => <MetricCard key={label} featured={index === 0} icon={<Icon />} tone={tone} label={label} value={value} detail={detail} />)}</section>
    <section className="dashboard-grid primary-row">
      <article className="panel performance-panel"><div className="panel-heading"><div><span className="panel-kicker">Xu hướng theo vai trò</span><h2>{config.trend}</h2></div><div className="period-control">{(["7", "30", "90"] as Period[]).map((item) => <button key={item} type="button" className={period === item ? "active" : ""} onClick={() => setPeriod(item)}>{item} ngày</button>)}</div></div><div className="chart-summary"><strong>{last.toFixed(1).replace(".", ",")}%</strong><span><TrendingUp /> {config.delta}</span></div><div className="line-chart" role="img" aria-label={`${config.trend} trong ${period} ngày`}><div className="y-axis"><span>100%</span><span>95%</span><span>90%</span><span>85%</span><span>80%</span></div><svg viewBox="0 0 700 230" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="area-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--role-accent)" stopOpacity=".24" /><stop offset="100%" stopColor="var(--role-accent)" stopOpacity="0" /></linearGradient><linearGradient id="line-stroke" x1="0" x2="1"><stop offset="0%" stopColor="var(--role-accent)" /><stop offset="100%" stopColor="var(--brand-teal)" /></linearGradient></defs><g className="chart-grid-lines">{[0, 52.5, 105, 157.5, 210].map((y) => <line key={y} x1="0" y1={y} x2="700" y2={y} />)}</g><path className="area-path" d={`${path} L700,210 L0,210 Z`} /><path className="line-path" d={path} /><circle className="last-point-ring" cx="700" cy={lastY} r="9" /><circle className="last-point" cx="700" cy={lastY} r="4" /></svg><div className="x-axis">{source.labels.map((label, index) => <span key={`${label}-${index}`}>{label}</span>)}</div></div></article>
      <article className="panel attention-panel"><div className="panel-heading"><div><span className="panel-kicker">Ưu tiên theo vai trò</span><h2>Cần bạn chú ý</h2></div><span className="count-badge">3</span></div><div className="attention-list">{config.alerts.map(([title, detail, meta, tone]) => <button className="attention-item" type="button" key={title} onClick={() => go(config.alertView)}><span className={`attention-dot ${tone}`} /><span className="attention-copy"><strong>{title}</strong><span>{detail}</span><small>{meta}</small></span><ArrowRight /></button>)}</div><button className="panel-link" type="button" onClick={() => go(config.alertView)}>Mở khu vực xử lý <ArrowRight /></button></article>
    </section>
    <section className="dashboard-grid secondary-row"><article className="panel query-panel"><div className="panel-heading"><div><span className="panel-kicker">Tác vụ nhanh</span><h2>{config.quick[0]}</h2></div><Bot /></div><p>{config.quick[1]}</p><button className="ask-box" type="button" onClick={() => go(config.quick[4])}><span>{config.quick[2]}</span><span className="ask-action"><Sparkles />{config.quick[3]}</span></button></article><article className="panel coverage-panel"><div className="panel-heading"><div><span className="panel-kicker">Mức độ sẵn sàng</span><h2>Phạm vi hiện tại</h2></div><RoleIcon /></div>{config.coverage.map(([label, value]) => <Coverage key={label} label={label} value={value} />)}</article></section>
  </div>;
}

function MetricCard({ featured, icon, tone = "", label, value, detail }: { featured?: boolean; icon: ReactNode; tone?: string; label: string; value: string; detail: string }) { return <article className={`metric-card ${featured ? "featured" : ""}`}><div className="metric-card-head"><span>{label}</span><span className={`metric-icon ${tone}`}>{icon}</span></div><strong className="metric-value">{value}</strong><div className="metric-foot positive"><TrendingUp /><span>{detail}</span></div></article>; }
function Coverage({ label, value }: { label: string; value: string }) { return <><div className="coverage-row"><span>{label}</span><strong>{value}</strong></div><div className="coverage-track"><span style={{ width: value }} /></div></>; }

function LegacyQueryWorkspace({ role }: { role: Role }) {
  const [question, setQuestion] = useState("Tỷ lệ phiên sạc thành công theo khu vực trạm trong quý 3 năm 2026?"); const [stage, setStage] = useState(-1); const [complete, setComplete] = useState(true);
  const steward = role === "metric_steward"; const canViewSql = role === "analyst" || steward;
  function submit(event: FormEvent) { event.preventDefault(); if (!question.trim() || stage >= 0) return; setComplete(false); setStage(0); }
  useEffect(() => { if (stage < 0) return; const timer = window.setTimeout(() => { if (stage < 3) setStage(stage + 1); else { setStage(-1); setComplete(true); } }, stage < 3 ? 470 : 560); return () => window.clearTimeout(timer); }, [stage]);
  return <div className="workspace-wrap content-view"><section className="workspace-heading"><h1>{steward ? "Kiểm thử metric" : "Cuộc trò chuyện"}</h1><p>{steward ? "Kiểm tra grain, bộ lọc và kết quả mẫu trước khi publish metric." : "Đặt câu hỏi tự nhiên và theo dõi cách AtlasIQ kiểm tra câu trả lời."}</p></section><form className="query-composer-large" onSubmit={submit}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Câu hỏi phân tích" /><div className="query-composer-foot"><div className="suggestion-row">{["So sánh theo khu vực trạm", "Xem lỗi sạc theo tuần", "Phân tích theo dòng xe"].map((text) => <button type="button" key={text} onClick={() => setQuestion(text)}>{text}</button>)}</div><button className="primary-button" type="submit" disabled={stage >= 0}>{stage >= 0 ? <LoaderCircle className="spin" /> : <SendHorizontal />}{stage >= 0 ? "Đang phân tích" : steward ? "Chạy kiểm thử" : "Phân tích"}</button></div><div className={`stage-progress ${stage >= 0 ? "visible" : ""}`} aria-live="polite">{["Hiểu câu hỏi", "Kiểm tra metric", "Tạo truy vấn", "Xác minh kết quả"].map((text, index) => <span key={text} className={stage > index ? "done" : stage === index ? "current" : ""}><Check />{text}</span>)}</div></form><section className={`query-result-layout ${complete ? "ready" : "loading"}`} aria-live="polite"><article className="panel result-panel-large"><div className="result-heading"><div><span>Kết quả · Quý 3/2026</span><h2>Tỷ lệ phiên sạc thành công theo khu vực trạm</h2></div><span className="verified-label"><ShieldCheck />Đã xác minh</span></div><div className="result-highlight"><strong>76,9%</strong><span>10 / 13 phiên sạc đủ điều kiện</span></div><div className="ranking-bars">{chargingGroups.map(([name, value, sample], index) => <div className="ranking-bar" key={name}><span>{index + 1}</span><strong>{name}</strong><span className="bar-track"><span style={{ width: `${100 - index * 20}%` }} /></span><b>{value}</b><small>{sample}</small></div>)}</div><div className="result-insight"><Sparkles /><p><strong>Điểm đáng chú ý:</strong> Khu vực phía Bắc có tỷ lệ thấp nhất trong dữ liệu mẫu. Nên xem thêm theo trạm và lý do dừng phiên sạc.</p></div></article><aside className="panel evidence-panel-large"><div className="evidence-title"><span><Database />Bằng chứng</span><CheckCircle2 /></div><dl><Evidence label="Metric" value="Charging success rate · v1.0" /><Evidence label="Công thức" value="Phiên thành công / phiên hoàn tất hoặc thất bại" /><Evidence label="Bộ lọc" value="Quý 3/2026 · Loại phiên hủy/đang sạc" /><Evidence label="Grain" value="Khu vực trạm" /><Evidence label="Độ mới dữ liệu" value="08:35 · 14/09/2026" /></dl><button className="secondary-button" type="button">{canViewSql ? <Code2 /> : <BookOpen />}{canViewSql ? "Xem truy vấn đã kiểm tra" : "Xem phương pháp tính"}</button></aside></section></div>;
}
function Evidence({ label, value }: { label: string; value: string }) { return <div><dt>{label}</dt><dd>{value}</dd></div>; }

function ConversationHistory({ items, activeId, onSelect, onNew, onDelete, onDeleteAll, variant = "sidebar" }: { items: ConversationItem[]; activeId: string; onSelect: (item: ConversationItem) => void; onNew: () => void; onDelete: (id: string) => void; onDeleteAll: () => void; variant?: "sidebar" | "page" }) {
  return <aside className={`conversation-history ${variant === "page" ? "conversation-history-page" : ""}`} aria-label="Lịch sử trò chuyện"><div className="conversation-history-heading"><div><span className="conversation-history-kicker">Workspace</span><h2>Trò chuyện</h2></div></div><button className="new-conversation-button" type="button" onClick={onNew}><Plus />Đoạn chat mới</button><div className="conversation-history-section-heading"><h3>Lịch sử trò chuyện</h3><div className="conversation-history-actions"><button className="conversation-history-delete-all" type="button" onClick={onDeleteAll} disabled={items.length === 0} aria-label="Xóa tất cả cuộc trò chuyện" title="Xóa tất cả">Xóa tất cả</button><span className="conversation-count" aria-label={`${items.length} cuộc trò chuyện`}>{items.length}</span></div></div><div className="conversation-history-list">{items.length > 0 ? items.map((item) => <div className={`conversation-history-item ${activeId === item.id ? "active" : ""}`} key={item.id}><button className="conversation-history-item-open" type="button" onClick={() => onSelect(item)} aria-pressed={activeId === item.id}><span className="conversation-history-icon"><MessageSquareText /></span><span className="conversation-history-copy"><strong>{item.title}</strong><small>{item.preview}</small><time>{item.updated}</time></span></button><button className="conversation-history-delete" type="button" onClick={() => onDelete(item.id)} aria-label={`Xóa cuộc trò chuyện ${item.title}`} title="Xóa cuộc trò chuyện"><Trash2 /></button></div>) : <p className="conversation-history-empty">Chưa có cuộc trò chuyện nào.</p>}</div></aside>;
}

function WrenResult({ response, error, loading, canViewSql }: { response: WrenResponse | null; error: string; loading: boolean; canViewSql: boolean }) {
  if (loading) {
    return <section className="query-result-layout loading live-wren-result" aria-label="Đang lập kế hoạch truy vấn"><article className="panel result-panel-large wren-state-panel"><LoaderCircle className="spin" /><div><span>Wren workflow đang xử lý</span><h2>Đang đọc MDL và viết SQL theo semantic model…</h2><p>Wren sẽ kiểm tra SQL bằng dry-plan trước khi thực thi.</p></div></article></section>;
  }
  if (error) {
    return <section className="query-result-layout live-wren-result" aria-label="Lỗi kết nối"><article className="panel result-panel-large wren-state-panel wren-error"><TriangleAlert /><div><span>Không thể hoàn tất</span><h2>Analytics API chưa sẵn sàng</h2><p>{error}</p></div></article></section>;
  }
  if (!response) return null;

  if (response.status !== "planned" && response.status !== "executed") {
    const clarification = response.status === "needs_clarification";
    return <section className="query-result-layout live-wren-result" aria-label="Kết quả Wren"><article className={`panel result-panel-large wren-state-panel ${clarification ? "wren-clarification" : "wren-error"}`}>{clarification ? <CircleHelp /> : <TriangleAlert />}<div><span>{clarification ? "Cần làm rõ" : "Ngoài phạm vi Wren"}</span><h2>{clarification ? "Câu hỏi chưa đủ thông tin" : "Wren chưa thể trả lời"}</h2><p>{response.message ?? "Wren chưa thể lập kế hoạch cho câu hỏi này."}</p><small>Câu hỏi: {response.question}</small></div></article></section>;
  }

  const security = response.security;
  const trace = response.trace;
  const modelSummary = response.context.models.map((item) => item.name).join(", ") || "Không có";
  return <section className="query-result-layout ready live-wren-result" aria-label="Wren SQL đã kiểm tra"><article className="panel result-panel-large"><div className="result-heading"><div><span>Wren Engine · {trace.workflow_version}</span><h2>SQL đã được dry-plan</h2></div><span className="verified-label"><CheckCircle2 />{response.status === "executed" ? "Đã thực thi" : "Đã kiểm tra"}</span></div><div className="wren-plan-grid"><div><span>Models</span><strong>{modelSummary}</strong></div><div><span>Knowledge</span><strong>{response.context.knowledge_files.length} tệp</strong></div><div><span>Repairs</span><strong>{trace.repair_attempts}</strong></div><div><span>Rows</span><strong>{response.execution ? response.execution.row_count : "Chưa thực thi"}</strong></div></div><div className="result-insight"><Sparkles /><p><strong>Wren là semantic authority.</strong> Agent đọc MDL/knowledge, tạo SQL theo model name, sau đó Wren `dry_plan` mở rộng sang SQL vật lý và policy kiểm tra lại trước khi chạy.</p></div>{canViewSql && response.sql && <details className="wren-sql" open><summary><Code2 />Xem SQL theo Wren model</summary><pre>{response.sql}</pre></details>}{canViewSql && response.planned_sql && <details className="wren-sql"><summary><Code2 />Xem SQL Wren đã mở rộng</summary><pre>{response.planned_sql}</pre></details>}</article><aside className="panel evidence-panel-large"><div className="evidence-title"><span><Database />Bằng chứng</span><CheckCircle2 /></div><dl><Evidence label="Project" value={response.context.project} /><Evidence label="Models" value={modelSummary} /><Evidence label="Stages" value={trace.stages.join(" → ")} /><Evidence label="Logical SQL" value={response.sql ? "Đã sinh" : "Không có"} /><Evidence label="Wren dry-plan" value={response.planned_sql ? "Pass" : "Not run"} /><Evidence label="SQL policy" value={security ? `${security.decision}${security.error_code ? ` · ${security.error_code}` : ""}` : "Not run"} /><Evidence label="Trạng thái" value={response.status} /></dl>{!canViewSql && <p className="wren-role-note"><BookOpen />Role hiện tại xem semantic evidence; SQL chỉ hiển thị cho Analyst và Metric Steward.</p>}</aside></section>;
}

function QueryWorkspace({ role }: { role: Role }) {
  const defaultQuestion = "Tỷ lệ phiên sạc thành công theo khu vực trạm trong quý 3 năm 2026?";
  const conversationHistory: ConversationItem[] = [
    { id: "charging-success", title: "Tỷ lệ sạc thành công theo khu vực", preview: "Toàn bộ dữ liệu mẫu · 76,9%", updated: "Hôm nay · 09:12", question: defaultQuestion },
    { id: "regional-performance", title: "So sánh hiệu quả theo khu vực trạm", preview: "Phía Bắc có tỷ lệ thấp nhất", updated: "Hôm qua · 16:40", question: "So sánh tỷ lệ phiên sạc thành công theo khu vực trạm trong quý này." },
    { id: "weekly-trend", title: "Xu hướng lỗi sạc theo tuần", preview: "Theo dõi thay đổi trong quý 3", updated: "2 ngày trước", question: "Xu hướng số phiên sạc thất bại theo tuần trong quý 3 năm 2026 như thế nào?" },
    { id: "reorder-point", title: "SKU dưới reorder point tại Hà Nội", preview: "12 SKU cần được chú ý", updated: "4 ngày trước", question: "SKU nào đang dưới reorder point tại kho Hà Nội?" },
  ];
  const [historyItems, setHistoryItems] = useState<ConversationItem[]>(conversationHistory);
  const [question, setQuestion] = useState(defaultQuestion);
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [stage, setStage] = useState(-1);
  const [complete, setComplete] = useState(true);
  const [showResult, setShowResult] = useState(false);
  const [wrenResponse, setWrenResponse] = useState<WrenResponse | null>(null);
  const [queryError, setQueryError] = useState("");
  const [activeConversation, setActiveConversation] = useState("");
  const [conversationOpen, setConversationOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<"all" | ConversationItem | null>(null);
  const steward = role === "metric_steward"; const canViewSql = role === "analyst" || steward;
  async function submit(event: FormEvent) {
    event.preventDefault();
    const nextQuestion = question.trim();
    if (!nextQuestion || stage >= 0) return;
    setSubmittedQuestion(nextQuestion);
    setShowResult(true);
    setComplete(false);
    setWrenResponse(null);
    setQueryError("");
    setStage(0);
    try {
      const response = await fetch("/api/wren", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question: nextQuestion }),
      });
      setStage(2);
      const payload = await response.json() as WrenResponse | { detail?: string };
      if (!response.ok) throw new Error("detail" in payload ? payload.detail : `HTTP ${response.status}`);
      setWrenResponse(payload as WrenResponse);
    } catch (caught) {
      setQueryError(caught instanceof Error ? caught.message : "Không thể kết nối Analytics API.");
    } finally {
      setStage(-1);
      setComplete(true);
    }
  }
  function openConversation(item: ConversationItem) { setActiveConversation(item.id); setConversationOpen(true); setQuestion(item.question); setSubmittedQuestion(""); setWrenResponse(null); setQueryError(""); setShowResult(false); setComplete(true); setStage(-1); }
  function startNewConversation() { setActiveConversation("new"); setConversationOpen(true); setQuestion(""); setSubmittedQuestion(""); setWrenResponse(null); setQueryError(""); setShowResult(false); setComplete(true); setStage(-1); }
  function deleteConversation(id: string) { setHistoryItems((items) => items.filter((item) => item.id !== id)); if (activeConversation === id) { setActiveConversation(""); setConversationOpen(false); setQuestion(""); setSubmittedQuestion(""); setWrenResponse(null); setQueryError(""); setShowResult(false); setStage(-1); } setDeleteTarget(null); }
  function requestDeleteConversation(id: string) { const item = historyItems.find((entry) => entry.id === id); if (item) setDeleteTarget(item); }
  function requestDeleteAll() { if (historyItems.length > 0) setDeleteTarget("all"); }
  function deleteAllConversations() { setHistoryItems([]); setActiveConversation(""); setConversationOpen(false); setQuestion(""); setSubmittedQuestion(""); setWrenResponse(null); setQueryError(""); setShowResult(false); setStage(-1); setDeleteTarget(null); }
  function confirmDelete() { if (deleteTarget === "all") deleteAllConversations(); else if (deleteTarget) deleteConversation(deleteTarget.id); }
  function backToHistory() { setConversationOpen(false); setStage(-1); }
  return <div className="workspace-wrap content-view conversation-view">
    <section className={`workspace-heading conversation-heading ${conversationOpen ? "conversation-heading-open" : ""}`}><div><h1>{steward ? "Kiểm thử metric" : "Cuộc trò chuyện"}</h1>{conversationOpen ? <button className="conversation-back-button" type="button" onClick={backToHistory}><ArrowLeft />Lịch sử trò chuyện</button> : <p>{steward ? "Kiểm tra grain, bộ lọc và kết quả mẫu trước khi publish metric." : "Đặt câu hỏi tự nhiên và theo dõi cách AtlasIQ kiểm tra câu trả lời."}</p>}</div>{conversationOpen && <div className="conversation-heading-actions"><button className="new-conversation-button conversation-heading-new" type="button" onClick={startNewConversation}><Plus />Đoạn chat mới</button></div>}</section>
    {!conversationOpen ? <ConversationHistory variant="page" items={historyItems} activeId={activeConversation} onSelect={openConversation} onNew={startNewConversation} onDelete={requestDeleteConversation} onDeleteAll={requestDeleteAll} /> : <div className="conversation-chat-page"><section className="conversation-shell">
      <div className={`conversation-scroll ${showResult ? "has-result" : "new-conversation"}`} aria-live="polite">
        <div className="conversation-message assistant-message"><div className="conversation-body"><div className="conversation-bubble assistant-bubble"><p>{steward ? "Bạn có thể gửi một câu hỏi để kiểm tra định nghĩa, grain và bộ lọc của metric." : "Bạn đang cần quyết định điều gì hôm nay? Hãy bắt đầu bằng một câu hỏi về phiên sạc, trạm sạc, dòng xe, pin hoặc dịch vụ."}</p></div></div></div>
        {showResult && <div className="conversation-message user-message"><div className="conversation-body"><div className="conversation-bubble user-bubble"><p>{submittedQuestion}</p></div><small className="conversation-meta">Câu hỏi đã gửi</small></div></div>}
        {showResult && <div className="conversation-message assistant-message"><div className="conversation-body conversation-answer"><WrenResult response={wrenResponse} error={queryError} loading={!complete} canViewSql={canViewSql} /><small className="conversation-meta">AtlasIQ · Wren-first workflow, dry-plan trước khi thực thi</small></div></div>}
      </div>
      <form className="conversation-composer" onSubmit={submit}><label className="sr-only" htmlFor="query-input">Câu hỏi phân tích</label><div className="conversation-input-row"><textarea id="query-input" value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Câu hỏi phân tích" /><button className="conversation-submit-icon" type="submit" disabled={stage >= 0} aria-label={stage >= 0 ? "Đang phân tích" : steward ? "Chạy kiểm thử" : "Phân tích"} title={stage >= 0 ? "Đang phân tích" : steward ? "Chạy kiểm thử" : "Phân tích"}>{stage >= 0 ? <LoaderCircle className="spin" /> : <SendHorizontal />}</button></div><div className={`stage-progress ${stage >= 0 ? "visible" : ""}`} aria-live="polite">{["Hiểu câu hỏi", "Kiểm tra metric", "Tạo truy vấn", "Xác minh kết quả"].map((text, index) => <span key={text} className={stage > index ? "done" : stage === index ? "current" : ""}><Check />{text}</span>)}</div></form>
    </section></div>}
    {deleteTarget && createPortal(<div className="conversation-confirm-backdrop" role="presentation" onMouseDown={() => setDeleteTarget(null)}><section className="conversation-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-confirm-title" aria-describedby="delete-confirm-description" onMouseDown={(event) => event.stopPropagation()}><span className="conversation-confirm-icon"><Trash2 /></span><div className="conversation-confirm-copy"><span className="eyebrow">Xác nhận thao tác</span><h2 id="delete-confirm-title">{deleteTarget === "all" ? "Xóa tất cả lịch sử trò chuyện?" : "Xóa cuộc trò chuyện này?"}</h2><p id="delete-confirm-description">{deleteTarget === "all" ? <>Tất cả cuộc trò chuyện đã lưu sẽ bị xóa khỏi danh sách.<br />Thao tác này không thể hoàn tác.</> : <>“{deleteTarget.title}” sẽ bị xóa khỏi danh sách.<br />Thao tác này không thể hoàn tác.</>}</p></div><div className="conversation-confirm-actions"><button className="secondary-button" type="button" onClick={() => setDeleteTarget(null)}>Hủy</button><button className="danger-button" type="button" onClick={confirmDelete}><Trash2 />{deleteTarget === "all" ? "Xóa tất cả" : "Xóa cuộc trò chuyện"}</button></div></section></div>, document.body)}
  </div>;
}

function CollectionPage({ type, role }: { type: "conversations" | "metrics" | "audit"; role: Role }) {
  const copy = type === "conversations" ? ["Lịch sử phân tích", "Cuộc hội thoại", "Tiếp tục câu hỏi trước mà không mất ngữ cảnh."] : type === "metrics" ? ["Nguồn sự thật nghiệp vụ", role === "business_user" ? "Định nghĩa KPI" : "Thư viện metric", "Theo dõi công thức, phiên bản và phạm vi sử dụng."] : ["Tin cậy & quản trị", role === "auditor" ? "Dấu vết hệ thống" : "Đánh giá và audit", "Kiểm tra validation, policy và dấu vết theo đúng phạm vi role."];
  return <div className="workspace-wrap content-view"><section className="collection-heading"><div><h1>{copy[1]}</h1><p>{copy[2]}</p></div>{type === "conversations" && <button className="primary-button" type="button" onClick={() => go("query")}><Sparkles />Đặt câu hỏi mới</button>}{type === "metrics" && role === "metric_steward" && <button className="primary-button" type="button" onClick={() => go("approvals")}><ClipboardCheck />Mở hàng chờ duyệt</button>}</section>{type === "conversations" ? <ConversationList /> : type === "metrics" ? <MetricTable role={role} /> : <AuditView role={role} />}</div>;
}
function ConversationList() { const items = ["Tỷ lệ sạc thành công theo khu vực", "Phiên sạc lỗi theo dòng xe", "Xu hướng điện năng sạc theo tuần", "Thời lượng sạc tại trạm công cộng"]; return <div className="collection-grid">{items.map((item, index) => <button className="collection-card" type="button" key={item} onClick={() => go("query")}><span className="collection-icon"><MessageSquareText /></span><span><strong>{item}</strong><small>{index ? `${index + 1} ngày trước` : "Hôm nay · 09:12"}</small></span><ArrowRight /></button>)}</div>; }
function MetricTable({ role }: { role: Role }) { const rows = [["Tỷ lệ phiên sạc thành công", "Charging Operations", "v1.0", "Đã duyệt"], ["Số phiên sạc thất bại", "Charging Operations", "v1.0", "Đã duyệt"], ["Điện năng sạc thành công", "Energy Analytics", "v1.0", "Đã duyệt"], ["Ứng viên theo dõi pin", "Battery Analytics", "v0.9", role === "metric_steward" ? "Chờ review" : "Bản nháp"]]; return <div className="panel table-panel"><div className="table-header"><span>Metric</span><span>Owner</span><span>Phiên bản</span><span>Trạng thái</span></div>{rows.map(([name, owner, version, status]) => <div className="table-row" key={name}><span><TableProperties /><strong>{name}</strong></span><span>{owner}</span><span>{version}</span><span className={status === "Đã duyệt" ? "approved" : "review-status"}>{status === "Đã duyệt" ? <CheckCircle2 /> : <Clock3 />}{status}</span></div>)}</div>; }
function AuditView({ role }: { role: Role }) { const admin = role === "admin"; const items = admin ? ["Role Analyst được gán cho Trần An", "Data scope EV Operations được cập nhật", "Yêu cầu #AR-092 đã được phê duyệt", "Policy export-raw-row được bật"] : ["Metric charging_success_rate v1.0 được sử dụng", "Query #AT-1048 đã xác minh kết quả", "Freshness check hoàn tất", "Catalog ev-customer được cập nhật"]; return <div className="audit-grid"><article className="panel audit-summary"><span className="metric-icon"><ShieldCheck /></span><strong>100%</strong><h2>Dấu vết đầy đủ</h2><p>Mọi sự kiện đều có actor, thời gian và policy result.</p></article><article className="panel audit-feed"><h2>Hoạt động gần đây</h2>{items.map((item, index) => <div key={item}><span className={index === 0 ? "live" : ""} /><p><strong>{item}</strong><small>{index * 14 + 3} phút trước</small></p></div>)}</article></div>; }

function SectionPage({ type }: { type: SectionView }) { const config = sections[type]; return <div className="workspace-wrap content-view"><section className="workspace-heading section-heading"><h1>{config.title}</h1><p>{config.description}</p></section><section className="section-stat-grid" aria-label={`Tóm tắt ${config.title}`}>{config.stats.map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</section><section className="section-list">{config.items.map(([title, detail, meta, status, tone]) => <article className="section-list-item" key={title}><span className={`section-status-dot ${tone}`} /><div><h2>{title}</h2><p>{detail}</p><small>{meta}</small></div><span className={`section-status ${tone}`}>{status}</span><ArrowRight /></article>)}</section></div>; }
function AccessDenied({ role }: { role: Role }) { return <div className="workspace-wrap content-view access-denied-wrap"><section className="panel access-denied"><span className="access-denied-icon"><LockKeyhole /></span><h1>Không có quyền truy cập màn hình này</h1><p>Role <strong>{roles[role].label}</strong> không có nhiệm vụ tại khu vực này. Điều hướng đã được giới hạn theo role và data scope.</p><button className="primary-button" type="button" onClick={() => go("dashboard")}><ArrowLeft />Về dashboard của tôi</button></section></div>; }

function RoleSelector({ selected, onChange }: { selected: Role; onChange: (role: Role) => void }) { return <fieldset className="role-selector"><legend>Vai trò mong muốn</legend><p>Chọn nhiệm vụ gần nhất với công việc của bạn.</p><div className="role-options">{(Object.keys(roles) as Role[]).map((role) => { const profile = roles[role]; const Icon = profile.icon; return <label className={`role-option ${selected === role ? "selected" : ""}`} key={role}><input type="radio" name="role" value={role} checked={selected === role} onChange={() => onChange(role)} /><span className="role-option-icon"><Icon /></span><span><strong>{profile.label}</strong><small>{profile.description}</small></span><span className="role-option-check"><Check /></span></label>; })}</div></fieldset>; }

function AuthPage({ mode, onAuthenticated }: { mode: "login" | "register"; onAuthenticated: (role: Role, pending: boolean) => void }) {
  const register = mode === "register"; const [showPassword, setShowPassword] = useState(false); const [email, setEmail] = useState(""); const [requestedRole, setRequestedRole] = useState<Role>("business_user"); const [status, setStatus] = useState(""); const [submitting, setSubmitting] = useState(false);
  useEffect(() => { setRequestedRole(storedRole()); }, []);
  function submit(event: FormEvent) { event.preventDefault(); if (submitting) return; setSubmitting(true); const detectedRole = roleFromAccount(email); setStatus(register ? "Đã ghi nhận role mong muốn. Đang mở giao diện xem trước…" : `Tài khoản đã nhận diện là ${roles[detectedRole].label}. Đang mở giao diện…`); window.setTimeout(() => onAuthenticated(register ? requestedRole : detectedRole, register), 850); }
  return <main className="auth-page content-view"><section className="auth-story"><button className="auth-brand" type="button" onClick={() => go("dashboard")}><BrandMark /><span><strong>AtlasIQ</strong><small>Semantic analytics</small></span></button><div className="auth-story-copy"><h1>{register ? <>Một không gian chung.<br />Đúng quyền cho từng người.</> : <>Mỗi nhiệm vụ.<br />Một trải nghiệm riêng.</>}</h1><p>{register ? "Chọn vai trò phù hợp; Workspace Admin sẽ phê duyệt trước khi quyền có hiệu lực." : "Sau đăng nhập, AtlasIQ tự nhận diện tài khoản và đưa bạn thẳng tới dashboard đúng với nhiệm vụ được giao."}</p></div><div className="auth-proof"><span><ShieldCheck />Role-based access</span><span><Check />Data scope độc lập</span><span><Clock3 />Audit mọi thay đổi</span></div></section><section className="auth-form-side"><div className="auth-form-wrap"><button className="back-button" type="button" onClick={() => go("dashboard")}><ArrowLeft />Quay lại dashboard</button><form className="auth-form" onSubmit={submit}><h2>{register ? "Tạo tài khoản" : "Đăng nhập"}</h2><p>{register ? "Dùng email công việc và chọn role phù hợp." : "Role được nhận tự động từ tài khoản sau khi xác thực."}</p>{register && <AuthField id="full-name" label="Họ và tên" icon={<User />} type="text" placeholder="Nguyễn Minh Anh" />}<AuthField id="auth-email" label="Email công việc" icon={<Mail />} type="email" placeholder="ban@company.vn" value={email} onChange={setEmail} />{!register && <p className="account-role-hint">Bản demo nhận diện từ email có chứa: <strong>admin</strong>, <strong>steward</strong>, <strong>analyst</strong> hoặc <strong>audit</strong>. Tài khoản khác dùng Business User.</p>}<div className="auth-field"><label htmlFor="auth-password">Mật khẩu</label><div><KeyRound /><input id="auth-password" type={showPassword ? "text" : "password"} placeholder="Tối thiểu 8 ký tự" required minLength={8} /><button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}>{showPassword ? <EyeOff /> : <Eye />}</button></div></div>{register && <RoleSelector selected={requestedRole} onChange={setRequestedRole} />}{register ? <label className="terms-check"><input type="checkbox" required />Tôi đồng ý với chính sách sử dụng dữ liệu.</label> : <div className="auth-options"><label><input type="checkbox" />Duy trì đăng nhập</label><button type="button">Quên mật khẩu?</button></div>}<div className={`role-security-note ${register ? "approval" : "demo"}`}><ShieldCheck /><p>{register ? <><strong>Role này là đề nghị.</strong> Workspace Admin phải phê duyệt trước khi backend cấp quyền.</> : <><strong>Tài khoản tự quyết định role.</strong> Bản demo chỉ mô phỏng; production phải lấy role và data scope từ session do backend xác thực.</>}</p></div><button className="auth-submit" type="submit" disabled={submitting}>{submitting ? <LoaderCircle className="spin" /> : register ? <UserCheck /> : <LockKeyhole />}{register ? "Gửi yêu cầu vai trò" : "Đăng nhập"}<ArrowRight /></button><div className="auth-status" aria-live="polite">{status}</div><p className="auth-switch">{register ? "Đã có tài khoản?" : "Chưa có tài khoản?"} <button type="button" onClick={() => go(register ? "login" : "register")}>{register ? "Đăng nhập" : "Đăng ký"}</button></p></form><p className="demo-note"><ShieldCheck />Credential không được gửi ra ngoài trong frontend demo.</p></div></section></main>;
}
function AuthField({ id, label, icon, type, placeholder, value, onChange }: { id: string; label: string; icon: ReactNode; type: string; placeholder: string; value?: string; onChange?: (value: string) => void }) { return <div className="auth-field"><label htmlFor={id}>{label}</label><div>{icon}<input id={id} type={type} placeholder={placeholder} required value={value} onChange={onChange ? (event) => onChange(event.target.value) : undefined} /></div></div>; }

export default function RoleApp() {
  const [view, setView] = useState<View>("dashboard"); const [role, setRole] = useState<Role>("analyst"); const [pending, setPending] = useState(false);
  useEffect(() => { const sync = () => setView(currentView()); setRole(storedRole()); setPending(window.sessionStorage.getItem("atlasiq_role_pending") === "true"); sync(); window.addEventListener("hashchange", sync); if (!window.location.hash) go("dashboard"); return () => window.removeEventListener("hashchange", sync); }, []);
  function authenticate(nextRole: Role, nextPending: boolean) { window.sessionStorage.setItem(DEMO_ROLE_STORAGE_KEY, nextRole); window.sessionStorage.setItem("atlasiq_role_pending", String(nextPending)); setRole(nextRole); setPending(nextPending); go("dashboard"); }
  if (view === "login" || view === "register") return <RouteMotion motionKey={view}><AuthPage mode={view} onAuthenticated={authenticate} /></RouteMotion>;
  const allowed = navigation[role].some(({ id }) => id === view); let content: ReactNode;
  if (!allowed) content = <AccessDenied role={role} />; else if (view === "dashboard") content = <Dashboard role={role} />; else if (view === "query") content = <QueryWorkspace role={role} />; else if (view === "conversations" || view === "metrics" || view === "audit") content = <CollectionPage type={view} role={role} />; else content = <SectionPage type={view as SectionView} />;
  return <ProductShell view={view} role={role} pending={pending}><RouteMotion motionKey={`${role}-${view}`}>{content}</RouteMotion></ProductShell>;
}
