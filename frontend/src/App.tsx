
import { useState, useEffect } from "react";
import axios from "axios";
import {
  BarChart3,
  Bot,
  Send,
  LayoutDashboard,
  MessageSquare,
  Package,
  Users,
  Globe,
  TrendingUp,
  Loader2,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

function App() {
  // Chat states
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[]
  >([
    {
      role: "assistant",
      content:
        "Hello! I'm your E-commerce AI Analyst. Ask me about revenue, products, customers, sales trends or business performance.",
    },
  ]);

  const [loading, setLoading] = useState(false);

  const [threadId] = useState(
    () => `user_${Date.now()}`
  );

  // Analytics states
  const [analytics, setAnalytics] = useState({
    total_revenue: 0,
    total_quantity: 0,
    total_invoices: 0,
    unique_customers: 0,
    total_countries: 0,
  });

  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  // Fetch analytics when dashboard loads
  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/analytics/summary`
        );

        setAnalytics(response.data);
      } catch (error) {
        console.error("Failed to fetch analytics:", error);
      } finally {
        setAnalyticsLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  // Send question to AI agent
  const sendMessage = async () => {
    if (!question.trim() || loading) return;

    const userQuestion = question.trim();

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userQuestion },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        question: userQuestion,
        thread_id: threadId,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.data.answer,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I couldn't process your request. Please check that the backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };
  const [activeTab, setActiveTab] = useState("dashboard");

  // Dynamic KPI cards
  const kpis = [
    {
      title: "Total Revenue",
      value: `£${analytics.total_revenue.toLocaleString("en-GB", {
        maximumFractionDigits: 2,
      })}`,
      icon: TrendingUp,
    },
    {
      title: "Units Sold",
      value: analytics.total_quantity.toLocaleString(),
      icon: Package,
    },
    {
      title: "Total Invoices",
      value: analytics.total_invoices.toLocaleString(),
      icon: BarChart3,
    },
    {
      title: "Total Customers",
      value: analytics.unique_customers.toLocaleString(),
      icon: Users,
    },
    {
      title: "Countries Served",
      value: analytics.total_countries.toLocaleString(),
      icon: Globe,
    },
  ];

  return (
    <div className="min-h-screen bg-[#0b1120] text-white flex">

      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 p-6 hidden md:block">
        <div className="flex items-center gap-3 mb-12">
          <div className="bg-blue-600 p-2 rounded-lg">
            <BarChart3 size={23} />
          </div>

          <div>
            <h1 className="font-bold text-lg">RetailIQ</h1>
            <p className="text-xs text-slate-400">
              AI Analytics
            </p>
          </div>
        </div>

        <p className="text-xs text-slate-500 mb-4 uppercase">
          Workspace
        </p>


<nav className="space-y-3">
  <button
    onClick={() => {
      setActiveTab("dashboard");
      document.getElementById("dashboard")?.scrollIntoView({
        behavior: "smooth",
      });
    }}
    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition ${
      activeTab === "dashboard"
        ? "bg-blue-600/20 text-blue-400"
        : "text-slate-400 hover:bg-slate-800"
    }`}
  >
    <LayoutDashboard size={18} />
    Dashboard
  </button>

  <button
    onClick={() => {
      setActiveTab("analyst");
      document.getElementById("analyst")?.scrollIntoView({
        behavior: "smooth",
      });
    }}
    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition ${
      activeTab === "analyst"
        ? "bg-blue-600/20 text-blue-400"
        : "text-slate-400 hover:bg-slate-800"
    }`}
  >
    <MessageSquare size={18} />
    AI Analyst
  </button>
</nav>


        <div className="mt-12 border-t border-slate-800 pt-6">
          <p className="text-xs text-slate-500">
            DATA SOURCE
          </p>

          <p className="text-sm mt-3">
            Online Retail Dataset
          </p>

          <p className="text-xs text-green-400 mt-2">
            ● PostgreSQL Connected
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main
            id="dashboard"
            className="flex-1 p-5 md:p-8 max-w-7xl mx-auto w-full"
          >

        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold">
              E-commerce Dashboard
            </h2>

            <p className="text-slate-400 text-sm mt-1">
              Business performance and AI-powered insights
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-green-400">
            <span>●</span> System Online
          </div>
        </header>

        {/* KPI Cards */}
        <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
          {kpis.map((item) => {
            const Icon = item.icon;

            return (
              <div
                key={item.title}
                className="bg-[#151e30] border border-slate-800 rounded-xl p-5"
              >
                <div className="flex justify-between items-center">
                  <p className="text-sm text-slate-400">
                    {item.title}
                  </p>

                  <Icon
                    size={20}
                    className="text-blue-400"
                  />
                </div>

                <h3 className="text-2xl font-bold mt-4">
                  {analyticsLoading ? "Loading..." : item.value}
                </h3>
              </div>
            );
          })}
        </section>

        {/* AI Chat */}
        <section
                id="analyst"
                className="bg-[#151e30] border border-slate-800 rounded-xl overflow-hidden"
              >

          <div className="p-5 border-b border-slate-800 flex items-center gap-3">
            <div className="bg-blue-600/20 p-2 rounded-lg">
              <Bot className="text-blue-400" size={22} />
            </div>

            <div>
              <h3 className="font-semibold">
                AI Business Analyst
              </h3>

              <p className="text-xs text-slate-400">
                Powered by LangGraph and PostgreSQL
              </p>
            </div>
          </div>

          <div className="h-[400px] overflow-y-auto p-5 space-y-5">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-xl p-4 text-sm whitespace-pre-wrap ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "bg-slate-800 text-slate-200"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Loader2 className="animate-spin" size={18} />
                Analyzing your business data...
              </div>
            )}
          </div>

          <div className="p-4 border-t border-slate-800">
            <div className="flex gap-3">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") sendMessage();
                }}
                placeholder="Ask about your business..."
                className="flex-1 bg-[#0b1120] border border-slate-700 rounded-lg px-4 py-3 outline-none focus:border-blue-500 text-sm"
              />

              <button
                onClick={sendMessage}
                disabled={loading || !question.trim()}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg px-5"
              >
                <Send size={19} />
              </button>
            </div>
          </div>

        </section>
      </main>
    </div>
  );
}

export default App;
