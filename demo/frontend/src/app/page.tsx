"use client";

import { useState, useRef, useEffect, useMemo, FormEvent } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const DEVELOPER_SUGGESTIONS = [
  "ما هي نقاط الوصول المتاحة للمنتجات؟",
  "أريد البحث عن endpoints الخاصة بالطلبات",
  "كيف أستخدم API لإضافة منتج جديد؟",
  "كم عدد الـ endpoints المتاحة في الـ API؟",
];

const STORE_OWNER_SUGGESTIONS = [
  "اعرض لي آخر 5 طلبات في متجري",
  "كم إجمالي الطلبات في 2025؟",
  "اعرض لي قائمة المنتجات مع الأسعار",
  "ما حالة الطلبات الأخيرة؟",
];

// Follow-up suggestions based on keywords in the last assistant message
const FOLLOWUPS: Record<string, string[]> = {
  "منتج|منتجات|products": [
    "اعرض تفاصيل أول منتج",
    "كم عدد المنتجات المتوفرة؟",
    "ابحث عن endpoints تعديل المنتجات",
  ],
  "طلب|طلبات|orders": [
    "اعرض تفاصيل آخر طلب",
    "ما هي حالات الطلبات المتاحة؟",
    "كم إجمالي المبيعات؟",
  ],
  "عميل|عملاء|customers": [
    "كم عدد العملاء الإجمالي؟",
    "اعرض بيانات أول عميل",
    "ابحث عن endpoints تسجيل العملاء",
  ],
  "endpoint|نقاط الوصول|نقطة": [
    "اعرض endpoints الطلبات",
    "ابحث عن endpoints الشحن",
    "كيف أستدعي endpoint معين؟",
  ],
  "شحن|shipping": [
    "ما هي شركات الشحن المتاحة؟",
    "اعرض endpoints الشحن",
    "كيف أتتبع شحنة؟",
  ],
};

const DEFAULT_FOLLOWUPS = [
  "اعرض لي المنتجات",
  "كم عدد الطلبات؟",
  "ابحث عن endpoints الدفع",
  "ما هي الـ endpoints الأكثر استخداماً؟",
];

function getFollowups(lastMessage: string): string[] {
  const matched: string[] = [];
  for (const [keywords, suggestions] of Object.entries(FOLLOWUPS)) {
    const patterns = keywords.split("|");
    if (patterns.some((p) => lastMessage.includes(p))) {
      matched.push(...suggestions);
    }
  }
  if (matched.length === 0) return DEFAULT_FOLLOWUPS.slice(0, 3);
  // Deduplicate and limit to 3
  return [...new Set(matched)].slice(0, 3);
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const followups = useMemo(() => {
    if (messages.length === 0) return [];
    const last = messages[messages.length - 1];
    if (last.role !== "assistant") return [];
    return getFollowups(last.content);
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", content: text.trim() };
    const updated = [...messages, userMsg];
    setMessages(updated);
    setInput("");
    setLoading(true);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 120000);
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: updated }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await res.json();
      setMessages([...updated, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([
        ...updated,
        { role: "assistant", content: "فشل الاتصال بالخادم. هل الخادم يعمل على المنفذ 8888؟" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <main className="container">
      <header>
        <div className="header-row">
          <div>
            <h1>وكيل سلة الذكي</h1>
            <p>اسألني أي شيء عن واجهة برمجة تطبيقات سلة</p>
          </div>
          {messages.length > 0 && (
            <button className="reset-btn" onClick={() => setMessages([])}>
              محادثة جديدة
            </button>
          )}
        </div>
      </header>

      <div className="chat">
        {messages.length === 0 && (
          <div className="welcome">
            <div className="tools-showcase">
              <h3>الأدوات المتاحة</h3>
              <div className="tools-grid">
                <div className="tool-card">
                  <div className="tool-icon">&#x1F50D;</div>
                  <div className="tool-info">
                    <h4>بحث في الـ API</h4>
                    <p>ابحث عن أي endpoint في واجهة سلة البرمجية بالكلمات المفتاحية</p>
                    <span className="tool-tag">search_api</span>
                  </div>
                </div>
                <div className="tool-card">
                  <div className="tool-icon">&#x26A1;</div>
                  <div className="tool-info">
                    <h4>تنفيذ طلب API</h4>
                    <p>نفّذ أي استدعاء API مباشرة — GET, POST, PUT, DELETE</p>
                    <span className="tool-tag">execute_api</span>
                  </div>
                </div>
                <div className="tool-card">
                  <div className="tool-icon">&#x1F4E6;</div>
                  <div className="tool-info">
                    <h4>عرض الطلبات</h4>
                    <p>اعرض طلبات المتجر مع إمكانية الفلترة حسب الحالة</p>
                    <span className="tool-tag">list_orders</span>
                  </div>
                </div>
                <div className="tool-card">
                  <div className="tool-icon">&#x1F4CA;</div>
                  <div className="tool-info">
                    <h4>لوحة المتجر</h4>
                    <p>نظرة عامة سريعة: عدد المنتجات، الطلبات، وآخر النشاطات</p>
                    <span className="tool-tag">store_dashboard</span>
                  </div>
                </div>
                <div className="tool-card">
                  <div className="tool-icon">&#x1F4B0;</div>
                  <div className="tool-info">
                    <h4>تقرير المبيعات</h4>
                    <p>تقرير مبيعات لفترة محددة مع الإيرادات ومتوسط الطلبات</p>
                    <span className="tool-tag">sales_report</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="suggestions-section">
              <h3>جرّب — للمطورين</h3>
              <div className="suggestions">
                {DEVELOPER_SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => send(s)} className="suggestion">
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="suggestions-section">
              <h3>جرّب — لأصحاب المتاجر</h3>
              <div className="suggestions">
                {STORE_OWNER_SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => send(s)} className="suggestion">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="bubble">
              {msg.role === "assistant" ? (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {!loading && followups.length > 0 && (
          <div className="followups">
            {followups.map((f) => (
              <button key={f} onClick={() => send(f)} className="followup">
                {f}
              </button>
            ))}
          </div>
        )}

        {loading && (
          <div className="message assistant">
            <div className="bubble loading-dots">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="اسأل عن واجهة سلة البرمجية..."
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          إرسال
        </button>
      </form>
    </main>
  );
}
