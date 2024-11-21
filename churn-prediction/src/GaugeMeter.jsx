import React from 'react';
import ReactSpeedometer from "react-d3-speedometer";

const GaugeMeter = ({churnProbability}) => {

let churnValue = Math.round(churnProbability * 100 * 100)/ 100;

return(
<div>
  <div className="text-center font-semibold p-3">Churn Probability</div>
  <div className="text-center font-semibold">The customer has a {churnValue}% probability of churning</div>
  <div className="flex justify-center mt-9">
  <ReactSpeedometer
  value={churnValue}
  minValue={0}
  maxValue={100}
  endColor={"#FF0000"}
  startColor={"#33CC33"}
  needleColor="steelblue"
  needleTransitionDuration={4000}
  needleTransition="easeElastic"/>
</div>


</div>
)
};

export default GaugeMeter;