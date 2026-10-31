import { useEffect, useState } from "react";

// 新闻分类颜色配置
function getCategoryStyle(category) {
  const colors = {
    国际政治: "#4285f4", // 蓝色
    国内政策: "#34a853", // 绿色
    宏观经济: "#fbbc04", // 黄色
    股市: "#ea4335", // 红色
    债券: "#a142f4", // 紫色
    大宗商品: "#00acc1", // 青色
    其他: "#9aa0a6", // 灰色
  };

  const color = colors[category] || colors["其他"];

  return {
    color,
    background: `${color}20`,
  };
}

// 将新闻更新时间转换为相对时间
function formatTimeAgo(timeString) {
  if (!timeString) return "等待更新";

  // 将后端时间字符串转换为本地时间
  const updateTime = new Date(timeString.replace(" ", "T"));

  if (Number.isNaN(updateTime.getTime())) {
    return "时间未知";
  }

  const diffSeconds = Math.floor((Date.now() - updateTime.getTime()) / 1000);

  if (diffSeconds < 0) return "刚刚更新";
  if (diffSeconds < 60) return "刚刚更新";

  const diffMinutes = Math.floor(diffSeconds / 60);

  if (diffMinutes < 60) {
    return `${diffMinutes} 分钟前`;
  }

  const diffHours = Math.floor(diffMinutes / 60);

  if (diffHours < 24) {
    return `${diffHours} 小时前`;
  }

  const diffDays = Math.floor(diffHours / 24);

  return `${diffDays} 天前`;
}

