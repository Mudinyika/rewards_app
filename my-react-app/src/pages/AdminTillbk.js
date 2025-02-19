import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from "recharts";
import "../styles/Analytics.css";

const Analytics = () => {
  const [reportType, setReportType] = useState("daily");
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [tillNumber, setTillNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("reports");
  const [activeFilter, setActiveFilter] = useState("till_operators");
  const [metrics, setMetrics] = useState({});
  const [chartData, setChartData] = useState([]);
  const [topPerformer, setTopPerformer] = useState("");

  // Fetch real-time metrics every 10 seconds
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/metrics");
      const data = await response.json();
      setMetrics(data);
      updateChartData(activeFilter, data);
    } catch (error) {
      console.error("Error fetching metrics:", error);
    }
  };

  const updateChartData = (filter, data) => {
    let newData = [];
    let topEntity = "";

    if (filter === "till_operators") {
      newData = [
        { name: "Most Points Added", value: data.total_added_points || 0 },
        { name: "Most Points Removed", value: data.total_removed_points || 0 }
      ];
      topEntity = `Top Till Operator: ${data.top_till_operator_name || "N/A"}`;
    } else if (filter === "admins") {
      newData = [
        { name: "Most Points Added", value: data.top_admin_add || 0 },
        { name: "Most Points Removed", value: data.top_admin_remove || 0 }
      ];
      topEntity = `Top Admin: ${data.top_admin_name || "N/A"}`;
    } else if (filter === "till_numbers") {
      newData = [
        { name: "Most Transactions", value: data.top_till_number_transactions || 0 }
      ];
      topEntity = `Top Till Number: ${data.top_till_number || "N/A"}`;
    }

    setChartData(newData);
    setTopPerformer(topEntity);
    setActiveFilter(filter);
  };

  const handleGenerateReport = async () => {
    setLoading(true);

    let queryParams = new URLSearchParams({ report_type: reportType });

    if (startDate && endDate) {
      queryParams.append("start_date", startDate.toISOString().split("T")[0]);
      queryParams.append("end_date", endDate.toISOString().split("T")[0]);
    }

    if (tillNumber) {
      queryParams.append("till_number", tillNumber);
    }

    try {
      const response = await fetch(
        `http://localhost:5000/api/generate-report?${queryParams.toString()}`,
        { method: "GET" }
      );

      if (!response.ok) throw new Error("Failed to fetch report");

      // Open the report in a new tab
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch (error) {
      console.error("Error generating report:", error);
      alert("Failed to generate report");
    }

    setLoading(false);
  };

  return (
    <div className="analytics-container">
      <h1 className="analytics-title">Analytics & Reports</h1>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button className={activeTab === "reports" ? "active" : ""} onClick={() => setActiveTab("reports")}>
          Reports
        </button>
        <button className={activeTab === "charts" ? "active" : ""} onClick={() => setActiveTab("charts")}>
          Charts
        </button>
      </div>

      {/* Reports Section */}
      {activeTab === "reports" && (
        <div className="reports-section">
          <div className="filters-container">
            <label>Report Type:</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>

            <label>Start Date:</label>
            <DatePicker selected={startDate} onChange={(date) => setStartDate(date)} />
            <label>End Date:</label>
            <DatePicker selected={endDate} onChange={(date) => setEndDate(date)} />

            <label>Till Number:</label>
            <input
              type="text"
              placeholder="Enter till number (optional)"
              value={tillNumber}
              onChange={(e) => setTillNumber(e.target.value)}
            />

            <button onClick={handleGenerateReport} disabled={loading}>
              {loading ? "Generating..." : "Generate Report"}
            </button>
          </div>
        </div>
      )}

      {/* Charts Section */}
      {activeTab === "charts" && (
        <div className="charts-fullscreen">
          <div className="chart-filters">
            <button onClick={() => updateChartData("till_operators", metrics)}>Till Operators</button>
            <button onClick={() => updateChartData("admins", metrics)}>Admins</button>
            <button onClick={() => updateChartData("till_numbers", metrics)}>Till Numbers</button>
          </div>

          <div className="chart-container">
            <h2>{activeFilter.replace("_", " ").toUpperCase()}</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#007bff" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h2>Points Over Time</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#28a745" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="top-performer">{topPerformer}</div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
