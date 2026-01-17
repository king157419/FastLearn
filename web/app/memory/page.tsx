"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Brain,
  User,
  MessageSquare,
  Clock,
  BookOpen,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Target,
  Calendar,
  Loader2,
  RefreshCw,
  Settings,
  Sparkles,
} from "lucide-react";
import { apiUrl } from "@/lib/api";
import { useGlobal } from "@/context/GlobalContext";

interface UserProfile {
  id: number;
  user_id: string;
  preferences: {
    language: string;
    include_code: boolean;
    include_math: boolean;
    learning_style: string;
    response_format: string;
    difficulty_preference: string;
  };
  statistics: {
    active_days: number;
    total_sessions: number;
    total_questions: number;
    last_active_date: string | null;
    most_active_hour: number | null;
    avg_session_length: number;
  };
  interests: string[];
  weak_points: Array<{
    concept: string;
    confusion_score: number;
  }>;
  created_at: string;
  updated_at: string;
}

interface SessionSummary {
  id: number;
  session_id: string;
  user_id: string;
  core_topic: string;
  key_points: string[];
  resolved_questions: string[];
  unresolved_questions: string[];
  subject: string;
  topic: string;
  difficulty: string;
  message_count: number;
  token_count: number;
  created_at: string;
  updated_at: string;
}

interface MemoryStats {
  totalSessions: number;
  totalTopics: number;
  totalQuestions: number;
  activeDays: number;
}

