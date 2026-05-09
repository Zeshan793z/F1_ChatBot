import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

function LapTimeChart({ driver = "VER", year = 2023, gp = "Miami" }) {
  const [lapData, setLapData] = useState([]);

  useEffect(() => {
    const fetchLapData = async () => {
      const res = await fetch(
        `http://localhost:8000/fastest-lap?year=${year}&gp=${gp}&driver=${driver}`
      );
      const data = await res.json();

      if (data.lap_data) {
        // For now we only have fastest lap, but later we can extend to all laps
        setLapData([
          {
            lap: data.lap_data.lap_number,
            time: parseFloat(data.lap_data.lap_time.replace(" seconds", "")),
            compound: data.lap_data.compound,
          },
        ]);
      }
    };

    fetchLapData();
  }, [driver, year, gp]);

  return (
    <div>
      <h2>Lap Time Chart - {driver} ({gp} {year})</h2>
      <LineChart
        width={600}
        height={300}
        data={lapData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="lap" label={{ value: "Lap Number", position: "insideBottomRight", offset: -5 }} />
        <YAxis label={{ value: "Lap Time (s)", angle: -90, position: "insideLeft" }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="time" stroke="#8884d8" activeDot={{ r: 8 }} />
      </LineChart>
    </div>
  );
}

export default LapTimeChart;
