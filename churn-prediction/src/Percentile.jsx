import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from "recharts";

const Percentile = ({ featurePercentile }) => {
  // Prepare data for the chart
  let data = Object.keys(featurePercentile).map((key) => {
    return {
      name: key,
      percentile: Math.round(featurePercentile[key] * 100) / 100
    };
  });

  console.log("Feature Percentile Data as an Array:", data);

  return (
    <div className="text-center">
      <h3 className="font-semibold pb-3">
        Customer Feature Percentiles
      </h3>
    <BarChart width={730} height={250} data={data}>
      <XAxis dataKey="name" orientation="top"/>
      <YAxis />
      <Tooltip
      contentStyle={{ backgroundColor: "white", color: "black" }} // Tooltip box style
      itemStyle={{ color: "black" }} // Tooltip text color
      />
      <Legend />
      <Bar dataKey="percentile" fill="#ffff00" />
    </BarChart>


    </div>
  );
};

export default Percentile;