export default function NewsSection() {
  const [newsData, setNewsData] = useState({
    news: [],
    updated_at: "",
  });

  const [isOnline, setIsOnline] = useState(false);

  const [currentTime, setCurrentTime] = useState(Date.now());

  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("全部");

  const categories = [
    "国际政治",
    "国内政策",
    "宏观经济",
    "股市",
    "债券",
    "大宗商品",
  ];

  useEffect(() => {
    let isMounted = true;

    const fetchNews = async () => {
      try {
        const res = await fetch("/api/news/latest");

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }

        const data = await res.json();

        if (isMounted) {
          setNewsData(data);
          setIsOnline(true);
        }
      } catch (err) {
        console.error("获取新闻失败:", err);

        if (isMounted) {
          setIsOnline(false);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // 页面加载后立即获取一次
    fetchNews();

    // 每 30 秒自动获取最新新闻
    const timer = setInterval(fetchNews, 30 * 1000);

    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  // 每 30 秒更新一次当前时间，用于刷新相对更新时间
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(Date.now());
    }, 30 * 1000);

    return () => clearInterval(timer);
  }, []);

  const news = Array.isArray(newsData.news) ? newsData.news : [];

  // 如果存在其他分类的新闻，才显示「其他」标签
  const hasOther = news.some((item) => item.category === "其他");

  const availableCategories = [
    "全部",
    ...categories,
    ...(hasOther ? ["其他"] : []),
  ];

  // 根据当前选中的分类筛选新闻
  const filteredNews =
    activeCategory === "全部"
      ? news
      : news.filter((item) => item.category === activeCategory);

  // 统计每个分类的新闻数量
  const getCategoryCount = (category) => {
    if (category === "全部") {
      return news.length;
    }

    return news.filter((item) => item.category === category).length;
  };

  return (
    <section style={{ marginTop: 32 }}>
      {/* 标题区域 */}

      {/* 标题区域 */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
          marginBottom: 16,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <h2
            style={{
              fontSize: 15,
              fontWeight: 500,
              color: "#9aa0a6",
              margin: 0,
              letterSpacing: 0.5,
            }}
          >
            实时政经要闻
          </h2>

          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 9px",
              borderRadius: 20,
              background: isOnline ? "#34a85318" : "#ea433518",
              color: isOnline ? "#34a853" : "#ea4335",
              fontSize: 11,
              fontWeight: 500,
            }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: isOnline ? "#34a853" : "#ea4335",
                boxShadow: isOnline ? "0 0 6px #34a85380" : "0 0 6px #ea433580",
              }}
            />
            {isOnline ? "实时更新" : "连接失败"}
          </span>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "#5f6368",
            }}
          >
            每 30 秒刷新
          </span>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 4,
              alignItems: "flex-end",
            }}
          >
            <span
              style={{
                fontSize: 12,
                color: "#9aa0a6",
              }}
            >
              最后更新：{newsData.updated_at || "等待更新"}
            </span>

            <span
              style={{
                fontSize: 11,
                color: "#34a853",
              }}
            >
              {currentTime && formatTimeAgo(newsData.updated_at)}
            </span>
          </div>
        </div>
      </div>

      {/* 7×24 全球直播入口 */}
      <a
        href="https://kuaixun.eastmoney.com/"
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 20px",
          marginBottom: 20,
          background: "#1a1d23",
          border: "1px solid #2a2e36",
          borderRadius: 10,
          textDecoration: "none",
          transition: "all 0.15s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "#4285f4";
          e.currentTarget.style.transform = "translateY(-2px)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "#2a2e36";
          e.currentTarget.style.transform = "none";
        }}
      >
        <div>
          <div
            style={{
              color: "#e8eaed",
              fontSize: 15,
              fontWeight: 600,
              marginBottom: 5,
            }}
          >
            7×24 全球直播
          </div>
          <div
            style={{
              color: "#9aa0a6",
              fontSize: 12,
            }}
          >
            查看东方财富全球财经实时快讯
          </div>
        </div>

        <span
          style={{
            color: "#4285f4",
            fontSize: 20,
          }}
        >
          ↗
        </span>
      </a>

      {/* 新闻分类标签 */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          marginBottom: 20,
        }}
      >
        {availableCategories.map((category) => {
          const isActive = activeCategory === category;

          return (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              style={{
                padding: "7px 12px",
                borderRadius: 6,
                border: `1px solid ${isActive ? "#4285f4" : "#2a2e36"}`,
                background: isActive ? "#4285f420" : "#1a1d23",
                color: isActive ? "#4285f4" : "#9aa0a6",
                fontSize: 12,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {category}
              <span style={{ marginLeft: 6, opacity: 0.7 }}>
                {getCategoryCount(category)}
              </span>
            </button>
          );
        })}
      </div>

      {/* 新闻卡片 */}
      {filteredNews.length === 0 ? (
        <div
          style={{
            padding: 30,
            textAlign: "center",
            color: "#5f6368",
            background: "#1a1d23",
            borderRadius: 10,
          }}
        >
          暂无该分类的新闻
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: 16,
          }}
        >
          {filteredNews.map((item, index) => (
            <a
              key={item.id || `${item.title}-${index}`}
              href={item.url || "https://kuaixun.eastmoney.com/"}
              target="_blank"
              rel="noopener noreferrer"
              style={{ textDecoration: "none" }}
            >
              <div
                style={{
                  background: "#1a1d23",
                  border: "1px solid #2a2e36",
                  borderRadius: 10,
                  padding: 16,
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  transition: "transform 0.15s ease, border-color 0.15s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "#4285f4";
                  e.currentTarget.style.transform = "translateY(-2px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#2a2e36";
                  e.currentTarget.style.transform = "none";
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    marginBottom: 8,
                  }}
                >
                  <span
                    style={{
                      background: "#c0c7d120",
                      color: "#c0c7d1",
                      fontSize: 11,
                      padding: "2px 6px",
                      borderRadius: 4,
                      marginRight: 8,
                    }}
                  >
                    {item.source}
                  </span>

                  <span style={{ fontSize: 12, color: "#5f6368" }}>
                    {item.time}
                  </span>

                  <span
                    style={{
                      background: getCategoryStyle(item.category).background,
                      color: getCategoryStyle(item.category).color,
                      fontSize: 11,
                      padding: "2px 6px",
                      borderRadius: 4,
                      marginLeft: 8,
                    }}
                  >
                    {item.category || "其他"}
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: 15,
                    fontWeight: 600,
                    color: "#e8eaed",
                    margin: "0 0 8px 0",
                    lineHeight: 1.4,
                  }}
                >
                  {item.title}
                </h3>

                <p
                  style={{
                    fontSize: 13,
                    color: "#9aa0a6",
                    margin: 0,
                    lineHeight: 1.5,
                    flexGrow: 1,
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {item.summary}
                </p>
              </div>
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
