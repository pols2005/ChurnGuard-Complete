import React, { useEffect, useState } from 'react';
import Heading from './Heading';
import CustomerForm from './CustomerForm';

const App = () => {

  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetails, setCustomerDetails] = useState({});
  const [churnProbability, setChurnProbability] = useState(null);
  const [modelProbabilities, setModelProbabilities] = useState(null);

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
    fetch(`http://localhost:5001/api/customer/${selectedOption.value}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setCustomerDetails(data.customer);
        }
      });
  };

  const handleShowChurnProbability = () => {
    if (!selectedCustomer) {
      alert('Please select a customer first!');
      return;
    }

    // Fetch average churn probability
    fetch(`http://localhost:5001/api/customer/${selectedCustomer.value}/churn-probability`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setChurnProbability(data.average_probability);
          console.log("avg", data);
        }
      });

    // Fetch probabilities from individual models
    fetch(`http://localhost:5001/api/customer/${selectedCustomer.value}/churn-model-probabilities`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setModelProbabilities(data.model_probabilities);
          console.log("models", data);
        }
      });
  }

  return (
    <div className="bg-gray-900 text-gray-100 min-h-screen flex flex-col items-center py-10">
      <Heading />
      <CustomerForm customers={customers} selectedCustomer={selectedCustomer} customerDetails={customerDetails} handleCustomerSelect={handleCustomerSelect}/>
      <div className="mt-6">
        <button
          onClick={handleShowChurnProbability}
          className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
        >
          Show Customer Churn Probability
        </button>
      </div>
    </div>
  );
};

export default App;
