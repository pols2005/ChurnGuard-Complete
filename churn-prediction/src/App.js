import React, { useEffect, useState } from 'react';
import Heading from './Heading';
import CustomerForm from './CustomerForm';
import GaugeMeter from './GaugeMeter';
import ModelProbabilities from './ModelProbabilities';
import Explanation from './Explanation';

const App = () => {

  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState({});
  const [churnProbability, setChurnProbability] = useState(null);
  const [modelProbabilities, setModelProbabilities] = useState(null);
  const [explanation, setExplanation] = useState('');

  useEffect(() => {
    fetch('http://localhost:5001/api/customers')
      .then((response) => response.json())
      .then((data) => {
        const formattedCustomers = data.map((customer) => ({
          value: customer.CustomerId,
          label: `${customer.Surname} (${customer.CustomerId})`,
        }));
        setCustomers(formattedCustomers);
      });
  }, []);

  const handleCustomerSelect = (selectedOption) => {
    setSelectedCustomer(selectedOption);

    setChurnProbability(null);
    setModelProbabilities(null);
    setExplanation('');

    fetch(`http://localhost:5001/api/customer/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setCustomerDetails(data.customer);
          console.log("customer details", data.customer);
        }
      });

    fetch(`http://localhost:5001/api/customer/${selectedOption.value}/churn-probability`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setChurnProbability(data.average_probability);
          console.log("Average Probability:", data.average_probability);
        }
      });

    fetch(`http://localhost:5001/api/customer/${selectedOption.value}/churn-model-probabilities`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setModelProbabilities(data.model_probabilities);
          console.log("Models Probability:", data.model_probabilities);
        }
      });

      fetch(`http://localhost:5001/api/llama/explanation/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setExplanation(data.explanation);
          console.log("Explanation:", data.explanation);
        }
      });
  };

  return (
    <div className="bg-gray-900 text-gray-100 min-h-screen flex flex-col items-center py-10">
      <Heading />
      <CustomerForm customers={customers} selectedCustomer={selectedCustomer} customerDetails={customerDetails} handleCustomerSelect={handleCustomerSelect}/>
      <div className="max-w-6xl w-full mx-auto mt-10 grid grid-cols-1 md:grid-cols-2 gap-0">
      {churnProbability && <GaugeMeter churnProbability={churnProbability}/>}
      {modelProbabilities && <ModelProbabilities modelProbabilities={modelProbabilities}/>}
      </div>
      {explanation && <Explanation explanation={explanation}/>}
    </div>
  );
};

export default App;
