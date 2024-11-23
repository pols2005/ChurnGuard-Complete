import React from 'react';

const Explanation = ({explanation}) => {

return (
  <div className="p-8 rounded-lg max-w-6xl w-full mx-auto mt-3"
  style={{
    background: `linear-gradient(135deg, #01497c, #014f86, #2a6f97, #2c7da0, #468faf)`,
  }}>
    <div className="text-2xl font-semibold mb-3">Explanation of Prediction:</div>
    <div>{explanation}</div>
  </div>
)
};

export default Explanation;