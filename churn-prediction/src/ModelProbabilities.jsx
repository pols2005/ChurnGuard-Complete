import React, { FunctionComponent } from "react";
// import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid } from "recharts";
import { BarChart, Bar, Cell, XAxis, YAxis} from "recharts";
import { scaleOrdinal } from "d3-scale";
import { schemeCategory10 } from "d3-scale-chromatic";

const ModelProbabilities = ({modelProbabilities}) => {

const colors = scaleOrdinal(schemeCategory10).range();

let data = Object.keys(modelProbabilities).map((key) => {
  return {
    name: key,
    uv: Math.round(modelProbabilities[key] * 100 * 100)/100
  }
});

console.log("bar data", data);

const getPath = (x: number, y: number, width: number, height: number) => {
  return `M${x},${y + height}C${x + width / 3},${y + height} ${x + width / 2},${
    y + height / 3
  }
  ${x + width / 2}, ${y}
  C${x + width / 2},${y + height / 3} ${x + (2 * width) / 3},${y + height} ${
    x + width
  }, ${y + height}
  Z`;
};

const TriangleBar: FunctionComponent<any> = (props: any) => {
  const { fill, x, y, width, height } = props;

  return <path d={getPath(x, y, width, height)} stroke="none" fill={fill} />;
};

  return (
    <div>
    <div className="font-semibold text-center">Probability of churn predicted by various ML models (%)</div>
    <BarChart
      width={600}
      height={300}
      data={data}
      margin={{
        top: 20,
        right: 30,
        left: 20,
        bottom: 5,
      }}
    >
      {/* <CartesianGrid strokeDasharray="3 3" /> */}
      <XAxis dataKey="name" />
      <YAxis />
      <Bar
        dataKey="uv"
        fill="#8884d8"
        shape={<TriangleBar />}
        label={{ position: "top" }}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={colors[index % 20]} />
        ))}
      </Bar>
    </BarChart>
    </div>
  );
}

export default ModelProbabilities;
