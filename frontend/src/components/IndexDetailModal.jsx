import { useEffect, useState } from "react";
import MiniTrendChart from "./MiniTrendChart.jsx";

export default function IndexDetailModal({ name }) {
  const [minuteData, setMinuteData] = useState([]);
  const [yearData, setYearData] = useState([]);
  const [loadingMinute, setLoadingMinute] = useState(true);
  const [loadingYear, setLoadingYear] = useState(true);

  useEffect(() => {
    let active = true;

    setLoadingMinute(true);
    setLoadingYear(true);
    setMinuteData([]);
    setYearData([]);

    // 获取当天分时数据
    const fetchMinute = async () => {
      try {
        const response = await fetch(
          `/api/global_indices/minute?name=${encodeURIComponent(name)}`,
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const d = await response.json();

        // 只有拿到有效数据才更新，避免空响应覆盖已有曲线
        if (active && Array.isArray(d?.data) && d.data.length > 0) {
          setMinuteData(d.data);
        }
      } catch (error) {
        console.error(`${name} 分时数据获取失败:`, error);
      } finally {
        if (active) {
          setLoadingMinute(false);
        }
      }
    };

    // 首次立即获取
    fetchMinute();

    // 每 60 秒刷新一次
    const timer = setInterval(fetchMinute, 60000);

    // 近一年历史数据只需获取一次
    fetch(`/api/global_indices/history?name=${encodeURIComponent(name)}`)
      .then((r) => r.json())
      .then((d) => {
        if (active) {
          setYearData(Array.isArray(d) ? d : []);
        }
      })
      .catch(() => {
        if (active) setYearData([]);
      })
      .finally(() => {
        if (active) setLoadingYear(false);
      });

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [name]);

  const minuteSeries = minuteData.map((p) => ({
    date: p.time,
    value: p.price,
  }));

  const hasMinute = minuteSeries.length > 10;
  const hasSingle = minuteSeries.length > 0 && minuteSeries.length <= 10;

  return (
    <section
      style={{
        marginTop: 16,
        padding: 20,
        background: "#1a1d23",
        border: "1px solid #2a2e36",
        borderRadius: 12,
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <h3
        style={{
          margin: "0 0 20px 0",
          fontSize: 18,
          color: "#e8eaed",
        }}
      >
        {name} 走势分析
      </h3>

      {/* 上方：当天分时 */}
      <div style={{ marginBottom: 24 }}>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "#9aa0a6",
            marginBottom: 8,
          }}
        >
          当天分时
          {minuteData.length > 0 ? `（${minuteSeries.length} 个点）` : ""}
        </div>

        {loadingMinute ? (
          <div style={emptyStyle}>加载中...</div>
        ) : hasMinute ? (
          <MiniTrendChart
            title={`${name} 当天分时`}
            data={minuteSeries}
            color="#4285f4"
            showXAxis={true}
            height={300}
          />
        ) : hasSingle ? (
          <div style={emptyStyle}>
            当前价 {minuteSeries[0].value}（暂无完整分时数据）
          </div>
        ) : (
          <div style={emptyStyle}>该指数暂无分时数据</div>
        )}
      </div>

      {/* 下方：近一年 */}
      <div>
        <div
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "#9aa0a6",
            marginBottom: 8,
          }}
        >
          近一年走势
          {yearData.length > 0 ? `（${yearData.length} 个交易日）` : ""}
        </div>

        {loadingYear ? (
          <div style={emptyStyle}>加载中...</div>
        ) : yearData.length > 0 ? (
          <MiniTrendChart
            title={`${name} 近一年走势`}
            data={yearData}
            color="#0f9d58"
            height={280}
          />
        ) : (
          <div style={emptyStyle}>暂无历史数据</div>
        )}
      </div>
    </section>
  );
}

const emptyStyle = {
  height: 220,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#9aa0a6",
  textAlign: "center",
  fontSize: 13,
};