export default function MemoryPage() {
  const router = useRouter();
  const { uiSettings } = useGlobal();
  const lang = uiSettings.language;
  const t = (key: string) => {
    const translations: Record<string, Record<string, string>> = {
      en: {
        "Memory & Profile": "Memory & Profile",
        "Your learning profile and conversation history":
          "Your learning profile and conversation history",
        Overview: "Overview",
        "User Profile": "User Profile",
        "Session Summaries": "Session Summaries",
        "Loading...": "Loading...",
        "No memory data found": "No memory data found",
        "Start chatting to build your learning profile!":
          "Start chatting to build your learning profile!",
        "Total Sessions": "Total Sessions",
        "Total Questions": "Total Questions",
        "Active Days": "Active Days",
        "Topics Covered": "Topics Covered",
        "Learning Style": "Learning Style",
        "Difficulty Preference": "Difficulty Preference",
        "Preferred Language": "Preferred Language",
        "Include Code": "Include Code",
        "Include Math": "Include Math",
        "Weak Points": "Weak Points",
        "Interests": "Interests",
        "Recent Sessions": "Recent Sessions",
        "Core Topic": "Core Topic",
        "Key Points": "Key Points",
        "Resolved Questions": "Resolved Questions",
        "Unresolved Questions": "Unresolved Questions",
        "Subject": "Subject",
        "Difficulty": "Difficulty",
        "Messages": "Messages",
        "Date": "Date",
        "No sessions yet": "No sessions yet",
        "Refresh": "Refresh",
        "User ID": "User ID",
        "Last Active": "Last Active",
        "Average Session Length": "Average Session Length",
        "Most Active Hour": "Most Active Hour",
        "Conversation Summary": "Conversation Summary",
        "Your AI learning companion builds a profile of your learning journey":
          "Your AI learning companion builds a profile of your learning journey",
        "Visual Style": "visual",
        "Textual Style": "textual",
        "Hands-on Style": "hands_on",
        "Code First Style": "code_first",
        "Beginner": "Beginner",
        "Intermediate": "Intermediate",
        "Advanced": "Advanced",
      },
      zh: {
        "Memory & Profile": "记忆与画像",
        "Your learning profile and conversation history": "您的学习画像和对话历史",
        Overview: "概览",
        "User Profile": "用户画像",
        "Session Summaries": "会话摘要",
        "Loading...": "加载中...",
        "No memory data found": "未找到记忆数据",
        "Start chatting to build your learning profile!": "开始聊天以建立您的学习画像！",
        "Total Sessions": "总会话数",
        "Total Questions": "总问题数",
        "Active Days": "活跃天数",
        "Topics Covered": "涵盖主题",
        "Learning Style": "学习风格",
        "Difficulty Preference": "难度偏好",
        "Preferred Language": "偏好语言",
        "Include Code": "包含代码",
        "Include Math": "包含数学",
        "Weak Points": "薄弱知识点",
        "Interests": "兴趣领域",
        "Recent Sessions": "最近会话",
        "Core Topic": "核心主题",
        "Key Points": "关键知识点",
        "Resolved Questions": "已解决问题",
        "Unresolved Questions": "未解决问题",
        "Subject": "学科",
        "Difficulty": "难度",
        "Messages": "消息数",
        "Date": "日期",
        "No sessions yet": "暂无会话",
        "Refresh": "刷新",
        "User ID": "用户ID",
        "Last Active": "最后活跃",
        "Average Session Length": "平均会话长度",
        "Most Active Hour": "最活跃时段",
        "Conversation Summary": "对话摘要",
        "Your AI learning companion builds a profile of your learning journey":
          "您的 AI 学习助手会建立您学习历程的画像",
        "Visual Style": "视觉型",
        "Textual Style": "文字型",
        "Hands-on Style": "动手型",
        "Code First Style": "代码优先型",
        "Beginner": "初学者",
        "Intermediate": "中级",
        "Advanced": "高级",
      },
    };
    return translations[lang]?.[key] || translations.en[key] || key;
  };

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [summaries, setSummaries] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<MemoryStats>({
    totalSessions: 0,
    totalTopics: 0,
    totalQuestions: 0,
    activeDays: 0,
  });
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  // Get userId from localStorage (same key as GlobalContext)
  // Must be called after component mounts due to SSR
  const getUserId = (): string => {
    if (typeof window === "undefined") {
      return ""; // SSR: return empty string, will be set in useEffect
    }
    const key = "deeptutor-user-id";  // Must match GlobalContext.tsx
    let userId = localStorage.getItem(key);
    if (!userId) {
      userId = `user_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      localStorage.setItem(key, userId);
    }
    return userId;
  };

  const loadMemoryData = async (userIdParam: string, showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      // Load profile
      const profileRes = await fetch(apiUrl(`/api/memory/profiles/${userIdParam}`));
      let profileData: UserProfile | null = null;

      if (profileRes.ok) {
        profileData = await profileRes.json();
        setProfile(profileData);
      }

      // Load session summaries
      const sessionsRes = await fetch(
        apiUrl(`/api/memory/sessions/${userIdParam}/list?days=30&limit=20`)
      );
      if (sessionsRes.ok) {
        const sessionsData = await sessionsRes.json();
        const summariesList = sessionsData.sessions || sessionsData || [];
        setSummaries(Array.isArray(summariesList) ? summariesList : []);

        // Calculate stats
        setStats({
          totalSessions: Array.isArray(summariesList) ? summariesList.length : 0,
          totalTopics: Array.isArray(summariesList)
            ? new Set(summariesList.map((s: SessionSummary) => s.topic)).size
            : 0,
          totalQuestions: Array.isArray(summariesList)
            ? summariesList.reduce(
                (acc: number, s: SessionSummary) =>
                  acc + (s.resolved_questions?.length || 0),
                0
              )
            : 0,
          activeDays: profileData?.statistics?.active_days || 0,
        });
      }
    } catch (e) {
      console.error("Failed to load memory data:", e);
      setError(lang === "zh" ? "加载数据失败" : "Failed to load data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Set userId on mount (after client-side hydration)
  useEffect(() => {
    const userId = getUserId();
    if (userId) {
      setCurrentUserId(userId);
      loadMemoryData(userId);
    }
  }, []);

  const formatLearningStyle = (style: string) => {
    const styleMap: Record<string, string> = {
      visual: t("Visual Style"),
      textual: t("Textual Style"),
      hands_on: t("Hands-on Style"),
      code_first: t("Code First Style"),
    };
    return styleMap[style] || style;
  };

  const formatDifficulty = (difficulty: string) => {
    const diffMap: Record<string, string> = {
      beginner: t("Beginner"),
      intermediate: t("Intermediate"),
      advanced: t("Advanced"),
    };
    return diffMap[difficulty] || difficulty;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString(lang === "zh" ? "zh-CN" : "en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const hasData = profile || summaries.length > 0;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <div className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <Brain className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {t("Memory & Profile")}
                </h1>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                  {t("Your learning profile and conversation history")}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                if (currentUserId) {
                  loadMemoryData(currentUserId, true);
                }
              }}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              {t("Refresh")}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {!hasData ? (
          /* Empty State */
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
              <Sparkles className="w-10 h-10 text-slate-400" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
              {t("No memory data found")}
            </h2>
            <p className="text-slate-500 dark:text-slate-400">
              {t("Start chatting to build your learning profile!")}
            </p>
            <a
              href="/"
              className="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
            >
              <MessageSquare className="w-5 h-5" />
              {lang === "zh" ? "开始聊天" : "Start Chatting"}
            </a>
          </div>
        ) : (
          <>
            {/* Stats Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                icon={<MessageSquare className="w-5 h-5" />}
                label={t("Total Sessions")}
                value={stats.totalSessions}
                color="blue"
              />
              <StatCard
                icon={<Target className="w-5 h-5" />}
                label={t("Total Questions")}
                value={stats.totalQuestions}
                color="green"
              />
              <StatCard
                icon={<Calendar className="w-5 h-5" />}
                label={t("Active Days")}
                value={stats.activeDays}
                color="purple"
              />
              <StatCard
                icon={<BookOpen className="w-5 h-5" />}
                label={t("Topics Covered")}
                value={stats.totalTopics}
                color="orange"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* User Profile Card */}
              <div className="lg:col-span-1">
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                        <User className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h2 className="text-lg font-semibold text-white">
                          {t("User Profile")}
                        </h2>
                        <p className="text-xs text-white/70">
                          {t("User ID")}: {currentUserId ? currentUserId.slice(0, 12) : "Loading..."}...
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 space-y-6">
                    {profile ? (
                      <>
                        {/* Learning Preferences */}
                        <div>
                          <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
                            {lang === "zh" ? "学习偏好" : "Learning Preferences"}
                          </h3>
                          <div className="space-y-3">
                            <PreferenceRow
                              label={t("Learning Style")}
                              value={formatLearningStyle(
                                profile.preferences.learning_style
                              )}
                            />
                            <PreferenceRow
                              label={t("Difficulty Preference")}
                              value={formatDifficulty(
                                profile.preferences.difficulty_preference
                              )}
                            />
                            <PreferenceRow
                              label={t("Preferred Language")}
                              value={profile.preferences.language.toUpperCase()}
                            />
                          </div>
                        </div>

                        {/* Statistics */}
                        <div>
                          <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
                            {lang === "zh" ? "统计数据" : "Statistics"}
                          </h3>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-slate-500 dark:text-slate-400">
                                {t("Total Sessions")}
                              </span>
                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                {profile.statistics.total_sessions}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500 dark:text-slate-400">
                                {t("Last Active")}
                              </span>
                              <span className="font-medium text-slate-900 dark:text-slate-100">
                                {formatDate(profile.statistics.last_active_date)}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Weak Points */}
                        {profile.weak_points && profile.weak_points.length > 0 && (
                          <div>
                            <h3 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                              <AlertCircle className="w-3.5 h-3.5 text-orange-500" />
                              {t("Weak Points")}
                            </h3>
                            <div className="space-y-2">
                              {profile.weak_points.slice(0, 3).map((wp, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center justify-between p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg"
                                >
                                  <span className="text-sm text-slate-700 dark:text-slate-300">
                                    {wp.concept}
                                  </span>
                                  <span className="text-xs font-medium text-orange-600 dark:text-orange-400">
                                    {Math.round(wp.confusion_score * 100)}%
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-center py-8 text-slate-400">
                        <User className="w-10 h-10 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">
                          {lang === "zh" ? "暂无画像数据" : "No profile data yet"}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Session Summaries */}
              <div className="lg:col-span-2">
                <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-blue-500" />
                      {t("Session Summaries")}
                    </h2>
                    <span className="text-sm text-slate-400">
                      {summaries.length} {lang === "zh" ? "个会话" : "sessions"}
                    </span>
                  </div>

                  <div className="divide-y divide-slate-100 dark:divide-slate-700 max-h-[700px] overflow-y-auto">
                    {summaries.length > 0 ? (
                      summaries.map((session) => (
                        <div
                          key={session.id}
                          className="p-6 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">
                                {session.core_topic}
                              </h3>
                              <div className="flex items-center gap-3 text-xs text-slate-500">
                                <span className="flex items-center gap-1">
                                  <Calendar className="w-3 h-3" />
                                  {formatDate(session.created_at)}
                                </span>
                                <span className="flex items-center gap-1">
                                  <MessageSquare className="w-3 h-3" />
                                  {session.message_count} {t("Messages")}
                                </span>
                                {session.subject && (
                                  <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                                    {session.subject}
                                  </span>
                                )}
                              </div>
                            </div>
                            {session.difficulty && (
                              <span
                                className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                                  session.difficulty === "beginner"
                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                                    : session.difficulty === "intermediate"
                                    ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300"
                                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                                }`}
                              >
                                {formatDifficulty(session.difficulty)}
                              </span>
                            )}
                          </div>

                          {/* Key Points */}
                          {session.key_points && session.key_points.length > 0 && (
                            <div className="mb-4">
                              <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1">
                                <Lightbulb className="w-3 h-3" />
                                {t("Key Points")}
                              </h4>
                              <ul className="space-y-1">
                                {session.key_points.slice(0, 3).map((point, idx) => (
                                  <li
                                    key={idx}
                                    className="text-sm text-slate-600 dark:text-slate-300 flex items-start gap-2"
                                  >
                                    <span className="text-blue-500 mt-0.5">•</span>
                                    <span>{point}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Questions */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {session.resolved_questions &&
                              session.resolved_questions.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-medium text-green-600 dark:text-green-400 mb-2 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" />
                                    {t("Resolved Questions")} ({session.resolved_questions.length})
                                  </h4>
                                  <ul className="space-y-1">
                                    {session.resolved_questions
                                      .slice(0, 2)
                                      .map((q, idx) => (
                                        <li
                                          key={idx}
                                          className="text-xs text-slate-500 dark:text-slate-400 truncate"
                                        >
                                          {q}
                                        </li>
                                      ))}
                                  </ul>
                                </div>
                              )}
                            {session.unresolved_questions &&
                              session.unresolved_questions.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-medium text-orange-600 dark:text-orange-400 mb-2 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" />
                                    {t("Unresolved Questions")} ({session.unresolved_questions.length})
                                  </h4>
                                  <ul className="space-y-1">
                                    {session.unresolved_questions
                                      .slice(0, 2)
                                      .map((q, idx) => (
                                        <li
                                          key={idx}
                                          className="text-xs text-slate-500 dark:text-slate-400 truncate"
                                        >
                                          {q}
                                        </li>
                                      ))}
                                  </ul>
                                </div>
                              )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-12 text-center text-slate-400">
                        <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>{t("No sessions yet")}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: "blue" | "green" | "purple" | "orange";
}) {
  const colorClasses = {
    blue: "bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400",
    green: "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400",
    purple: "bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400",
    orange: "bg-orange-50 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400",
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-5">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <div>
          <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {value}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        </div>
      </div>
    </div>
  );
}

function PreferenceRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-700 last:border-0">
      <span className="text-sm text-slate-500 dark:text-slate-400">{label}</span>
      <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
        {value}
      </span>
    </div>
  );
}
